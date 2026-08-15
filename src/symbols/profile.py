"""The destination half of symbol matching: :class:`DestinationProfile`.

A symbol says which ``environments``/``regions``/``climate`` it belongs to
(``src.symbols.model.SymbolFacets``); a profile says the same about a
destination, in the same vocabulary (``src.symbols.vocab``), so a future
relevance score can compare the two by plain set overlap. The dataclass
itself lives in ``src.models.context`` (so ``DestinationKnowledge`` can carry
one without that module depending on this package); this module is where a
profile actually gets *built*.

Two ways to get one, and ``profile_for()`` picks between them:

``profile_for()`` -> authored, if the pack has one; else derived
    An authored profile is a destination pack's own ``"profile"`` block —
    trustworthy enough that a future relevance score may use it to bar a
    symbol outright (a desert destination really has no boats).
    A derived profile is a keyword scan over the destination's own knowledge
    text, exactly the trick ``src.activities.packing`` already uses for "does
    this trip need a rain coat" — a safety net for pack-less and LLM-only
    destinations. Recorded as ``source="derived"`` so a later relevance score
    knows never to treat it as strong enough to veto: a scan that simply
    failed to notice the river must cost a boat some points, never all of
    them.
"""

from __future__ import annotations

from src.models.context import KNOWLEDGE_FIELDS, DestinationKnowledge, DestinationProfile

#: keyword -> environment tags it implies, scanned across every knowledge
#: category's joined text. A destination can match several hint groups (a
#: mountain village matches both), so the result is a union, not a pick-one.
_ENVIRONMENT_HINTS: tuple[tuple[tuple[str, ...], tuple[str, ...]], ...] = (
    (("beach", "coast", "island", "bay", "gulf", "harbour", "harbor", "shore"), ("coast", "water")),
    (("river", "lake", "boat", "dolphin", "sailing", "fishing"), ("water",)),
    (("mountain", "peak", "alps", "highland", "hillside"), ("mountain",)),
    (("forest", "woodland", "pine", "chestnut"), ("forest",)),
    (("desert", "dune", "oasis", "wadi"), ("desert",)),
    (("farm", "orchard", "vineyard", "grazing"), ("farm",)),
    (("snow", "ski", "chairlift", "winter sports"), ("snow", "mountain")),
    (("village", "old town", "square", "cobbled", "cobblestone"), ("village",)),
    (("city", "downtown", "urban"), ("city",)),
)

#: keyword -> climate tags it implies, same scanning approach.
_CLIMATE_HINTS: tuple[tuple[tuple[str, ...], tuple[str, ...]], ...] = (
    (("hot", "sunny", "heat", "warm"), ("hot",)),
    (("cold", "snowy", "frost", "chilly"), ("cold",)),
    (("rain", "wet", "humid", "misty", "showers"), ("wet",)),
    (("dry", "arid"), ("dry",)),
    (("mild", "temperate"), ("temperate",)),
)


def derive_profile(knowledge: DestinationKnowledge) -> DestinationProfile:
    """Guess a profile from a destination's own knowledge text.

    A miss just means one fewer tag, never a wrong one — the property that
    makes a derived profile safe to use as a scoring bonus but never as a
    veto (see ``DestinationProfile.source``).
    """
    haystack = " ".join(
        phrase for category in KNOWLEDGE_FIELDS for phrase in knowledge.get(category)
    ).lower()
    return DestinationProfile(
        environments=_match(haystack, _ENVIRONMENT_HINTS),
        climate=_match(haystack, _CLIMATE_HINTS),
        source="derived",
    )


def _match(haystack: str, hints: tuple[tuple[tuple[str, ...], tuple[str, ...]], ...]) -> tuple[str, ...]:
    found: list[str] = []
    for keywords, tags in hints:
        if any(keyword in haystack for keyword in keywords):
            for tag in tags:
                if tag not in found:
                    found.append(tag)
    return tuple(found)


def profile_for(knowledge: DestinationKnowledge) -> DestinationProfile:
    """The profile to actually match symbols against.

    Prefers an authored profile (the pack's own ``"profile"`` block); falls
    back to a derived guess so every destination — including a bare
    knowledge-only one with no pack at all — has something to match against.
    """
    if knowledge.profile is not None:
        return knowledge.profile
    return derive_profile(knowledge)
