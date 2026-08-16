"""Agent 1: curated packs, the model provider, and the offline fallback."""

from __future__ import annotations

import json

import pytest

from src.agents.destination_agent import (
    DestinationKnowledgeAgent,
    FileKnowledgeProvider,
    HeuristicKnowledgeProvider,
    LLMKnowledgeProvider,
    build_knowledge_agent,
)
from src.models.context import KNOWLEDGE_FIELDS, DestinationKnowledge

from tests.conftest import DATA_DIR


def _api_response(payload: dict) -> str:
    """Shape a Messages API response body around a knowledge payload."""
    return json.dumps({"content": [{"type": "text", "text": json.dumps(payload)}]})


# -- file packs ---------------------------------------------------------


def test_file_provider_loads_a_curated_pack():
    knowledge = FileKnowledgeProvider(DATA_DIR).fetch("Kfar Hanokdim")
    assert knowledge is not None
    assert knowledge.source == "file"
    assert "camels" in knowledge.wildlife
    assert knowledge.coverage() == len(KNOWLEDGE_FIELDS)


@pytest.mark.parametrize(
    "spelling", ["Kfar Hanokdim", "kfar hanokdim", "Kfar HaNokdim", "Nokdim Village"]
)
def test_file_provider_matches_aliases_and_casing(spelling):
    assert FileKnowledgeProvider(DATA_DIR).fetch(spelling) is not None


def test_file_provider_returns_none_for_an_unknown_place():
    assert FileKnowledgeProvider(DATA_DIR).fetch("Somewhere Unlisted") is None


def test_file_provider_lists_what_it_has():
    known = FileKnowledgeProvider(DATA_DIR).known_destinations()
    assert "Kfar Hanokdim" in known and "Prague" in known


def test_file_provider_skips_a_corrupt_pack(tmp_path):
    (tmp_path / "broken.json").write_text("{not json", encoding="utf-8")
    (tmp_path / "good.json").write_text(
        json.dumps({"destination": "Elsewhere", "landmarks": ["a bridge"]}), encoding="utf-8"
    )
    provider = FileKnowledgeProvider(tmp_path)
    assert provider.fetch("Elsewhere").landmarks == ("a bridge",)


# -- translation fragments ------------------------------------------------


def _write_pack(tmp_path, stem="place", **overrides):
    data = {
        "destination": "Place",
        "landmarks": ["a bridge", "a tower"],
        "local_food": ["bread"],
        **overrides,
    }
    (tmp_path / f"{stem}.json").write_text(json.dumps(data), encoding="utf-8")
    return data


def test_a_fragment_translates_matching_phrases_and_falls_back_for_the_rest(tmp_path):
    """A fragment translating only some of a category is a partial pack, not
    an error — the untranslated phrase stays English."""
    _write_pack(tmp_path)
    (tmp_path / "place.he.json").write_text(
        json.dumps({"display_name": "מקום", "translations": {"a bridge": "גשר"}}),
        encoding="utf-8",
    )
    knowledge = FileKnowledgeProvider(tmp_path).fetch("Place", language="he")
    assert knowledge.landmarks == ("גשר", "a tower")
    assert knowledge.display_name == "מקום"
    assert knowledge.english_terms == {"גשר": "a bridge"}


def test_a_corrupt_fragment_falls_back_to_the_base_pack(tmp_path):
    _write_pack(tmp_path)
    (tmp_path / "place.he.json").write_text("{not json", encoding="utf-8")
    knowledge = FileKnowledgeProvider(tmp_path).fetch("Place", language="he")
    assert knowledge.landmarks == ("a bridge", "a tower")
    assert knowledge.illustration_terms == ()


def test_a_fragment_never_registers_as_its_own_destination(tmp_path):
    _write_pack(tmp_path)
    (tmp_path / "place.he.json").write_text(
        json.dumps({"translations": {}}), encoding="utf-8"
    )
    provider = FileKnowledgeProvider(tmp_path)
    assert provider.known_destinations() == ("Place",)
    assert provider.languages_for("Place") == ("en", "he")


def test_a_fragment_with_no_translations_key_is_treated_as_empty(tmp_path):
    """``{}`` is a valid, if pointless, fragment — not a malformed one."""
    _write_pack(tmp_path)
    (tmp_path / "place.he.json").write_text("{}", encoding="utf-8")
    knowledge = FileKnowledgeProvider(tmp_path).fetch("Place", language="he")
    assert knowledge.landmarks == ("a bridge", "a tower")


