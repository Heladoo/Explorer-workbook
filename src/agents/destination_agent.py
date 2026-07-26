"""Agent 1 — Destination Knowledge.

Turns a destination name into structured facts. Three interchangeable providers
ship with the MVP:

``FileKnowledgeProvider``
    Curated JSON packs under ``data/destinations/``. Default, offline, exact.
``LLMKnowledgeProvider``
    Asks a Claude model for the same JSON shape. Opt-in via ``--provider llm``.
``HeuristicKnowledgeProvider``
    Never fails. Produces deliberately generic material so an unknown
    destination still yields a usable workbook, and says so in ``notes``.

Adding RAG or web search later means writing another class with the same
``fetch`` method and putting it in the chain — nothing downstream changes.
"""

from __future__ import annotations

import json
import logging
import os
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Callable, Iterable, Protocol, Sequence

from src.models.context import KNOWLEDGE_FIELDS, DestinationKnowledge, slugify

logger = logging.getLogger(__name__)

#: Where the curated packs live, relative to the repository root.
DEFAULT_DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "destinations"

DEFAULT_MODEL = "claude-sonnet-5"
ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"


class KnowledgeProvider(Protocol):
    """Anything that can answer "what is there to know about this place?"."""

    name: str

    def fetch(self, destination: str, *, interests: Sequence[str] = ()) -> DestinationKnowledge | None:
        """Return knowledge, or ``None`` when this provider has nothing to say."""


class FileKnowledgeProvider:
    """Loads curated destination packs from a directory of JSON files."""

    name = "file"

    def __init__(self, data_dir: Path | str | None = None) -> None:
        self.data_dir = Path(data_dir) if data_dir else DEFAULT_DATA_DIR

    def fetch(
        self, destination: str, *, interests: Sequence[str] = ()
    ) -> DestinationKnowledge | None:
        pack = self._find_pack(destination)
        if pack is None:
            return None
        return DestinationKnowledge.from_dict(pack, source=self.name)

    def _find_pack(self, destination: str) -> dict[str, Any] | None:
        if not self.data_dir.is_dir():
            return None
        wanted = slugify(destination)
        for path in sorted(self.data_dir.glob("*.json")):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                logger.warning("skipping unreadable destination pack %s: %s", path.name, exc)
                continue
            names = [data.get("destination", path.stem), *data.get("aliases", [])]
            if any(slugify(str(name)) == wanted for name in names if name):
                return data
        return None

    def known_destinations(self) -> tuple[str, ...]:
        """Destination names that have a curated pack, for CLI help and tests."""
        if not self.data_dir.is_dir():
            return ()
        names = []
        for path in sorted(self.data_dir.glob("*.json")):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            names.append(str(data.get("destination", path.stem)))
        return tuple(names)


