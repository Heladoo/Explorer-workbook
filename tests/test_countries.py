"""data/countries.json: strict load, and every token it uses must resolve
in every shipped locale (see src/countries.py's module docstring for why
this is stricter than a destination pack)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.countries import CountryDataError, countries, country_for
from src.locales import en, he

ROOT = Path(__file__).resolve().parents[1]
DESTINATIONS_DIR = ROOT / "data" / "destinations"

_LOCALE_MODULES = (en, he)


def test_loads_without_raising():
    table = countries()
    assert len(table) >= 20


def test_every_code_is_its_own_key():
    for code, facts in countries().items():
        assert facts.code == code


def test_country_for_is_case_insensitive():
    assert country_for("gr") is country_for("GR")


def test_country_for_unknown_code_is_none_not_an_error():
    assert country_for("ZZ") is None
    assert country_for("") is None


def test_every_country_has_at_least_one_language():
    for facts in countries().values():
        assert facts.languages
        assert facts.primary_language == facts.languages[0]


def test_every_country_has_flag_colours():
    for facts in countries().values():
        assert facts.flag_colours


@pytest.mark.parametrize("locale", _LOCALE_MODULES, ids=lambda m: m.LANGUAGE)
def test_every_capital_resolves_in_every_locale(locale):
    keys = set(locale.STRINGS)
    for facts in countries().values():
        assert f"place.{facts.capital}" in keys, facts.capital


@pytest.mark.parametrize("locale", _LOCALE_MODULES, ids=lambda m: m.LANGUAGE)
def test_every_country_name_resolves_in_every_locale(locale):
    keys = set(locale.STRINGS)
    for facts in countries().values():
        assert f"country.{facts.name}" in keys, facts.name


@pytest.mark.parametrize("locale", _LOCALE_MODULES, ids=lambda m: m.LANGUAGE)
def test_every_continent_resolves_in_every_locale(locale):
    keys = set(locale.STRINGS)
    for facts in countries().values():
        assert f"continent.{facts.continent}" in keys, facts.continent


@pytest.mark.parametrize("locale", _LOCALE_MODULES, ids=lambda m: m.LANGUAGE)
def test_every_currency_resolves_in_every_locale(locale):
    keys = set(locale.STRINGS)
    for facts in countries().values():
        assert f"currency.{facts.currency}" in keys, facts.currency


@pytest.mark.parametrize("locale", _LOCALE_MODULES, ids=lambda m: m.LANGUAGE)
def test_every_flag_colour_resolves_in_every_locale(locale):
    keys = set(locale.STRINGS)
    for facts in countries().values():
        for colour in facts.flag_colours:
            assert f"colour.{colour}" in keys, colour


@pytest.mark.parametrize("locale", _LOCALE_MODULES, ids=lambda m: m.LANGUAGE)
def test_every_language_resolves_in_every_locale(locale):
    keys = set(locale.STRINGS)
    for facts in countries().values():
        for code in facts.languages:
            assert f"language.{code}" in keys, code


def test_every_destination_pack_names_a_known_country():
    """Every shipped base pack's ``country`` (when it names one at all) must
    be an entry countries() actually has — a typo here would silently make
    the quiz's country-fact questions disappear for that destination without
    any test noticing, since QuizActivity degrades gracefully by design."""
    for path in sorted(DESTINATIONS_DIR.glob("*.json")):
        if "." in path.stem:  # a <slug>.<lang>.json translation overlay
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        code = data.get("country")
        if code:
            assert country_for(code) is not None, f"{path.name} names unknown country {code!r}"


# -- strict-loader failure modes ------------------------------------------


def _write(tmp_path: Path, payload: dict) -> Path:
    path = tmp_path / "countries.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_rejects_unknown_continent(tmp_path):
    path = _write(
        tmp_path,
        {
            "countries": {
                "XX": {
                    "name": "nowhere", "capital": "nowhere_city", "continent": "narnia",
                    "currency": "usd", "languages": ["en"], "flag_colours": ["red"],
                }
            }
        },
    )
    with pytest.raises(CountryDataError, match="continent"):
        countries(path)


def test_rejects_unknown_colour(tmp_path):
    path = _write(
        tmp_path,
        {
            "countries": {
                "XX": {
                    "name": "nowhere", "capital": "nowhere_city", "continent": "europe",
                    "currency": "usd", "languages": ["en"], "flag_colours": ["chartreuse"],
                }
            }
        },
    )
    with pytest.raises(CountryDataError, match="colour"):
        countries(path)


def test_rejects_missing_field(tmp_path):
    path = _write(
        tmp_path,
        {"countries": {"XX": {"name": "nowhere", "capital": "nowhere_city"}}},
    )
    with pytest.raises(CountryDataError, match="missing field"):
        countries(path)


def test_rejects_unknown_field(tmp_path):
    path = _write(
        tmp_path,
        {
            "countries": {
                "XX": {
                    "name": "nowhere", "capital": "nowhere_city", "continent": "europe",
                    "currency": "usd", "languages": ["en"], "flag_colours": ["red"],
                    "population": 1000,
                }
            }
        },
    )
    with pytest.raises(CountryDataError, match="unknown field"):
        countries(path)


def test_rejects_lowercase_code(tmp_path):
    path = _write(
        tmp_path,
        {
            "countries": {
                "xx": {
                    "name": "nowhere", "capital": "nowhere_city", "continent": "europe",
                    "currency": "usd", "languages": ["en"], "flag_colours": ["red"],
                }
            }
        },
    )
    with pytest.raises(CountryDataError, match="uppercase"):
        countries(path)