# -- heuristic fallback --------------------------------------------------


def test_file_provider_country_survives_the_hebrew_translation_merge():
    """A base pack's ``country`` is structure, not translatable prose —
    ``_merge_translation``'s ``dict(base)`` should carry it through
    untouched into a ``he`` fetch, the same way ``profile`` already does,
    with no dedicated handling needed in that function."""
    en_knowledge = FileKnowledgeProvider(DATA_DIR).fetch("Pelion", language="en")
    he_knowledge = FileKnowledgeProvider(DATA_DIR).fetch("Pelion", language="he")
    assert en_knowledge.country == "GR"
    assert he_knowledge.country == "GR"


def test_heuristic_provider_always_answers():
    knowledge = HeuristicKnowledgeProvider().fetch("Somewhere Unlisted")
    assert knowledge.coverage() == len(KNOWLEDGE_FIELDS)
    assert knowledge.source == "heuristic"
    assert knowledge.notes, "generic material must say that it is generic"


def test_heuristic_provider_never_guesses_a_country():
    """The heuristic provider knows nothing about any specific place, so it
    must never populate ``country`` — a guessed capital in a child's
    workbook is worse than the quiz question not appearing at all."""
    knowledge = HeuristicKnowledgeProvider().fetch("Somewhere Unlisted")
    assert knowledge.country == ""


def test_heuristic_provider_reads_the_setting_from_the_name():
    park = HeuristicKnowledgeProvider().fetch("Redwood National Park")
    beach = HeuristicKnowledgeProvider().fetch("Coral Bay Beach")
    assert "deer" in park.wildlife
    assert "seagulls" in beach.wildlife
    assert park.landmarks != beach.landmarks


def test_heuristic_provider_follows_declared_interests():
    knowledge = HeuristicKnowledgeProvider().fetch("Tbilisi", interests=("trains",))
    assert "the train station" in knowledge.landmarks


# -- LLM provider --------------------------------------------------------


def test_llm_provider_parses_a_model_answer():
    payload = {name: [f"{name} one", f"{name} two"] for name in KNOWLEDGE_FIELDS}
    captured: dict[str, object] = {}

    def transport(url, headers, body):
        captured["url"] = url
        captured["headers"] = headers
        captured["body"] = json.loads(body)
        return _api_response(payload)

    provider = LLMKnowledgeProvider(api_key="test-key", transport=transport)
    knowledge = provider.fetch("Prague", interests=("castles",))

    assert knowledge is not None
    assert knowledge.source == "llm"
    assert knowledge.landmarks == ("landmarks one", "landmarks two")
    assert captured["headers"]["x-api-key"] == "test-key"
    assert "Prague" in captured["body"]["messages"][0]["content"]
    assert "castles" in captured["body"]["messages"][0]["content"]


def test_llm_provider_handles_a_fenced_answer():
    payload = {"wildlife": ["swans"]}
    fenced = f"```json\n{json.dumps(payload)}\n```"
    provider = LLMKnowledgeProvider(
        api_key="k",
        transport=lambda *args: json.dumps({"content": [{"type": "text", "text": fenced}]}),
    )
    assert provider.fetch("Prague").wildlife == ("swans",)


def test_llm_provider_without_a_key_declines():
    provider = LLMKnowledgeProvider(api_key="")
    assert provider.fetch("Prague") is None


@pytest.mark.parametrize(
    "response",
    ["not json at all", json.dumps({"content": [{"type": "text", "text": "sorry, no"}]})],
)
def test_llm_provider_declines_on_a_bad_answer(response):
    provider = LLMKnowledgeProvider(api_key="k", transport=lambda *args: response)
    assert provider.fetch("Prague") is None


def test_llm_provider_declines_when_the_call_fails():
    def transport(*args):
        raise TimeoutError("network down")

    provider = LLMKnowledgeProvider(api_key="k", transport=transport)
    assert provider.fetch("Prague") is None


# -- the agent chain -----------------------------------------------------


