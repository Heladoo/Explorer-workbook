"""The spottable-symbol bank behind the scavenger hunt.

A scavenger hunt fails in two ways when it is built only from destination
knowledge: the items are too rare to actually find ("the Bedouin hospitality
tent" appears once, if at all), and asking one image model call to draw a
labelled grid of twelve specific things reliably produces the wrong count, the
wrong items and stray text.

So the hunt is built from two pools:

``UNIVERSAL_SYMBOLS``
    Things a child can find almost anywhere in the world — a stop sign, a
    bridge, a police car. These carry the page: they are findable on any trip,
    in any country, on the way to anywhere.
``destination_symbols()``
    A few real, generic things from the destination's own knowledge ("camels",
    not "camels grazing near the Nokdim valley lookout"), so the hunt is still
    about *this* trip without turning into a landmark checklist — a place
    name isn't something a young child spots and recognises the way an animal
    or a food is, so those are left out entirely.

Each symbol is drawn **on its own**, from its own small prompt, and the print
layout typesets the table around it. A one-subject prompt ("a single stop sign,
centred, thick black outline") is the kind an image model gets right every
time.

Because a universal symbol's prompt mentions no destination, style signature or
characters, its drawing is identical in every book — so ``key`` doubles as a
cache key and the same stop sign can be generated once and reused forever.

The bank itself — including symbols with no cached artwork yet, and the
facets a future relevance score will read (topic, ubiquity, environments,
regions, ...) — lives in ``data/symbols/library.json``, loaded via
``src/symbols``. ``UNIVERSAL_SYMBOLS`` below is that library's
always-findable, artwork-ready pool: what used to be hand-maintained here as
a tuple of commented/uncommented literals is now `Library.universal_pool()`,
so a symbol joins this pool by editing its `status`/`ubiquity` in the library
file, not by uncommenting a line.

Leading underscore keeps this module out of the activity auto-discovery scan.
"""

from __future__ import annotations

import re

from src.activities._wordbank import _HEBREW_PROCLITICS
from src.models.context import WorkbookContext, slugify
from src.symbol_art import CUTOUTS, find_variant
from src.symbols import Symbol, library

#: Knowledge categories that name a real, spottable *thing* rather than a fact
#: or a place. ``landmarks`` is deliberately excluded — a landmark is a place
#: name by definition ("the Masada cliff fortress"), and a symbol here has to
#: read as a short, generic topic ("camels") the way the universal pool does.
SPOTTABLE_CATEGORIES = ("wildlife", "plants", "local_food")

#: The pool the hunt and the matching page have always drawn from: library
#: entries with committed artwork that are findable almost anywhere.
#: Deliberately not every ``ready`` entry — a ``local``/``regional`` symbol
#: like souvlaki has artwork but is findable-in-Greece, not
#: findable-anywhere, and belongs to destination matching, not this backbone.
UNIVERSAL_SYMBOLS: tuple[Symbol, ...] = library().universal_pool()

#: Grid width in cells. Fixed rather than derived from the item count so every
#: sheet reads as the same shape; row count is what varies with difficulty.
GRID_COLUMNS = 4

#: How many things go on the sheet, and how many of them come from the
#: destination rather than the universal pool. Every difficulty is a fixed
#: 4x4 = 16 cells — small enough that a 4-year-old can still finish it, and
#: the one grid shape the print layout's checkbox/label furniture is tuned
#: for. Difficulty only changes how many of the 16 come from the destination
#: rather than the always-findable universal pool; it used to also grow the
#: sheet to 20 (4x5) for medium/hard, which the print layout was never
#: actually verified against — see test_no_page_overflows_its_sheet.
_PLAN = {
    "easy": (16, 0),
    "medium": (16, 6),
    "hard": (16, 10),
}


def hunt_size(difficulty: str) -> tuple[int, int]:
    """``(total items, how many come from the destination)`` for a difficulty."""
    return _PLAN.get(difficulty, _PLAN["medium"])


