"""Draft a destination pack from deterministic public APIs.

An **authoring tool**, not part of the pipeline — nothing under ``src/``
imports it, the same posture as ``tools/make_shadow_symbols.py``. It never
writes into ``data/``: it prints a draft pack and a review report, and a
human decides what to commit. That split is the whole point. Every field
below is machine-fetched from a source that can be re-checked, but "fetched
from a real source" is not the same as "fit for a child's workbook" (see
the landmark stoplist), and only a person can close that gap.

What it fills, and from where:

``country`` + a ``data/countries.json`` row
    Wikidata, **rank-filtered**. A raw property read is not usable: Greece's
    ``P36`` returns Athens *and Aegina* (a capital from the 1820s), and
    ``P38`` returns the drachma alongside the euro, because Wikidata records
    history beside the present. Taking preferred-rank claims (falling back
    to normal rank) and dropping anything carrying an end-time qualifier
    (``P582``) reduces both to exactly one current value.
``profile.environments``
    Wikidata ``P31`` instance-of, walked up the ``P279`` subclass chain, plus
    ``P206`` (body of water) — and GeoNames terrain features when an account
    is configured. Deliberately a *classification*, not a measurement: see
    ``environments_from_wikidata`` for why elevation alone is not evidence.
``wildlife``
    iNaturalist observation counts near the coordinates, rolled up to the
    **family** rank and then filtered for distinctiveness (see
    ``wildlife_nearby``). Ranked by what people actually record seeing there,
    generalized by the taxonomy itself rather than by a language model
    ("Marginated Tortoise" and "Hermann's Tortoise" are both Testudinidae,
    which iNaturalist already names "Tortoises"), and checked against a
    worldwide baseline so a family that is common on nearly every continent
    (crows, ducks, herons, gulls, hawks — see ``COSMOPOLITAN_RANK_CUTOFF``)
    is dropped even when it is the single most-observed thing locally. A
    workbook about *this* trip should show what is distinctive about it, not
    what is distinctive about being outdoors anywhere. Deliberately not read
    by the quiz activity (``src/activities/quiz.py``) — a real-vs-silly
    distractor format has no way to represent "this animal is only worth
    asking about because it's genuinely local", so the one fact that matters
    about a wildlife entry would be invisible on that page.
``landmarks``
    Wikipedia GeoSearch within 10 km (the API's own radius cap). Every result
    is a *candidate* — this is the field that most needs human review.
``aliases``
    The destination's own name in every language the workbook ships (see
    ``native_aliases`` — reads ``src.strings.available_languages()``, so a
    new locale gets picked up automatically), plus the original search term
    if it differs from Wikidata's resolved label.
``region``
    ``"<administrative region>, <country>"`` from Wikidata ``P131``. Not read
    by any pipeline code — it is documentary only, matching the free-text
    field every hand-curated pack already carries.
``profile.climate``
    Five years of daily highs/lows/rainfall from Open-Meteo, reduced to
    hot/cold/wet/dry/temperate by fixed thresholds (see
    ``climate_from_open_meteo``). Real measured data, but **not the same
    thing as a pack's climate character** — checked against Pelion's own
    committed pack (``["temperate", "hot"]``), the coordinate's actual
    5-year hottest-month average is only 21.5°C, nowhere near "hot" by any
    honest threshold. An annual mean describes the whole year; "hot" in a
    hand-written pack almost certainly describes a July visit. Both are
    correct — a workbook author's sense of the place is not a measurement
    error, so this is reported as a data point to weigh, not a correction.

What it deliberately leaves empty, with a reason recorded in the report:

``activities``, ``local_food``
    No public API describes "things a family does here" or "food a child will
    be offered" at the register a workbook needs. These are the two fields
    that drive coloring-page scenes, so they are exactly where human wording
    matters most.
``plants``
    iNaturalist is biased toward what observers photograph, not what a
    visitor sees: for Pelion its top families are orchids and mints, while
    the olive groves and chestnut forests that define the place visually
    barely register. Rolled-up family names ("Mint Family", "Legumes") are
    botany-class words, not visitor words, so this is not a tuning problem.
``weather``, ``history``, ``interesting_facts``
    Prose, not data.

Usage::

    python tools/fetch_destination.py "Pelion"
    python tools/fetch_destination.py "Pelion" --qid Q1334825
    python tools/fetch_destination.py "Prague" --out draft-prague.json

Stdlib only, like the rest of the project's core.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable

REPO_ROOT = Path(__file__).resolve().parents[1]
ENV_FILE = REPO_ROOT / ".env"

# Only for src.strings.available_languages() (see native_aliases) — the same
# sys.path fix tools/register_doodle_symbols.py already needs to import from
# src when run as a plain script rather than a package.
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.strings import available_languages  # noqa: E402

USER_AGENT = "ExplorerWorkbook/0.1 (children's travel workbook generator; authoring tool)"

WIKIDATA_ENTITY = "https://www.wikidata.org/wiki/Special:EntityData/{qid}.json"
WIKIDATA_SEARCH = "https://www.wikidata.org/w/api.php?action=wbsearchentities&format=json&language=en&limit=7&search={term}"
WIKIPEDIA_GEOSEARCH = (
    "https://en.wikipedia.org/w/api.php?action=query&format=json&list=geosearch"
    "&gscoord={lat}%7C{lng}&gsradius={radius}&gslimit=40"
)
INAT_SPECIES = (
    "https://api.inaturalist.org/v1/observations/species_counts"
    "?lat={lat}&lng={lng}&radius={radius}&quality_grade=research"
    "&iconic_taxa={iconic}&per_page=200&locale=en"
)
INAT_SPECIES_GLOBAL = (
    "https://api.inaturalist.org/v1/observations/species_counts"
    "?quality_grade=research&iconic_taxa={iconic}&per_page=200&locale=en"
)
INAT_TAXA = "https://api.inaturalist.org/v1/taxa/{ids}?locale=en"
INAT_ICONIC_TAXA = "Aves,Mammalia,Reptilia,Amphibia"

#: A family ranked in the global top N (by worldwide iNaturalist observation
#: count, across every place on the platform) is common on more or less every
#: continent — the "you'd see this crow at home too" case. Excluded from a
#: destination's wildlife list by default, no matter how often it turns up
#: locally, because a workbook about *this* trip should show what's
#: distinctive about it, not what's distinctive about being outdoors at all.
#: Picked from the actual global ranking (see the module's probe notes):
#: rank 1-9 is Ducks/Herons/Crows/Hawks-Eagles/Pigeons/Finches/Thrushes/
#: Sparrows/Woodpeckers — every one of them a back-garden bird on any
#: continent iNaturalist has decent coverage of. Rank 10+ starts admitting
#: things that are common *somewhere in particular* rather than everywhere
#: (gulls, deer, pond turtles), which is a different, allowed case.
COSMOPOLITAN_RANK_CUTOFF = 10

#: Never return fewer than this many wildlife entries even if the ubiquity
#: filter would otherwise remove everything — a thin destination should
#: still get a wildlife section, just one that says plainly (in the report)
#: that it fell back to "common anywhere" rather than pretending otherwise.
_MIN_WILDLIFE = 4
GEONAMES_NEARBY = (
    "http://api.geonames.org/findNearbyJSON?lat={lat}&lng={lng}&radius={radius}"
    "&maxRows=25&featureClass={fclass}&username={user}"
)
OPEN_METEO_ARCHIVE = (
    "https://archive-api.open-meteo.com/v1/archive?latitude={lat}&longitude={lng}"
    "&start_date={start}&end_date={end}"
    "&daily=temperature_2m_max,temperature_2m_min,precipitation_sum&timezone=auto"
)
#: Five full calendar years — long enough to average out one freak heatwave
#: or drought year, short enough that one request stays fast. Fixed range
#: rather than "last 5 years" so a re-run reproduces the same numbers.
OPEN_METEO_YEARS = ("2019-01-01", "2023-12-31")

#: Deterministic thresholds over a coordinate's 5-year daily record, applied
#: to two numbers: the hottest calendar month's average daily *high*, and the
#: coldest calendar month's average daily *low*. "temperate" is the default
#: for anything short of a climate extreme in either direction, so it
#: legitimately combines with "hot" or "cold" — a place can have a properly
#: cold winter and still read as an otherwise ordinary four-season climate
#: (see Prague/Pelion's own committed packs, both temperate + one extreme).
#: Calibrated by checking real 5-year numbers against the two destinations
#: this project already has hand-curated ``profile.climate`` for (see
#: ``climate_from_open_meteo``'s docstring for the one place they disagree).
_HOT_THRESHOLD_C = 28.0
_COLD_THRESHOLD_C = 0.0
_WET_THRESHOLD_MM = 900.0
_DRY_THRESHOLD_MM = 400.0
_TEMPERATE_COLD_FLOOR_C = -15.0
_TEMPERATE_HOT_CEILING_C = 35.0

#: Wikidata class -> the ``src/symbols/vocab.py`` environments it implies.
#: Keyed on *classes*, reached by walking ``P279`` up from the destination's
#: own ``P31``, because a type is evidence and a measurement is not.
#: A river gets both ``water`` and ``riverside``: ``riverside`` is a real
#: place-type (riverside walks, riverside cafes) a lake or open sea claim
#: doesn't earn, and it's additive rather than a replacement for ``water`` —
#: existing symbol facets and ``maze.py``'s goal-icon table already key off
#: ``water``/``coast`` (see the packing/maze consumers), so a river-adjacent
#: destination still matches everything it always did, plus this one more
#: specific signal.
_CLASS_ENVIRONMENTS: dict[str, tuple[str, ...]] = {
    "Q8502": ("mountain",),        # mountain
    "Q54050": ("mountain",),       # hill
    "Q46831": ("mountain",),       # mountain range
    "Q207326": ("mountain",),      # massif
    "Q23442": ("coast", "water"),  # island
    "Q40080": ("coast",),          # beach
    "Q93352": ("coast",),          # bay
    "Q165": ("coast", "water"),    # sea
    "Q9430": ("coast", "water"),   # ocean
    "Q23397": ("water",),          # lake
    "Q4022": ("water", "riverside"),  # river
    "Q4421": ("forest",),          # forest
    "Q8514": ("desert",),          # desert
    "Q515": ("city",),             # city
    "Q1549591": ("city",),         # big city
    "Q3957": ("village",),         # town
    "Q532": ("village",),          # village
    "Q46169": ("forest",),         # national park
    "Q22698": ("forest",),         # park
    "Q39816": ("mountain",),       # valley
}

#: GeoNames feature *codes* -> environments. Terrain actually present near the
#: point, which is the signal elevation was never a substitute for. Deliberately
#: excludes GeoNames' own ``HLL`` (hill) code: querying Munich — flat, no real
#: relief for kilometres — turned up "Perlacher Mugl", 20 km out, which
#: Wikidata's own German description names outright as a "künstlicher Berg"
#: (artificial hill): a landscaped WWII rubble mound, not terrain. ``HLL`` is
#: too coarse a bucket — it can't tell that from an actual foothill — so it is
#: the same kind of weak, easily-wrong signal elevation already was; ``MT``
#: (mountain) and ``PK``/``RDGE`` (peak/ridge) stay because those codes are
#: specific enough that GeoNames itself only applies them to real relief.
_GEONAMES_ENVIRONMENTS: dict[str, tuple[str, ...]] = {
    "MT": ("mountain",), "PK": ("mountain",), "RDGE": ("mountain",),
    "BCH": ("coast",), "CST": ("coast",), "CAPE": ("coast",), "COVE": ("coast",),
    "BAY": ("coast", "water"), "HBR": ("coast", "water"),
    "LK": ("water",), "STM": ("water", "riverside"), "SEA": ("coast", "water"),
    "FRST": ("forest",), "GROVE": ("forest",),
    "DSRT": ("desert",), "DUNE": ("desert",),
    "PPL": ("village",), "PPLA": ("city",), "PPLA2": ("city",), "PPLC": ("city",),
    "FRM": ("farm",), "VINS": ("farm",), "GRVE": ("farm",),
}

#: iNaturalist family common names are list-shaped ("Gulls, Terns, and
#: Skimmers"). Splitting on the first comma gets most of the way; this table
#: covers the ones where the first segment is still not a word a child uses.
#: Written once, reused for every destination — the curated asset that makes
#: the taxonomy rollup usable without a language model.
_FAMILY_OVERRIDES: dict[str, str] = {
    "true toads": "toads",
    "colubrid snakes": "snakes",
    "wall lizards": "lizards",
    "typical frogs": "frogs",
    "hawks": "eagles",
    "old world flycatchers": "robins",
    "sandpipers": "wading birds",
    "wagtails": "small birds",
    "true finches": "finches",
    "swallows": "swallows",
    "pigeons": "pigeons",
    "herons": "herons",
    "gulls": "seagulls",
    "crows": "crows",
    "ducks": "ducks",
    "tortoises": "tortoises",
    "geckos": "geckos",
    "squirrels": "squirrels",
    "deer": "deer",
    "bats": "bats",
    "cats": "cats",
    "dogs": "dogs",
    "horses": "horses",
    "cattle, antelopes, sheep, and goats": "goats",
}

#: A Wikipedia GeoSearch result matching any of these is never offered as a
#: landmark. This book is for four-to-ten-year-olds; a nearby page can just as
#: easily be a wartime atrocity as a clock tower ("Drakeia massacre" is 6.4 km
#: from Pelion's summit and comes back in the same response as the monastery).
_LANDMARK_STOPWORDS = (
    "massacre", "battle", "war ", " war", "cemetery", "grave", "tomb", "prison",
    "execution", "victims", "holocaust", "genocide", "disaster", "crash",
    "earthquake", "shooting", "bombing", "siege", "military", "airbase",
    "hospital", "asylum", "murder", "assassination", "concentration camp",
)

#: Administrative and disambiguation pages are places on a map, not sights.
#: The year-prefixed branch is evidence-based, not speculative: Prague turned
#: up "1972 UCI Cyclo-cross World Championships" and Munich turned up three
#: more ("1997"/"1985 UCI Cyclo-cross World Championships", "2022 European
#: Road Championships") — a one-off sporting event hosted in a city becomes
#: a permanent, geotagged Wikipedia page there, and GeoSearch has no way to
#: distinguish "a thing you can visit" from "a thing that happened here once".
#: A landmark title essentially never starts with a bare year, which makes
#: this a precise, cheap signature rather than a guess.
_LANDMARK_NOISE = re.compile(
    r"\((disambiguation|municipality|regional unit|prefecture)\)|"
    r"^(list of|history of|geography of)\b|"
    r"^\d{4}\b.*\b(championships?|olympics|world cup|grand prix|games)\b",
    re.IGNORECASE,
)


# -- plumbing --------------------------------------------------------------


def read_env() -> dict[str, str]:
    """Parse ``.env`` into a dict. Absent file is fine — every key is optional."""
    values: dict[str, str] = {}
    if not ENV_FILE.is_file():
        return values
    for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        values[key.strip()] = value.strip()
    return values


def get_json(url: str, *, attempts: int = 4) -> Any:
    """GET and parse JSON, backing off on 429/5xx.

    Wikidata's query service in particular rate-limits hard during incidents,
    and a draft-a-pack run is not worth failing over a transient 429.
    """
    last: Exception | None = None
    for attempt in range(attempts):
        request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        try:
            with urllib.request.urlopen(request, timeout=60) as response:  # noqa: S310
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            last = exc
            if exc.code in (429, 500, 502, 503, 504) and attempt < attempts - 1:
                time.sleep(2 ** attempt)
                continue
            raise
        except (urllib.error.URLError, TimeoutError) as exc:
            last = exc
            if attempt < attempts - 1:
                time.sleep(2 ** attempt)
                continue
            raise
    raise RuntimeError(f"unreachable: {last}")


def token(text: str) -> str:
    """A locale vocabulary token: lowercase, underscores, no punctuation.

    ``data/countries.json`` stores tokens (``athens``, ``north_america``), not
    display text — every value is translated through the locale modules.
    """
    cleaned = re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")
    return cleaned


# -- Wikidata --------------------------------------------------------------


def resolve_qid(name: str) -> tuple[str, list[dict[str, str]]]:
    """Best-guess QID for a destination name, plus the alternatives.

    Returns the alternatives too because the first hit is regularly wrong —
    searching "Pelion" offers the Greek mountain, an asteroid, a town in South
    Carolina and an ancient Chaonian fort. The report prints them so a human
    can re-run with ``--qid``.
    """
    data = get_json(WIKIDATA_SEARCH.format(term=urllib.parse.quote(name)))
    hits = [
        {"qid": h["id"], "label": h.get("label", ""), "description": h.get("description", "")}
        for h in data.get("search", [])
    ]
    if not hits:
        raise SystemExit(f"Wikidata has no entity matching {name!r}")
    return hits[0]["qid"], hits


def entity(qid: str) -> dict[str, Any]:
    return get_json(WIKIDATA_ENTITY.format(qid=qid))["entities"][qid]


def current_claims(claims: dict[str, Any], prop: str) -> list[str]:
    """QIDs of a property's *currently true* claims.

    Preferred-rank claims win when present, normal rank otherwise; anything
    carrying an end time (``P582``) is a former value and is dropped. Without
    this, Greece's capital reads ``['Athens', None, 'Aegina', 'Athens']``.
    """
    rows = [c for c in claims.get(prop, []) if c.get("rank") != "deprecated"]
    rows = [c for c in rows if "P582" not in (c.get("qualifiers") or {})]
    chosen = [c for c in rows if c.get("rank") == "preferred"] or rows
    out: list[str] = []
    for claim in chosen:
        value = claim["mainsnak"].get("datavalue", {}).get("value")
        if isinstance(value, dict) and "id" in value:
            out.append(value["id"])
    return out


def claim_string(claims: dict[str, Any], prop: str) -> str | None:
    """First string-valued claim (ISO codes: ``P498`` currency, ``P218`` lang)."""
    for claim in claims.get(prop, []):
        value = claim["mainsnak"].get("datavalue", {}).get("value")
        if isinstance(value, str):
            return value
    return None


def label_of(qid: str, lang: str = "en") -> str | None:
    return entity(qid)["labels"].get(lang, {}).get("value")


def native_aliases(qid: str, english_label: str) -> list[str]:
    """This place's own name in every language the workbook actually ships.

    Reads ``src.strings.available_languages()`` rather than hardcoding
    "he" — the alias list stays in sync automatically if a third locale is
    ever added, the same way ``src/fonts.py`` derives its embedded-font set
    from what a book's markup actually needs rather than a fixed list.
    A Hebrew-language book about a destination should be findable by its
    Hebrew name (see ``pelion.json``'s own ``"פליון"`` alias) — this is that,
    fetched rather than typed by hand, and it costs one Wikidata field this
    tool was already downloading.
    """
    aliases: list[str] = []
    for language in available_languages():
        if language == "en":
            continue
        native = label_of(qid, language)
        if native and native.lower() != english_label.lower() and native not in aliases:
            aliases.append(native)
    return aliases


def environments_from_wikidata(claims: dict[str, Any]) -> tuple[list[str], list[str]]:
    """Environment tags implied by what this place *is*, plus the evidence.

    Walks ``P31`` up the ``P279`` subclass chain, so "stratovolcano" still
    reaches "mountain" without every subtype being listed here, and adds
    ``P206`` (located next to a body of water) because a coastline is an
    authored claim rather than something to infer.

    Elevation (``P2044``) is deliberately **not** consulted. It is a
    measurement, not a classification, and on its own it is wrong in both
    directions: Mexico City sits at 2 240 m and is a city, not a mountain,
    while a sea-cliff village at 40 m is unmistakably coastal. Where a class
    already says "mountain", elevation adds nothing; where it does not,
    elevation is not evidence enough to overrule it.
    """
    found: list[str] = []
    evidence: list[str] = []
    seen: set[str] = set()
    frontier = list(current_claims(claims, "P31"))

    depth = 0
    while frontier and depth < 6:
        next_frontier: list[str] = []
        for qid in frontier:
            if qid in seen:
                continue
            seen.add(qid)
            if qid in _CLASS_ENVIRONMENTS:
                name = label_of(qid) or qid
                for tag in _CLASS_ENVIRONMENTS[qid]:
                    if tag not in found:
                        found.append(tag)
                        evidence.append(f"{tag} <- Wikidata class {qid} ({name})")
                continue  # an anchor class is specific enough; stop climbing it
            try:
                next_frontier.extend(current_claims(entity(qid)["claims"], "P279"))
            except Exception:  # a class page that won't load is not fatal
                continue
        frontier = next_frontier
        depth += 1

    for qid in current_claims(claims, "P206"):
        name = label_of(qid) or qid
        tags = ("water", "coast") if _is_coastal_water(qid) else ("water",)
        for tag in tags:
            if tag not in found:
                found.append(tag)
                evidence.append(f"{tag} <- P206 next to {name}")

    return found, evidence


def _is_coastal_water(qid: str) -> bool:
    """Whether a body of water (``P206``'s target) actually implies a coastline.

    A city can sit "next to" a river, a lake, a reservoir or a sea — ``P206``
    does not distinguish. Only the last of those is a coast: Prague sits on
    the Vltava, a river (Q131574), which is landlocked Czechia's only
    connection to any water at all — tagging that "coast" would be wrong in
    the same way elevation-as-mountain-evidence was wrong, just for water
    instead of terrain. Checked by direct ``P31`` class only (sea/ocean/bay
    are not usually stated several subclass hops down), which keeps this
    cheap; a body typed as neither is treated as inland.
    """
    classes = current_claims(entity(qid)["claims"], "P31")
    return any(cls in {"Q165", "Q9430", "Q93352", "Q1322134"} for cls in classes)  # sea, ocean, bay, gulf


def region_of(claims: dict[str, Any], country_label: str) -> str | None:
    """A human-readable "<administrative region>, <country>" string.

    ``P131`` (located in the administrative territorial entity) at
    preferred rank, falling back to normal rank the same way
    ``current_claims`` does for everything else. Matches the free-text
    ``"region"`` field every hand-curated pack already carries (Pelion's
    "Thessaly, Greece", Prague's "Bohemia, Czech Republic") — this field is
    not read by any pipeline code (nothing in ``src/`` parses it), so it is
    documentary only, but it is real, sourced data rather than nothing.
    """
    region_qids = current_claims(claims, "P131")
    if not region_qids:
        return None
    name = label_of(region_qids[0])
    if not name:
        return None
    return f"{name}, {country_label}" if country_label else name


def country_row(country_qid: str) -> tuple[dict[str, Any], list[str]]:
    """A ``data/countries.json`` row in the repo's own vocabulary tokens."""
    warnings: list[str] = []
    claims = entity(country_qid)["claims"]

    name = label_of(country_qid) or country_qid
    capitals = current_claims(claims, "P36")
    continents = current_claims(claims, "P30")

    currency_code = None
    for qid in current_claims(claims, "P38"):
        currency_code = claim_string(entity(qid)["claims"], "P498")  # ISO 4217
        if currency_code:
            break
    if not currency_code:
        warnings.append("no ISO 4217 currency code found (P38 -> P498)")

    languages: list[str] = []
    for qid in current_claims(claims, "P37"):
        code = claim_string(entity(qid)["claims"], "P218")  # ISO 639-1
        if code and code not in languages:
            languages.append(code)
    if not languages:
        warnings.append("no ISO 639-1 language code found (P37 -> P218)")

    colours: list[str] = []
    for flag_qid in current_claims(claims, "P163"):
        for colour_qid in current_claims(entity(flag_qid)["claims"], "P462"):
            colour = label_of(colour_qid)
            if colour and token(colour) not in colours:
                colours.append(token(colour))
        if colours:
            break
    if not colours:
        warnings.append("no flag colours found (P163 -> P462)")

    row = {
        "name": token(name),
        "capital": token(label_of(capitals[0]) or "") if capitals else "",
        "continent": token(label_of(continents[0]) or "") if continents else "",
        "currency": (currency_code or "").lower(),
        "languages": languages,
        "flag_colours": colours,
    }
    for field in ("capital", "continent"):
        if not row[field]:
            warnings.append(f"no {field} found")
    return row, warnings


# -- iNaturalist -----------------------------------------------------------


def _family_rollup(observations: list[dict[str, Any]]) -> tuple[dict[str, int], dict[str, list[str]]]:
    """Roll a ``species_counts`` result up from species to family.

    Shared by the local query and the global baseline so both are rolled up
    identically — the family-rank comparison between them only means
    anything if the same taxonomy walk produced both sides.
    """
    counts: dict[tuple[int, ...], int] = defaultdict(int)
    samples: dict[tuple[int, ...], list[str]] = defaultdict(list)
    for row in observations:
        taxon = row["taxon"]
        key = tuple(taxon.get("ancestor_ids", []))
        counts[key] += row["count"]
        samples[key].append(taxon.get("preferred_common_name") or taxon["name"])

    ancestor_ids = sorted({i for key in counts for i in key})
    resolved: dict[int, tuple[str, str]] = {}
    for start in range(0, len(ancestor_ids), 30):
        chunk = ancestor_ids[start : start + 30]
        taxa = get_json(INAT_TAXA.format(ids=",".join(map(str, chunk))))
        for taxon in taxa.get("results", []):
            resolved[taxon["id"]] = (
                taxon.get("rank", ""),
                taxon.get("preferred_common_name") or taxon.get("name", ""),
            )

    families: dict[str, int] = defaultdict(int)
    family_samples: dict[str, list[str]] = defaultdict(list)
    for key, count in counts.items():
        family_name = None
        for ancestor in reversed(key):
            if resolved.get(ancestor, ("", ""))[0] == "family":
                family_name = resolved[ancestor][1]
                break
        if not family_name:
            continue
        families[family_name] += count
        family_samples[family_name].extend(samples[key])
    return dict(families), dict(family_samples)


def _global_family_ranks() -> dict[str, tuple[int, int]]:
    """Every family's worldwide rank, family name -> (rank, observation count).

    One call across the whole iNaturalist platform, no location filter — the
    "found everywhere" baseline every destination is compared against. Not
    cached: it costs one request and a couple of seconds, which is small
    next to the rest of this tool's run, and a fresh baseline is one fewer
    thing that can go stale silently.
    """
    data = get_json(INAT_SPECIES_GLOBAL.format(iconic=urllib.parse.quote(INAT_ICONIC_TAXA)))
    families, _samples = _family_rollup(data.get("results", []))
    ranked = sorted(families.items(), key=lambda kv: -kv[1])
    return {name: (rank, count) for rank, (name, count) in enumerate(ranked, start=1)}


def wildlife_nearby(lat: float, lng: float, radius: int = 30) -> tuple[list[str], list[str]]:
    """Animal groups worth putting in front of a child at this destination.

    Two filters, not one. Every candidate is first rolled up from species to
    family and ranked by local observations, same as before — that answers
    "can you actually see this here". Then each surviving family is checked
    against ``_global_family_ranks()``: a family common on nearly every
    continent (ducks, herons, crows, gulls, pigeons — see
    ``COSMOPOLITAN_RANK_CUTOFF``) is dropped even if it is the single
    most-observed thing at this destination, because "you'd see this at home
    too" is exactly the entry a workbook about *this* trip should not spend a
    page on. A family with no meaningful global footprint (not in the
    worldwide top 200 at all — tortoises, for Pelion) is the strongest
    possible pass: genuinely distinctive, not just locally convenient.

    Family-level comparison is a real approximation, not a precise one — it
    can't tell "Common Buzzard" (Pelion) from "Bald Eagle" (Florida) inside
    the shared "Hawks, Eagles, and Kites" family, so an emblematic *species*
    inside a globally common *family* still gets filtered out here. The
    report prints both ranks for every candidate so a human curating the
    draft can put one back by hand — the filter is a first pass, not a veto.
    """
    data = get_json(
        INAT_SPECIES.format(lat=lat, lng=lng, radius=radius, iconic=urllib.parse.quote(INAT_ICONIC_TAXA))
    )
    families, family_samples = _family_rollup(data.get("results", []))
    global_ranks = _global_family_ranks()

    ranked_local = sorted(families.items(), key=lambda kv: -kv[1])

    def to_term(family: str) -> str:
        head = re.split(r",| and ", family)[0].strip().lower()
        return _FAMILY_OVERRIDES.get(family.lower()) or _FAMILY_OVERRIDES.get(head) or head

    kept: list[tuple[str, str, int]] = []  # (term, family, local_count)
    dropped: list[tuple[str, str, int, int]] = []  # (term, family, local_count, global_rank)
    seen_terms: set[str] = set()
    for family, local_count in ranked_local:
        term = to_term(family)
        if term in seen_terms:
            continue
        global_rank, global_count = global_ranks.get(family, (None, 0))
        cosmopolitan = global_rank is not None and global_rank <= COSMOPOLITAN_RANK_CUTOFF
        if cosmopolitan:
            dropped.append((term, family, local_count, global_rank))
            continue
        seen_terms.add(term)
        kept.append((term, family, local_count))

    report: list[str] = []
    forced_back = 0
    if len(kept) < _MIN_WILDLIFE and dropped:
        # A destination whose only visible fauna are the cosmopolitan kind
        # (an urban park, say) should not print an empty wildlife section —
        # top up from what was dropped, least-ubiquitous first, and say so.
        dropped.sort(key=lambda row: -row[3])  # highest global rank number = least ubiquitous
        while len(kept) < _MIN_WILDLIFE and dropped:
            term, family, local_count, _rank = dropped.pop(0)
            if term in seen_terms:
                continue
            seen_terms.add(term)
            kept.append((term, family, local_count))
            forced_back += 1

    for term, family, local_count in kept[:12]:
        global_rank, global_count = global_ranks.get(family, (None, 0))
        distinctiveness = "not in global top 200 — distinctive" if global_rank is None else f"global rank #{global_rank}"
        sample = ", ".join(family_samples.get(family, [])[:2])
        report.append(
            f"  keep  {term:<14} {local_count:>5} obs locally  ({distinctiveness})  <- {family} ({sample})"
        )
    if forced_back:
        report.append(
            f"  ! only {len(kept) - forced_back} distinctive families found; topped up "
            f"{forced_back} common one(s) rather than print a short wildlife list — review these"
        )
    for term, family, local_count, global_rank in dropped:
        if any(term == k[0] for k in kept):
            continue
        report.append(
            f"  drop  {term:<14} {local_count:>5} obs locally  (global rank #{global_rank} — "
            "found on nearly every continent, not distinctive to here)"
        )

    return [term for term, _family, _count in kept[:12]], report


# -- Wikipedia / GeoNames --------------------------------------------------


def landmarks_nearby(lat: float, lng: float, exclude: str) -> tuple[list[str], list[str]]:
    """Nearby Wikipedia places, minus anything unfit for a children's book."""
    data = get_json(WIKIPEDIA_GEOSEARCH.format(lat=lat, lng=lng, radius=10000))
    kept: list[str] = []
    rejected: list[str] = []
    for place in data.get("query", {}).get("geosearch", []):
        title = place["title"]
        lowered = f" {title.lower()} "
        if title.lower() == exclude.lower():
            continue
        if any(stop in lowered for stop in _LANDMARK_STOPWORDS):
            rejected.append(f"  BLOCKED  {title}  ({place['dist']/1000:.1f} km)")
            continue
        if _LANDMARK_NOISE.search(title):
            rejected.append(f"  noise    {title}")
            continue
        kept.append(title)
    return kept[:10], rejected


def geonames_environments(lat: float, lng: float, user: str) -> tuple[list[str], list[str]]:
    """Environment tags from real terrain features near the point."""
    found: list[str] = []
    evidence: list[str] = []
    for feature_class in ("T", "H", "V", "P", "L"):
        url = GEONAMES_NEARBY.format(
            lat=lat, lng=lng, radius=20, fclass=feature_class, user=urllib.parse.quote(user)
        )
        try:
            data = get_json(url)
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", "replace")
            evidence.append(f"  GeoNames unavailable (HTTP {exc.code}): {body.strip()[:120]}")
            return found, evidence
        if "status" in data:
            evidence.append(f"  GeoNames error: {data['status'].get('message')}")
            return found, evidence
        for place in data.get("geonames", []):
            tags = _GEONAMES_ENVIRONMENTS.get(place.get("fcode", ""))
            if not tags:
                continue
            for tag in tags:
                if tag not in found:
                    found.append(tag)
                    evidence.append(f"  {tag} <- {place.get('fcode')} {place.get('name')}")
    return found, evidence


def climate_from_open_meteo(lat: float, lng: float) -> tuple[list[str], list[str]]:
    """``profile.climate`` tags from five years of real daily weather.

    Two numbers drive every tag: the hottest calendar month's average daily
    high, and the coldest calendar month's average daily low, both averaged
    across ``OPEN_METEO_YEARS`` rather than read off a single year (a single
    hot or cold year would swing the tag). Annual rainfall drives ``wet``/
    ``dry`` the same way.

    This is real measured data, not a guess — and it can still disagree with
    how a human characterises a destination. Checked against Pelion's own
    committed pack: it calls the mountain ``["temperate", "hot"]``, but five
    years of daily highs at that exact coordinate average only 21.5°C in the
    hottest month — nowhere near ``_HOT_THRESHOLD_C``. That is not a bug in
    either the pack or this function: an annual mean describes the whole
    year, while "hot" in the hand-written pack almost certainly describes
    what a family visiting in July actually feels, at a specific point a
    human chose rather than wherever this tool's coordinate happens to land.
    A statistical read of one point's full year and a destination's peak-
    season character are genuinely different things, and this function can
    only ever produce the former — treat its output as a data point to weigh
    against the pack author's own sense of the place, not a correction of it.
    """
    start, end = OPEN_METEO_YEARS
    data = get_json(OPEN_METEO_ARCHIVE.format(lat=lat, lng=lng, start=start, end=end))
    daily = data.get("daily", {})
    dates = daily.get("time", [])
    highs = daily.get("temperature_2m_max", [])
    lows = daily.get("temperature_2m_min", [])
    rain = daily.get("precipitation_sum", [])

    month_highs: dict[int, list[float]] = defaultdict(list)
    month_lows: dict[int, list[float]] = defaultdict(list)
    year_rain: dict[str, float] = defaultdict(float)
    for date, hi, lo, mm in zip(dates, highs, lows, rain):
        if hi is not None:
            month_highs[int(date[5:7])].append(hi)
        if lo is not None:
            month_lows[int(date[5:7])].append(lo)
        if mm is not None:
            year_rain[date[:4]] += mm

    if not month_highs or not month_lows or not year_rain:
        return [], ["  Open-Meteo returned no usable daily data"]

    hottest_month_avg = max(sum(v) / len(v) for v in month_highs.values())
    coldest_month_avg = min(sum(v) / len(v) for v in month_lows.values())
    annual_rain = sum(year_rain.values()) / len(year_rain)

    tags: list[str] = []
    if hottest_month_avg >= _HOT_THRESHOLD_C:
        tags.append("hot")
    if coldest_month_avg <= _COLD_THRESHOLD_C:
        tags.append("cold")
    if annual_rain >= _WET_THRESHOLD_MM:
        tags.append("wet")
    elif annual_rain <= _DRY_THRESHOLD_MM:
        tags.append("dry")
    if _TEMPERATE_COLD_FLOOR_C < coldest_month_avg and hottest_month_avg < _TEMPERATE_HOT_CEILING_C:
        tags.append("temperate")

    report = [
        f"  hottest-month avg daily high: {hottest_month_avg:.1f}°C "
        f"(hot if ≥ {_HOT_THRESHOLD_C:.0f}°C)",
        f"  coldest-month avg daily low:  {coldest_month_avg:.1f}°C "
        f"(cold if ≤ {_COLD_THRESHOLD_C:.0f}°C)",
        f"  avg annual rainfall:          {annual_rain:.0f}mm "
        f"(wet if ≥ {_WET_THRESHOLD_MM:.0f}mm, dry if ≤ {_DRY_THRESHOLD_MM:.0f}mm)",
        f"  -> {tags or ['none']}",
    ]
    return tags, report


# -- assembly --------------------------------------------------------------


def build(name: str, qid: str | None, env: dict[str, str]) -> tuple[dict[str, Any], list[str]]:
    report: list[str] = []

    if qid:
        alternatives: list[dict[str, str]] = []
    else:
        qid, alternatives = resolve_qid(name)

    data = entity(qid)
    claims = data["claims"]
    label = data["labels"].get("en", {}).get("value", name)
    description = data["descriptions"].get("en", {}).get("value", "")

    report.append("=" * 72)
    report.append(f"RESOLVED  {label} ({qid}) — {description}")
    if alternatives[1:]:
        report.append("  other Wikidata matches (re-run with --qid to pick one):")
        for alt in alternatives[1:5]:
            report.append(f"    {alt['qid']:<12} {alt['label']} — {alt['description'][:60]}")

    coordinates = None
    for claim in claims.get("P625", []):
        value = claim["mainsnak"].get("datavalue", {}).get("value")
        if value:
            coordinates = (value["latitude"], value["longitude"])
            break
    if coordinates is None:
        raise SystemExit(f"{label} ({qid}) has no coordinates (P625) — cannot query by location")
    lat, lng = coordinates
    report.append(f"  coordinates: {lat:.4f}, {lng:.4f}")

    # -- country ----------------------------------------------------------
    country_code = ""
    country_facts: dict[str, Any] | None = None
    country_qids = current_claims(claims, "P17")
    if country_qids:
        country_claims = entity(country_qids[0])["claims"]
        country_code = claim_string(country_claims, "P297") or ""  # ISO 3166-1 alpha-2
        country_facts, country_warnings = country_row(country_qids[0])
        report.append("")
        report.append(f"COUNTRY   {country_code}  (rank-filtered Wikidata)")
        report.append(f"  {json.dumps(country_facts, ensure_ascii=False)}")
        for warning in country_warnings:
            report.append(f"  ! {warning}")
    else:
        report.append("  ! no country (P17) — quiz country questions will not appear")

    # -- environments ------------------------------------------------------
    environments, evidence = environments_from_wikidata(claims)
    report.append("")
    report.append("ENVIRONMENTS")
    for line in evidence:
        report.append(f"  {line}")
    geonames_user = env.get("GeoNamesUser", "")
    if geonames_user:
        extra, geo_evidence = geonames_environments(lat, lng, geonames_user)
        report.extend(geo_evidence)
        for tag in extra:
            if tag not in environments:
                environments.append(tag)
    else:
        report.append("  (no GeoNamesUser in .env — terrain features skipped)")
    report.append("  NOTE: elevation (P2044) is not used as evidence; see module docstring.")

    # -- wildlife ----------------------------------------------------------
    wildlife, wildlife_report = wildlife_nearby(lat, lng)
    report.append("")
    report.append(
        f"WILDLIFE  (iNaturalist, family rank; families in the global top "
        f"{COSMOPOLITAN_RANK_CUTOFF} are dropped as 'found everywhere')"
    )
    report.extend(wildlife_report)

    # -- landmarks ---------------------------------------------------------
    landmarks, rejected = landmarks_nearby(lat, lng, exclude=label)
    report.append("")
    report.append("LANDMARKS (Wikipedia GeoSearch, 10 km — ALL need human review)")
    for place in landmarks:
        report.append(f"    {place}")
    for line in rejected:
        report.append(line)

    # -- climate -------------------------------------------------------
    climate, climate_report = climate_from_open_meteo(lat, lng)
    report.append("")
    report.append("CLIMATE (Open-Meteo, 5-year daily average — see climate_from_open_meteo for caveats)")
    report.extend(climate_report)

    # -- region + native aliases ----------------------------------------
    region = region_of(claims, label_of(country_qids[0]) if country_qids else "")
    aliases = native_aliases(qid, label)
    if name.lower() != label.lower() and name not in aliases:
        aliases.append(name)
    if aliases:
        report.append("")
        report.append(f"ALIASES  {aliases}")
    if region:
        report.append(f"REGION   {region}")

    pack: dict[str, Any] = {
        "destination": label,
        "aliases": aliases,
        "region": region or "",
        "country": country_code,
        "profile": {
            "regions": [],
            "environments": environments,
            "climate": climate,
        },
        "landmarks": landmarks,
        "wildlife": wildlife,
        "plants": [],
        "activities": [],
        "history": [],
        "local_food": [],
        "weather": [],
        "interesting_facts": [],
        "_draft": {
            "wikidata": qid,
            "coordinates": [lat, lng],
            "needs_human": {
                "activities": "no API describes what a family does here — drives coloring scenes",
                "local_food": "no API at a child's register",
                "plants": "iNaturalist is biased to photographed species, not visible ones",
                "weather": "prose, not data",
                "profile.regions": "closed vocabulary in src/symbols/vocab.py — pick by hand",
                "profile.climate": (
                    "an annual mean, not a peak-visiting-season read — weigh against your "
                    "own sense of the place; see climate_from_open_meteo's docstring"
                ),
                "landmarks": "candidates only — check every one is child-appropriate",
            },
        },
    }
    if country_facts:
        pack["_draft"]["countries_json_row"] = {country_code: country_facts}

    report.append("")
    report.append("NOT FILLED (see _draft.needs_human in the pack)")
    for field, why in pack["_draft"]["needs_human"].items():
        report.append(f"  {field:<18} {why}")
    report.append("=" * 72)
    return pack, report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("destination", help="destination name, e.g. \"Pelion\"")
    parser.add_argument("--qid", help="skip search and use this Wikidata QID")
    parser.add_argument("--out", type=Path, help="write the draft pack here (default: stdout)")
    args = parser.parse_args(argv)

    pack, report = build(args.destination, args.qid, read_env())

    print("\n".join(report), file=sys.stderr)
    rendered = json.dumps(pack, ensure_ascii=False, indent=2)
    if args.out:
        args.out.write_text(rendered + "\n", encoding="utf-8")
        print(f"\ndraft written to {args.out}", file=sys.stderr)
    else:
        print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