def test_agent_falls_through_to_the_next_provider():
    empty = LLMKnowledgeProvider(api_key="")
    agent = DestinationKnowledgeAgent(
        (empty, FileKnowledgeProvider(DATA_DIR)), completer=HeuristicKnowledgeProvider()
    )
    assert agent.fetch("Prague").source == "file"


def test_agent_falls_back_to_generic_material():
    agent = build_knowledge_agent("file", data_dir=DATA_DIR)
    knowledge = agent.fetch("Somewhere Unlisted")
    assert knowledge.source == "heuristic"
    assert not knowledge.is_empty


def test_agent_tops_up_a_thin_pack(tmp_path):
    (tmp_path / "thin.json").write_text(
        json.dumps({"destination": "Thin Town", "landmarks": ["the clock tower"]}),
        encoding="utf-8",
    )
    agent = build_knowledge_agent("file", data_dir=tmp_path)
    knowledge = agent.fetch("Thin Town")

    assert knowledge.source == "file"
    assert knowledge.landmarks[0] == "the clock tower", "curated entries win"
    assert knowledge.wildlife, "empty categories are completed"
    assert any("completed" in note for note in knowledge.notes)


def test_agent_topping_up_a_thin_pack_does_not_clobber_its_country(tmp_path):
    """``filled_with()`` only patches empty ``KNOWLEDGE_FIELDS`` categories
    from the heuristic completer — ``country`` isn't one of those fields, so
    a thin-but-country-bearing pack must keep its own country rather than
    losing it (the heuristic provider never sets one at all, so a naive
    field-by-field merge could otherwise blank it out)."""
    (tmp_path / "thin.json").write_text(
        json.dumps(
            {"destination": "Thin Town", "country": "GR", "landmarks": ["the clock tower"]}
        ),
        encoding="utf-8",
    )
    agent = build_knowledge_agent("file", data_dir=tmp_path)
    knowledge = agent.fetch("Thin Town")

    assert knowledge.country == "GR"
    assert knowledge.wildlife, "empty categories are still completed as before"


def test_llm_provider_drops_a_country_code_that_is_not_curated():
    """The model may only *select* a country from the checked-in table,
    never supply its own facts — a code it names that data/countries.json
    doesn't have is dropped rather than trusted, so a hallucinated country
    can never reach the quiz's capital/flag questions."""
    payload = {name: [] for name in KNOWLEDGE_FIELDS}
    payload["wildlife"] = ["something real"]
    payload["country"] = "ZZ"  # not a real entry in data/countries.json
    provider = LLMKnowledgeProvider(api_key="k", transport=lambda *a: _api_response(payload))
    knowledge = provider.fetch("Somewhere Fictional")
    assert knowledge is not None
    assert knowledge.country == ""


def test_llm_provider_keeps_a_country_code_that_is_curated():
    payload = {name: [] for name in KNOWLEDGE_FIELDS}
    payload["wildlife"] = ["something real"]
    payload["country"] = "gr"  # lower-case, as from_dict() normalizes it
    provider = LLMKnowledgeProvider(api_key="k", transport=lambda *a: _api_response(payload))
    knowledge = provider.fetch("Somewhere In Greece")
    assert knowledge.country == "GR"


def test_llm_chain_prefers_the_model_then_the_pack():
    payload = {"wildlife": ["dragons of the model"]}
    provider = LLMKnowledgeProvider(api_key="k", transport=lambda *a: _api_response(payload))
    agent = build_knowledge_agent("llm", data_dir=DATA_DIR, llm_provider=provider)
    assert agent.fetch("Prague").wildlife[0] == "dragons of the model"


def test_auto_chain_prefers_the_pack_over_the_model():
    provider = LLMKnowledgeProvider(
        api_key="k", transport=lambda *a: _api_response({"wildlife": ["never used"]})
    )
    agent = build_knowledge_agent("auto", data_dir=DATA_DIR, llm_provider=provider)
    assert agent.fetch("Prague").source == "file"


def test_unknown_provider_name_is_rejected():
    with pytest.raises(ValueError, match="unknown knowledge provider"):
        build_knowledge_agent("telepathy")


def test_knowledge_from_dict_ignores_unknown_keys():
    knowledge = DestinationKnowledge.from_dict(
        {"landmarks": ["a tower"], "population": 12345}, source="test"
    )
    assert knowledge.landmarks == ("a tower",)
    assert knowledge.source == "test"
