"""Turning knowledge phrases into puzzle-able words.

Knowledge entries are readable phrases ("the big Bedouin hospitality tent"),
but a word search or crossword needs a single clean token (TENT). This module
does that extraction once so both puzzle activities agree on it.

Leading underscore keeps it out of the activity auto-discovery scan.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

from src.models.context import WorkbookContext

#: Words that carry no meaning as a puzzle answer.
STOPWORDS = frozenset(
    {
        "the", "a", "an", "of", "at", "in", "on", "to", "and", "or", "with",
        "from", "for", "your", "you", "its", "it", "this", "that", "these",
        "some", "one", "two", "big", "small", "little", "old", "new", "local",
        "fresh", "sweet", "great", "just", "very", "up", "down", "near",
        "nearby", "over", "under", "into", "along", "around", "here", "there",
        "where", "when", "what", "who", "can", "you", "see", "go", "made",
        # Filler that would otherwise show up in every destination's puzzle.
        "trip", "ride", "tour", "visit", "thing", "things", "place", "places",
    }
)

#: Categories worth mining for puzzle words, in preference order. Deliberately
#: excludes ``landmarks`` — a landmark is a place name by definition, and a
#: proper noun in a foreign script or spelling is exactly the kind of word a
#: child can't be expected to already know how to find, unlike an everyday
#: noun like "boats" or "chestnuts" (see ``_symbols.py``'s
#: ``SPOTTABLE_CATEGORIES`` for the same exclusion, for the same reason).
PUZZLE_CATEGORIES = ("wildlife", "plants", "local_food", "activities")


@dataclass(frozen=True)
class WordEntry:
    """One puzzle answer plus the phrase it came from."""

    word: str
    source: str
    category: str

    def blanked_source(self) -> str:
        """The source phrase with the answer replaced by a blank.

        ``"the big Bedouin hospitality tent"`` → ``"The big Bedouin hospitality ___"``
        This makes a natural crossword clue at zero cost.
        """
        pattern = re.compile(rf"\b{re.escape(self.word)}\w*\b", re.IGNORECASE)
        blanked, count = pattern.subn("___", self.source, count=1)
        if not count:
            return ""
        blanked = " ".join(blanked.split()).strip()
        return blanked[:1].upper() + blanked[1:] if blanked else ""


def normalize(text: str) -> str:
    """Strip everything that is not a letter, folding accents but keeping script.

    Decomposing and dropping combining marks turns "Český" into "CESKY" while
    leaving Hebrew intact (niqqud are combining marks, so they drop out and the
    consonants remain) — a word search works in any alphabet.
    """
    decomposed = unicodedata.normalize("NFKD", text)
    letters = [
        character
        for character in decomposed
        if character.isalpha() and not unicodedata.combining(character)
    ]
    return "".join(letters).upper()


#: Hebrew attaches a one-letter preposition/conjunction/article directly to
#: the word that follows, with no space — ``בסירות`` ("in boats") is ``ב``
#: ("in") plus ``סירות`` ("boats"). English's equivalent function words are
#: their own tokens and so are already caught by STOPWORDS above; Hebrew's
#: never are, which used to let a phrase like "watching fishing boats come
#: into a harbour" print "בסירות" as the puzzle answer instead of "סירות" —
#: not a word on its own. There's no safe way to *cut* the letter off
#: (a real word can start with any of these too — ``מפרץ`` "gulf",
#: ``מקומי`` "local" — and mis-cutting prints a fragment that isn't a word
#: at all), so a token that might carry one is only used when the phrase
#: offers nothing better; picking a different real word from the same
#: phrase is always safe, guessing where to cut one is not.
_HEBREW_PROCLITICS = "ובכלמשה"


def _maybe_prefixed(word: str, *, min_length: int) -> bool:
    return (
        len(word) > 1
        and word[0] in _HEBREW_PROCLITICS
        and len(word) - 1 >= min_length
    )


def puzzle_word(phrase: str, *, min_length: int = 3, max_length: int = 10) -> str | None:
    """Pick the most distinctive word in a phrase, or ``None`` if there isn't one.

    Longest wins, because length correlates with specificity ("hospitality"
    over "tent"). Equal lengths go to the earlier token, which in an English
    noun phrase is the modifier that distinguishes it — "boat" trip, "camel"
    yard — while the head noun is often the generic half.
    """
    candidates = []
    for token in phrase.split():
        word = normalize(token)
        if not word or word.lower() in STOPWORDS:
            continue
        if min_length <= len(word) <= max_length:
            candidates.append(word)
    if not candidates:
        return None
    unprefixed = [w for w in candidates if not _maybe_prefixed(w, min_length=min_length)]
    # If *every* candidate is proclitic-prefixed, there is no safe word left
    # to cut off the prefix from (see the module docstring above) — admit
    # defeat rather than settle for a fragment. build_word_bank() already
    # round-robins across categories/phrases and accepts fewer than `count`
    # words if the pool runs out, so a `None` here just means it moves on to
    # a cleaner word from a different phrase instead.
    if not unprefixed:
        return None
    return max(unprefixed, key=lambda word: (len(word), -unprefixed.index(word)))


def build_word_bank(
    context: WorkbookContext,
    *,
    count: int,
    key: str,
    categories: tuple[str, ...] = PUZZLE_CATEGORIES,
    min_length: int = 3,
    max_length: int = 10,
) -> tuple[WordEntry, ...]:
    """Collect up to ``count`` distinct puzzle words from the destination knowledge.

    Draws round-robin across categories so a puzzle mixes animals, places and
    food rather than emptying one category first.
    """
    per_category: dict[str, list[WordEntry]] = {}
    for category in categories:
        entries: list[WordEntry] = []
        for phrase in context.knowledge.get(category):
            word = puzzle_word(phrase, min_length=min_length, max_length=max_length)
            if word:
                entries.append(WordEntry(word=word, source=phrase, category=category))
        if entries:
            per_category[category] = entries

    if not per_category:
        return ()

    rng = context.rng_for(f"wordbank:{key}")
    for entries in per_category.values():
        rng.shuffle(entries)

    collected: list[WordEntry] = []
    seen: set[str] = set()
    exhausted = False
    while len(collected) < count and not exhausted:
        exhausted = True
        for category in categories:
            entries = per_category.get(category)
            if not entries:
                continue
            exhausted = False
            entry = entries.pop(0)
            # Reject near-duplicates as well as exact ones: CAMEL and CAMELS in
            # the same puzzle read as a mistake, and in a word search the child
            # can circle one inside the other.
            if any(
                entry.word in chosen or chosen in entry.word for chosen in seen
            ):
                continue
            seen.add(entry.word)
            collected.append(entry)
            if len(collected) >= count:
                break
    return tuple(collected)