def grid_dimensions(total: int) -> tuple[int, int]:
    """``(columns, rows)`` for laying ``total`` cells out on one A4 page."""
    columns = GRID_COLUMNS
    rows = -(-total // columns)  # ceiling division
    return columns, rows


def destination_symbols(context: WorkbookContext) -> tuple[Symbol, ...]:
    """Real, general things from the destination's knowledge, as drawable symbols.

    The key is slugified from the **English** term, not the localized label, so
    a Hebrew book and an English book share one cache entry per sight — and so
    a Hebrew phrase, which slugifies to nothing, still gets a usable key.
    Entries with no English form to slugify are dropped rather than given an
    unstable key.

    Both the label and the subject are shortened to a short general topic —
    "dolphins", not "dolphins off the Pagasetic Gulf" — by ``_topic()``: a
    knowledge phrase is a sentence fragment written for prose ("sweet tea with
    na'ana mint"), not a checklist word, and the full phrase is both too long
    for a grid label and drags location detail into what should be a generic,
    findable-anywhere-similar thing into an image prompt.

    A phrase whose topic slugifies to an existing ``ready`` library key, or
    stem-matches one of its ``aliases`` (see ``_match_alias`` — "chestnut
    forests" and "chestnuts roasted" both carry the root "chestnut" and both
    resolve onto the ``chestnuts`` entry, however a destination pack happens
    to phrase it), reuses that library ``Symbol`` outright — its own
    committed artwork, its own facets, and ``symbol.<key>`` for the
    reader-facing label — instead of minting a fresh, artwork-less one that
    can only ever print as a placeholder. A ``draft`` entry is never matched:
    it has no artwork either, so matching it would trade a specific
    destination phrase for a more generic label and gain nothing. Because
    resolution is by *key*, two differently-phrased sightings of the same
    thing ("chestnut forests" from ``plants``, "chestnuts roasted" from
    ``local_food``) collapse onto one entry via the ``seen`` check below
    instead of printing the same subject twice under two different names.
    """
    english_terms = context.knowledge.english_terms
    lib = library()
    ready_symbols = tuple(
        symbol
        for symbol in lib.all()
        if symbol.facets is not None and symbol.facets.status == "ready"
    )
    candidates: list[Symbol] = []
    seen: set[str] = set()
    for category in SPOTTABLE_CATEGORIES:
        for phrase in context.knowledge.get(category) or ():
            english = english_terms.get(phrase, phrase)
            # ``slugify`` falls back to the literal "destination" for a string
            # with no ASCII letters, so guard on the source text: without that
            # check every untranslated Hebrew entry would collapse onto one key
            # and silently share one wrong drawing.
            if not _LATIN.search(english):
                continue
            topic = _topic(english)
            key = slugify(topic)

            library_symbol = lib[key] if key in lib else None
            if library_symbol is None or library_symbol.facets.status != "ready":
                library_symbol = _match_alias(topic, ready_symbols)

            resolved = library_symbol or Symbol(key=key, label=_topic(phrase), subject=topic)
            if resolved.key in seen:
                continue
            seen.add(resolved.key)
            candidates.append(resolved)

    # A library match (``facets is not None``) is guaranteed a cutout — see
    # ``tests/test_symbol_art.py::test_every_ready_symbol_has_every_variant``
    # — but a symbol minted fresh above, from a phrase with no library match
    # at all, has no committed artwork by construction: it would print
    # anywhere it's used as a raw English slug instead of a picture (see the
    # regression this guards, a maze goal marker reading
    # "cobblestone-kalderimi-paths-flag"). Check the whole batch's cutouts in
    # one directory scan and drop anything still missing — the caller
    # (``scavenger_hunt.py``) already tops up an under-supplied local pool
    # from the universal bank, so a dropped entry here just means one more
    # symbol comes from there instead.
    unmatched_keys = tuple(symbol.key for symbol in candidates if symbol.facets is None)
    has_art = find_variant(unmatched_keys, CUTOUTS) if unmatched_keys else {}
    return tuple(
        symbol for symbol in candidates if symbol.facets is not None or symbol.key in has_art
    )


def _match_alias(topic: str, candidates: tuple[Symbol, ...]) -> Symbol | None:
    """Whether ``topic`` names the same thing as one of ``candidates``' aliases.

    A single-word alias ("chestnut") matches by shared word stem, so it
    catches any phrasing that carries that root ("chestnuts roasted",
    "chestnut forests") instead of needing one alias hand-written per wording
    a destination pack happens to use. A multi-word alias ("fresh fish",
    "wild tortoises") still has to appear as that whole phrase — stemming a
    short single word like "hill" is useful, but stemming one word out of a
    multi-word alias would match almost anything.
    """
    topic_lower = topic.lower()
    topic_words = re.findall(r"[a-z']+", topic_lower)
    for symbol in candidates:
        for alias in symbol.facets.aliases:
            alias_lower = alias.lower()
            if " " in alias_lower:
                if alias_lower in topic_lower:
                    return symbol
            elif any(
                word == alias_lower or word.startswith(alias_lower) for word in topic_words
            ):
                return symbol
    return None


#: A term needs at least one Latin letter to produce a meaningful slug.
_LATIN = re.compile(r"[A-Za-z]")

#: Leading words that add nothing to a topic ("the date palm grove" -> "date
#: palm grove"). Comparison is case-insensitive; only English is handled here
#: — a non-English phrase simply falls through to the word-count cap below.
_LEADING_ARTICLES = ("the", "a", "an")

#: Words that must never end a topic — capping at 3 words can land mid-phrase
#: ("goats grazing the hillsides" -> "goats grazing the"), so these are
#: stripped from the *end* after capping, same as the leading article is
#: stripped from the front.
_TRAILING_STOPWORDS = ("the", "a", "an", "and", "or", "of", "with", "in", "on", "by")

#: A knowledge phrase is prose, not a checklist word, and everything from the
#: first of these connectors onward is scene-setting detail rather than the
#: thing itself: "fresh pita from the saj" -> "fresh pita", "dolphins off the
#: Pagasetic Gulf" -> "dolphins". Checked as whole words only.
_CONNECTORS = re.compile(
    r"\b(?:of|from|with|off|in|at|near|after|before|during|on|over|under|"
    r"through|around|without|beside|among|by|along|across|towards?)\b",
    re.IGNORECASE,
)

#: However short a phrase already is, a symbol title is at most this many words.
MAX_TOPIC_WORDS = 3


def _ends_on_a_dangling_hebrew_prefix(word: str) -> bool:
    """Whether ``word`` looks like a Hebrew preposition/conjunction/article
    stranded at the end of a phrase this function itself just shortened.

    Hebrew attaches a one-letter proclitic directly to the word it governs,
    with no space (see ``_wordbank._HEBREW_PROCLITICS`` for the full
    rationale — the exact same letters, the exact same reason). A phrase
    capped at ``MAX_TOPIC_WORDS`` words can land squarely on one of these:
    "מפירות" ("from fruits") drops the "local" the phrase needed, "בעצי"
    ("in the trees of") is itself an unfinished construct-state noun with no
    object at all. There is no safe way to tell which — only English's
    ``_CONNECTORS``/``_TRAILING_STOPWORDS`` above are actually parsed — so
    the same word is never *cut down*, only dropped wholesale, same
    principle as the puzzle-word picker in ``_wordbank.py``.
    """
    return bool(word) and word[0] in _HEBREW_PROCLITICS and _LATIN.search(word) is None


def _topic(phrase: str) -> str:
    """Shorten a knowledge phrase to a short, general topic, max 3 words.

    Cuts at the first prepositional connector (the usual source of place names
    and other scene detail in a knowledge phrase), then caps the word count —
    so this also holds for phrases with no connector at all ("Nubian ibex
    grazing near the wadi" -> "Nubian ibex").
    """
    connector = _CONNECTORS.search(phrase)
    text = phrase[: connector.start()] if connector else phrase
    words = text.split()
    if words and words[0].lower() in _LEADING_ARTICLES:
        words = words[1:]
    truncated = len(words) > MAX_TOPIC_WORDS
    words = words[:MAX_TOPIC_WORDS]
    # The word-count cap can itself land mid-phrase, on a connector or
    # article the earlier cut didn't reach — drop those too, but never below
    # one word. Only English is parsed here; a non-English phrase simply
    # never matches _TRAILING_STOPWORDS and falls through untouched.
    while len(words) > 1 and words[-1].lower() in _TRAILING_STOPWORDS:
        words = words[:-1]
    # Same idea, for a phrase the word-count cap above genuinely shortened —
    # a phrase that was already this short and happens to end this way is
    # simply how the sentence reads, not a truncation artifact, so this only
    # fires once, on the exact word the cap landed on.
    if truncated and len(words) > 1 and _ends_on_a_dangling_hebrew_prefix(words[-1]):
        words = words[:-1]
    return " ".join(words).strip() or phrase.strip()
