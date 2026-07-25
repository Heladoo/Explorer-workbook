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


# -- heuristic fallback --------------------------------------------------


def test_heuristic_provider_always_answers():
    knowledge = HeuristicKnowledgeProvider().fetch("Somewhere Unlisted")
    assert knowledge.coverage() == len(KNOWLEDGE_FIELDS)
    assert knowledge.source == "heuristic"
    assert knowledge.notes, "generic material must say that it is generic"


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
