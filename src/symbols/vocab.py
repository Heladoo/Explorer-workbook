"""The closed vocabulary every symbol facet and destination profile draws from.

This is the part of the symbol library the code actually branches on — the
loader validates every tag in ``data/symbols/library.json`` (and, later,
every destination pack's ``profile`` block) against these tuples and raises
on anything it doesn't recognise. The 300 rows of content that use these tags
are data and live in JSON; the vocabulary is structure and lives in code, per
the same split the rest of the project already uses (``src/locales/*.py``,
``src/activities/_symbols.py``).
"""

from __future__ import annotations

#: The single browse/diversity axis. One per symbol, not a set — its job is
#: "no two of the same kind on one shadow-match page" (a boat beside a fish,
#: a taxi beside a police car, is a bad puzzle), which only works if a symbol
#: has exactly one topic to compare.
TOPICS = (
    "street",     # signs and road furniture
    "vehicles",   # things that carry people or goods
    "buildings",  # fixed structures
    "animals",
    "water",      # things on or in water
    "people",
    "food",
    "gear",       # things worn, carried or packed
    "nature",     # terrain, plants, weather
)

#: Findability tier. An easy scavenger hunt is built entirely from
#: ``everywhere`` symbols so a young child can finish it on any trip.
UBIQUITY = ("everywhere", "common", "regional", "local")

#: Where a symbol's subject actually occurs. The one facet allowed to *bar* a
#: symbol from a destination: a boat needs ``water``/``coast``, and a
#: destination with neither should never be offered one.
ENVIRONMENTS = (
    "city",
    "village",
    "street",
    "road",
    "coast",
    "water",
    "mountain",
    "forest",
    "desert",
    "farm",
    "snow",
)

#: Weather relevance — mostly used for what-to-pack signals, distinct from
#: ``environments`` (a mountain can be hot or snowy; the terrain doesn't say).
CLIMATES = ("hot", "cold", "wet", "dry", "temperate")

#: Activity capability. Multi-valued and usually is: most symbols are
#: findable (``spot``) and read clearly as a shadow (``shadow``); only some
#: are also things you'd actually pack (``pack``). ``decor`` marks artwork
#: fit for future page decoration (borders, headers) rather than any puzzle
#: page — not consumed by any activity yet, just a forward-looking tag.
ROLES = ("spot", "pack", "shadow", "decor")

#: Whether artwork is committed. Authored by whoever adds the entry, not
#: scanned from disk at runtime — see the "authored, not derived" note in the
#: symbol library's own docstring for why.
STATUS = ("ready", "draft")

#: Geographic affinity, most symbols have none. Kept flat and non-hierarchical
#: on purpose: ancestry (``greece`` belongs to ``mediterranean`` belongs to
#: ``europe``) lives on the destination profile side instead, since there are
#: only a handful of destinations to enrich against many more symbols.
REGIONS = (
    "greece",
    "mediterranean",
    "europe",
    "israel",
    "middle-east",
    "usa",
    "north-america",
)

#: Keys some module names by hand rather than sampling (``maze.py``'s start
#: icon, its plain-flag fallback). Removing one from the library must fail a
#: test, not crash a book at generation time.
REQUIRED_KEYS = ("airplane", "flag")