class HeuristicKnowledgeProvider:
    """Builds generic-but-usable knowledge for any destination, offline.

    It never invents a specific claim about a place it does not know. Entries
    are phrased generically ("the main square", "birds overhead") and the
    result is tagged so the workbook can say where its material came from.
    """

    name = "heuristic"

    #: Keyword in the destination name -> extra material typical of that setting.
    _SETTING_HINTS: tuple[tuple[tuple[str, ...], dict[str, tuple[str, ...]]], ...] = (
        (
            ("national park", "reserve", "forest", "nature", "wildlife"),
            {
                "landmarks": ("the visitor centre", "a marked scenic trail", "a lookout point"),
                "wildlife": ("deer", "birds of prey", "small forest mammals"),
                "plants": ("tall trees", "wildflowers", "ferns"),
                "activities": ("walking a marked trail", "spotting animals", "a ranger talk"),
                "weather": ("changeable outdoor weather", "cooler in the shade"),
            },
        ),
        (
            ("desert", "dunes", "wadi", "oasis", "negev", "sahara"),
            {
                "landmarks": ("a wide desert viewpoint", "a dry riverbed", "a camp under the stars"),
                "wildlife": ("camels", "desert lizards", "ibex"),
                "plants": ("date palms", "acacia trees", "hardy desert shrubs"),
                "activities": ("a camel ride", "stargazing", "walking in the dunes"),
                "weather": ("hot and dry by day", "cold and clear at night"),
            },
        ),
        (
            ("mountain", "alps", "peak", "valley", "highland"),
            {
                "landmarks": ("a mountain viewpoint", "a cable car station", "a mountain stream"),
                "wildlife": ("mountain goats", "marmots", "eagles"),
                "plants": ("pine trees", "alpine flowers"),
                "activities": ("a mountain walk", "riding the cable car"),
                "weather": ("cool mountain air", "weather that changes quickly"),
            },
        ),
        (
            ("beach", "island", "coast", "bay", "sea", "riviera"),
            {
                "landmarks": ("the harbour", "a lighthouse", "a long sandy beach"),
                "wildlife": ("seagulls", "crabs", "small fish"),
                "plants": ("palm trees", "beach grass"),
                "activities": ("swimming", "building sandcastles", "a boat trip"),
                "weather": ("sunny with a sea breeze",),
            },
        ),
        (
            ("castle", "fortress", "chateau", "palace"),
            {
                "landmarks": ("the castle gate", "a stone tower", "the courtyard"),
                "activities": ("exploring the towers", "walking the walls"),
                "history": ("people lived and worked inside these walls long ago",),
            },
        ),
    )

    #: Declared interests -> material to weave in, so the book still fits the child.
    _INTEREST_HINTS: dict[str, dict[str, tuple[str, ...]]] = {
        "animals": {
            "wildlife": ("birds", "stray cats", "insects"),
            "activities": ("looking for animals",),
        },
        "castles": {
            "landmarks": ("an old tower", "a city gate"),
            "activities": ("exploring old buildings",),
        },
        "trains": {
            "landmarks": ("the train station",),
            "activities": ("a train ride", "watching the trains"),
        },
        "science": {
            "landmarks": ("a science museum",),
            "activities": ("a hands-on experiment",),
            "interesting_facts": ("Every place has something you can measure or count.",),
        },
        "dinosaurs": {
            "landmarks": ("a natural history museum",),
            "activities": ("hunting for fossils in the museum",),
        },
        "food": {"activities": ("tasting something new",)},
        "art": {"landmarks": ("an art museum",), "activities": ("drawing what you see",)},
    }

    #: The floor: material that is true of visiting anywhere at all.
    _BASELINE: dict[str, tuple[str, ...]] = {
        "landmarks": ("the main square", "a viewpoint over the town", "a local market"),
        "wildlife": ("birds overhead", "insects in the grass"),
        "plants": ("street trees", "flowers in a garden"),
        "activities": ("a walking tour", "drawing what you see", "buying a postcard"),
        "history": ("people have lived here for a very long time",),
        "local_food": ("a local bread", "a sweet local treat", "fresh fruit"),
        "weather": ("check the forecast before you go",),
        "interesting_facts": (
            "Every place has its own sounds — stop and listen for a minute.",
            "Maps look different once you have walked the streets yourself.",
        ),
    }

    def fetch(
        self, destination: str, *, interests: Sequence[str] = ()
    ) -> DestinationKnowledge:
        collected: dict[str, list[str]] = {name: [] for name in KNOWLEDGE_FIELDS}
        haystack = destination.lower()

        for keywords, material in self._SETTING_HINTS:
            if any(keyword in haystack for keyword in keywords):
                _merge(collected, material)

        for interest in interests:
            material = self._INTEREST_HINTS.get(interest.strip().lower())
            if material:
                _merge(collected, material)

        _merge(collected, self._BASELINE)
        collected["interesting_facts"].insert(
            0, f"{destination} is waiting for you — write down the first thing you notice."
        )

        return DestinationKnowledge(
            **{name: tuple(values) for name, values in collected.items()},
            source=self.name,
            notes=(
                "Generic material: no curated data pack or model answer was available "
                f"for {destination}, so these entries describe travel in general.",
            ),
        )


class LLMKnowledgeProvider:
    """Asks a Claude model for the destination knowledge, in the same JSON shape.

    ``transport`` is injected so tests never touch the network. Any failure —
    missing key, HTTP error, unparseable answer — is logged and turned into
    ``None`` so the agent can fall through to the next provider.
    """

    name = "llm"

    PROMPT = (
        "You are a travel researcher preparing material for a children's activity "
        "book about {destination}.\n"
        "Return ONLY a JSON object, no prose and no code fences, with exactly these "
        "keys: {fields}.\n"
        "Each value is an array of 4-8 short strings (2-6 words each), suitable for a "
        "child aged 4-10 and safe to illustrate.\n"
        "Only include things that are genuinely true of {destination}. If you are not "
        "sure about a category, return an empty array for it rather than guessing.\n"
        "{interest_note}"
    )

    def __init__(
        self,
        *,
        model: str = DEFAULT_MODEL,
        api_key: str | None = None,
        transport: Callable[[str, dict[str, str], bytes], str] | None = None,
        max_tokens: int = 4000,
        timeout: float = 60.0,
    ) -> None:
        # ``max_tokens`` caps thinking *and* response text together, and current
        # models think by default — a budget sized for the JSON alone would let
        # thinking crowd out the answer and truncate it mid-object.
        self.model = model
        self.api_key = api_key if api_key is not None else os.environ.get("ANTHROPIC_API_KEY", "")
        self.transport = transport or _urllib_transport
        self.max_tokens = max_tokens
        self.timeout = timeout

    def fetch(
        self, destination: str, *, interests: Sequence[str] = ()
    ) -> DestinationKnowledge | None:
        if not self.api_key:
            logger.warning(
                "LLM knowledge provider skipped: ANTHROPIC_API_KEY is not set. "
                "Falling back to the next provider."
            )
            return None

        interest_note = (
            f"The child is especially interested in {', '.join(interests)}; favour "
            "entries connected to that where they genuinely exist.\n"
            if interests
            else ""
        )
        prompt = self.PROMPT.format(
            destination=destination,
            fields=", ".join(KNOWLEDGE_FIELDS),
            interest_note=interest_note,
        )
        body = json.dumps(
            {
                "model": self.model,
                "max_tokens": self.max_tokens,
                "messages": [{"role": "user", "content": prompt}],
            }
        ).encode("utf-8")
        headers = {
            "content-type": "application/json",
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
        }

        try:
            raw = self.transport(ANTHROPIC_URL, headers, body)
        except Exception as exc:  # network, auth, timeout — all recoverable here
            logger.warning("LLM knowledge lookup failed (%s); falling back.", exc)
            return None

        payload = self._extract_json(raw)
        if payload is None:
            logger.warning("LLM knowledge answer was not valid JSON; falling back.")
            return None

        knowledge = DestinationKnowledge.from_dict(payload, source=self.name)
        if knowledge.is_empty:
            logger.warning("LLM knowledge answer was empty; falling back.")
            return None
        return knowledge

    @staticmethod
    def _extract_json(raw: str) -> dict[str, Any] | None:
        """Pull the knowledge object out of an API response body."""
        try:
            response = json.loads(raw)
        except json.JSONDecodeError:
            return None

        text = raw
        if isinstance(response, dict) and "content" in response:
            blocks = response.get("content") or []
            text = "".join(
                block.get("text", "")
                for block in blocks
                if isinstance(block, dict) and block.get("type") == "text"
            )
        elif isinstance(response, dict):
            # Already the bare knowledge object.
            return response

        text = text.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[-1].rsplit("```", 1)[0]
        start, end = text.find("{"), text.rfind("}")
        if start == -1 or end <= start:
            return None
        try:
            parsed = json.loads(text[start : end + 1])
        except json.JSONDecodeError:
            return None
        return parsed if isinstance(parsed, dict) else None


class DestinationKnowledgeAgent:
    """Agent 1: tries each provider in order and tops up thin results.

    The first provider that returns anything wins. Empty categories are then
    filled from the always-available heuristic provider, so every downstream
    activity can rely on the knowledge it declares as required.
    """

    def __init__(
        self,
        providers: Iterable[KnowledgeProvider],
        *,
        completer: KnowledgeProvider | None = None,
    ) -> None:
        self.providers = tuple(providers)
        self.completer = completer

    def fetch(
        self, destination: str, *, interests: Sequence[str] = ()
    ) -> DestinationKnowledge:
        for provider in self.providers:
            knowledge = provider.fetch(destination, interests=interests)
            if knowledge is not None and not knowledge.is_empty:
                logger.info("destination knowledge for %r from %s", destination, provider.name)
                return self._complete(knowledge, destination, interests)
        logger.info("no provider had knowledge for %r; using generic material", destination)
        if self.completer is None:
            raise RuntimeError(
                f"no knowledge provider produced anything for {destination!r} and no "
                "fallback provider is configured"
            )
        fallback = self.completer.fetch(destination, interests=interests)
        if fallback is None or fallback.is_empty:
            raise RuntimeError(f"fallback knowledge provider returned nothing for {destination!r}")
        return fallback

    def _complete(
        self,
        knowledge: DestinationKnowledge,
        destination: str,
        interests: Sequence[str],
    ) -> DestinationKnowledge:
        if self.completer is None or knowledge.coverage() == len(KNOWLEDGE_FIELDS):
            return knowledge
        fallback = self.completer.fetch(destination, interests=interests)
        return knowledge.filled_with(fallback) if fallback else knowledge


def build_knowledge_agent(
    provider: str = "auto",
    *,
    data_dir: Path | str | None = None,
    llm_provider: LLMKnowledgeProvider | None = None,
) -> DestinationKnowledgeAgent:
    """Assemble the provider chain named by ``provider``.

    ``file``
        curated packs only. ``llm`` model first, packs as backup.
        ``auto`` packs first, model only when there is no pack.
        ``heuristic`` generic material only.
    """
    file_provider = FileKnowledgeProvider(data_dir)
    heuristic = HeuristicKnowledgeProvider()
    chains: dict[str, tuple[KnowledgeProvider, ...]] = {
        "file": (file_provider,),
        "heuristic": (),
        "llm": (llm_provider or LLMKnowledgeProvider(), file_provider),
        "auto": (file_provider, llm_provider or LLMKnowledgeProvider()),
    }
    try:
        chain = chains[provider]
    except KeyError as exc:
        raise ValueError(
            f"unknown knowledge provider {provider!r}; choose from {', '.join(sorted(chains))}"
        ) from exc
    return DestinationKnowledgeAgent(chain, completer=heuristic)


def _urllib_transport(url: str, headers: dict[str, str], body: bytes) -> str:
    request = urllib.request.Request(url, data=body, headers=headers, method="POST")
    with urllib.request.urlopen(request, timeout=60) as response:  # noqa: S310 - fixed API URL
        return response.read().decode("utf-8")


def _merge(target: dict[str, list[str]], material: dict[str, tuple[str, ...]]) -> None:
    """Append material into the collected buckets, skipping duplicates."""
    for name, values in material.items():
        bucket = target.setdefault(name, [])
        for value in values:
            if value not in bucket:
                bucket.append(value)
