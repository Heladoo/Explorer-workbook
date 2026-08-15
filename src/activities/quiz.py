"""Simple Quiz: a short set of basic-fact questions about the destination's
country, written and read as text.

Three text options per question, marked with a lettered bubble to circle.
This is a *reading* task — unlike the rest of the workbook, it does not work
for a pre-reader, which is why ``min_age`` is higher here than on any other
activity (see the class attribute below).

Two families of question:

- **Country facts** — capital city, flag colours, spoken language, continent,
  currency — resolved from ``data/countries.json`` via ``src.countries``, and
  only available when the destination's pack names a ``country``. Distractors
  are real facts about *other* countries, so a wrong answer is never make-believe.
- **Knowledge facts** — wildlife and local food the destination genuinely has
  (with landmarks and activities as a demoted fallback), exactly as before.
  Distractors are a deliberately silly locale-defined pool
  (``quiz.distractor_*``), guarded so nothing in it can accidentally match
  something true here.

A destination with no curated country falls straight through to the
knowledge questions and still gets a full quiz — the country facts are a
bonus when available, never a requirement.

The page's working area also carries a short local-language dictionary (see
``src/phrasebook.py``); that lives in this same activity because both halves
of the page — "what do you know", "what will you say" — are about getting
ready for the same trip, and the page has room for one A4 sheet's worth of
either alone or both together.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Callable

from src.activities._symbols import _topic
from src.activities.base import (
    ActivityGenerator,
    PlannedPage,
    register_activity,
)
from src import fonts
from src.countries import COLOURS, CountryFacts, countries, country_for
from src.models.context import WorkbookContext
from src.models.page import ActivityDraft
from src.phrasebook import phrasebook_for
from src.strings import Strings

logger = logging.getLogger(__name__)

QUESTION_COUNT = 3

#: (kind == knowledge category, question string key, distractor pool key).
#: Wildlife and local food lead; landmarks and activities are demoted —
#: kept only as fallback fuel for a destination with a thin knowledge set
#: and no curated country, so a book still reaches QUESTION_COUNT.
_KNOWLEDGE_SOURCES: tuple[tuple[str, str, str], ...] = (
    ("wildlife", "quiz.q_wildlife", "quiz.distractor_wildlife"),
    ("local_food", "quiz.q_food", "quiz.distractor_food"),
    ("landmarks", "quiz.q_landmark", "quiz.distractor_landmark"),
    ("activities", "quiz.q_activity", "quiz.distractor_activity"),
)


@dataclass(frozen=True)
class _Draft:
    """One candidate question before slot arrangement."""

    kind: str
    question: str
    answer: str
    distractors: tuple[str, ...]  # always >= 2, already display text
    category: str = ""  # a KNOWLEDGE_FIELDS name, "" for a country-fact question


@register_activity
class QuizActivity(ActivityGenerator):
    """A short, honest quiz: real facts, written down, three choices each."""

    activity_type = "quiz"
    display_name = "Simple Quiz"
    educational_goal = (
        "Checks what the child has picked up about the destination and its "
        "country, and practises reading three short options and choosing "
        "between them."
    )
    # Higher than every other activity's min_age: this is the one page in the
    # workbook that is a genuine reading task rather than a look-and-point
    # one, so it does not belong in a book for a pre-reader.
    min_age = 7
    max_age = 12
    weight = 12
    energy = "calm"

    def supports(self, context: WorkbookContext) -> bool:
        if not super().supports(context):
            return False
        strings = self.strings(context)
        facts = country_for(context.knowledge.country)
        available = sum(
            1 for draft in self._all_drafts(context, strings, facts, limit=None) if draft
        )
        return available >= QUESTION_COUNT

    def generate(self, context: WorkbookContext, planned: PlannedPage) -> ActivityDraft:
        strings = self.strings(context)
        facts = country_for(context.knowledge.country)
        questions_raw = self._all_drafts(context, strings, facts, limit=QUESTION_COUNT)

        questions: list[dict[str, Any]] = []
        for index, draft in enumerate(questions_raw):
            options = self._arrange(context, draft.answer, list(draft.distractors[:2]), index)
            questions.append(
                {
                    "question": draft.question,
                    "options": options,
                    "answer": draft.answer,
                    "answer_index": options.index(draft.answer) + 1,
                    "category": draft.category,
                    "kind": draft.kind,
                }
            )

        return self.draft(
            title=self.text(context, "quiz.title", destination=context.display_destination),
            instructions=self.text(context, "quiz.instructions", count=len(questions)),
            planned=planned,
            metadata={
                "questions": questions,
                "question_count": len(questions),
                "needs_illustration": False,
                **self._dictionary_metadata(context, strings, facts),
            },
        )

    # -- the local-language dictionary --------------------------------------

    def _dictionary_metadata(
        self, context: WorkbookContext, strings: Strings, facts: CountryFacts | None
    ) -> dict[str, Any]:
        """The page's dictionary section, or ``{}`` when there isn't one.

        Omitted — never printed half-filled or broken — when: the
        destination has no country or spoken language; that language is the
        workbook's own (a Hebrew book about an Israeli destination needs no
        Hebrew dictionary); nobody has curated a phrasebook for it; that
        phrasebook has no pronunciation for this workbook's language; or
        this repository has no embedded font for its script, in which case
        printing it would fall back to a system font or tofu boxes on
        whatever machine renders the book (see ``src/fonts.py``).
        """
        if facts is None or not facts.primary_language:
            return {}
        workbook_base = (context.language or "en").split("-")[0].lower()
        if facts.primary_language == workbook_base:
            return {}
        book = phrasebook_for(facts.primary_language, workbook_language=context.language)
        if book is None:
            return {}
        if not fonts.covers_script(book.script):
            logger.warning(
                "phrasebook for %r uses script %r, which has no embedded font; "
                "omitting the dictionary section.",
                facts.primary_language,
                book.script,
            )
            return {}
        entries = [
            {
                "concept": phrase.concept,
                "meaning": strings.text(f"phrasebook.concept.{phrase.concept}"),
                "native": phrase.native,
                "pronunciation": phrase.pronunciation,
            }
            for phrase in book.phrases
        ]
        return {
            "dictionary": entries,
            "native_language": book.language,
            "native_direction": book.direction,
            "script": book.script,
        }

    # -- assembling the question set --------------------------------------

    def _all_drafts(
        self,
        context: WorkbookContext,
        strings: Strings,
        facts: CountryFacts | None,
        *,
        limit: int | None,
    ) -> list[_Draft]:
        """Every question this destination can ask, in priority order,
        stopping once ``limit`` real drafts are collected (``None`` collects
        everything, used by :meth:`supports` to just count what's available).
        """
        drafts: list[_Draft] = []

        def take(candidate: _Draft | None) -> bool:
            if candidate is None:
                return False
            drafts.append(candidate)
            return limit is not None and len(drafts) >= limit

        # Capital and flag lead when there is a country: the two questions
        # most parents would expect a "basic facts" quiz to open with.
        for builder in (self._q_capital, self._q_flag):
            if take(builder(context, strings, facts)):
                return drafts

        # The rest — remaining country facts plus the knowledge categories —
        # in an order shuffled per book, so the third question varies
        # between books but is reproducible for a given seed.
        rest: list[Callable[[], _Draft | None]] = [
            lambda: self._q_language(context, strings, facts),
            lambda: self._q_continent(context, strings, facts),
            lambda: self._q_currency(context, strings, facts),
        ]
        used_answers: set[str] = set()
        for category, question_key, distractor_key in _KNOWLEDGE_SOURCES:
            rest.append(
                lambda category=category, question_key=question_key, distractor_key=distractor_key: (
                    self._q_knowledge(context, strings, category, question_key, distractor_key, used_answers)
                )
            )
        context.rng_for("quiz:builders").shuffle(rest)

        for builder in rest:
            draft = builder()
            if draft is not None:
                used_answers.add(draft.answer)
            if take(draft):
                return drafts

        # Still short: ask each knowledge category for a *second*, still-unused
        # answer, in the same fixed order as _KNOWLEDGE_SOURCES — reaching
        # QUESTION_COUNT for a destination with no country and a thin pool is
        # more important here than any further shuffling.
        for category, question_key, distractor_key in _KNOWLEDGE_SOURCES:
            draft = self._q_knowledge(context, strings, category, question_key, distractor_key, used_answers)
            if draft is not None:
                used_answers.add(draft.answer)
            if take(draft):
                return drafts

        return drafts

    # -- country-fact question builders ------------------------------------

    def _q_capital(
        self, context: WorkbookContext, strings: Strings, facts: CountryFacts | None
    ) -> _Draft | None:
        if facts is None:
            return None
        others = [
            c for c in countries().values() if c.code != facts.code and c.capital != facts.capital
        ]
        if len(others) < 2:
            return None
        # Prefer a different continent so the options aren't two plausible
        # neighbours — fall back to whatever's available if the library is
        # too thin in other continents for this one.
        pool = [c for c in others if c.continent != facts.continent]
        if len(pool) < 2:
            pool = others
        picks = context.rng_for("quiz:capital").sample(pool, 2)
        return _Draft(
            kind="capital",
            question=strings.text("quiz.q_capital", country=_country_name(strings, facts)),
            answer=_place(strings, facts.capital),
            distractors=tuple(_place(strings, c.capital) for c in picks),
        )

    def _q_flag(
        self, context: WorkbookContext, strings: Strings, facts: CountryFacts | None
    ) -> _Draft | None:
        if facts is None:
            return None
        true_set = frozenset(facts.flag_colours)
        size = len(facts.flag_colours)
        rng = context.rng_for("quiz:flag")
        seen_answers = {_flag_text(strings, facts.flag_colours)}
        candidates: list[str] = []
        for _ in range(20):
            if len(candidates) >= 2:
                break
            sample = tuple(rng.sample(COLOURS, min(size, len(COLOURS))))
            if frozenset(sample) == true_set:
                continue
            text = _flag_text(strings, sample)
            if text in seen_answers:
                continue
            seen_answers.add(text)
            candidates.append(text)
        if len(candidates) < 2:
            return None
        return _Draft(
            kind="flag",
            question=strings.text("quiz.q_flag", country=_country_name(strings, facts)),
            answer=_flag_text(strings, facts.flag_colours),
            distractors=tuple(candidates),
        )

    def _q_language(
        self, context: WorkbookContext, strings: Strings, facts: CountryFacts | None
    ) -> _Draft | None:
        if facts is None or not facts.primary_language:
            return None
        pool = sorted(
            {
                c.primary_language
                for c in countries().values()
                if c.primary_language and c.primary_language != facts.primary_language
            }
        )
        if len(pool) < 2:
            return None
        picks = context.rng_for("quiz:language").sample(pool, 2)
        return _Draft(
            kind="language",
            question=strings.text("quiz.q_language", country=_country_name(strings, facts)),
            answer=_language_name(strings, facts.primary_language),
            distractors=tuple(_language_name(strings, code) for code in picks),
        )

    def _q_continent(
        self, context: WorkbookContext, strings: Strings, facts: CountryFacts | None
    ) -> _Draft | None:
        if facts is None:
            return None
        pool = sorted({c.continent for c in countries().values() if c.continent != facts.continent})
        if len(pool) < 2:
            return None
        picks = context.rng_for("quiz:continent").sample(pool, 2)
        return _Draft(
            kind="continent",
            question=strings.text("quiz.q_continent", country=_country_name(strings, facts)),
            answer=_continent_name(strings, facts.continent),
            distractors=tuple(_continent_name(strings, token) for token in picks),
        )

    def _q_currency(
        self, context: WorkbookContext, strings: Strings, facts: CountryFacts | None
    ) -> _Draft | None:
        if facts is None:
            return None
        pool = sorted({c.currency for c in countries().values() if c.currency != facts.currency})
        if len(pool) < 2:
            return None
        picks = context.rng_for("quiz:currency").sample(pool, 2)
        return _Draft(
            kind="currency",
            question=strings.text("quiz.q_currency", country=_country_name(strings, facts)),
            answer=_currency_name(strings, facts.currency),
            distractors=tuple(_currency_name(strings, token) for token in picks),
        )

    # -- knowledge question builder (wildlife / food / landmarks / activities) --

    def _q_knowledge(
        self,
        context: WorkbookContext,
        strings: Strings,
        category: str,
        question_key: str,
        distractor_key: str,
        used_answers: set[str],
    ) -> _Draft | None:
        pool = context.knowledge.get(category)
        if not pool:
            return None
        # First choice is a deterministic sample; if that one's answer (after
        # shortening) collides with something already used this quiz, fall
        # through the remaining pool in its original order.
        sampled = self.pick(context, category, 1, salt=len(used_answers))
        candidates = list(sampled) + [item for item in pool if item not in sampled]
        answer = None
        for raw in candidates:
            shortened = _topic(raw)
            if shortened not in used_answers:
                answer = shortened
                break
        if answer is None:
            return None

        distractor_pool = strings.items(distractor_key)
        distractors = self._knowledge_distractors(context, distractor_pool, category, answer)
        if len(distractors) < 2:
            return None
        return _Draft(
            kind=category,
            question=self.text(context, question_key, destination=context.display_destination),
            answer=answer,
            distractors=tuple(distractors[:2]),
            category=category,
        )

    def _knowledge_distractors(
        self,
        context: WorkbookContext,
        pool: tuple[str, ...],
        category: str,
        answer: str,
    ) -> list[str]:
        """Pick wrong-but-fun options that are definitely not true here."""
        local = {value.lower() for value in context.knowledge.get(category)}
        candidates = [
            item
            for item in pool
            if item.lower() != answer.lower()
            and not any(item.lower() in value or value in item.lower() for value in local)
        ]
        rng = context.rng_for(f"quiz:distractors:{category}")
        rng.shuffle(candidates)
        return candidates

    # -- shared option arrangement ------------------------------------------

    def _arrange(
        self,
        context: WorkbookContext,
        answer: str,
        distractors: list[str],
        question_index: int,
    ) -> list[str]:
        """Place the answer in a rotating slot so it is never always first."""
        options = list(distractors)
        offset = context.rng_for("quiz:offset").randrange(3)
        options.insert((question_index + offset) % (len(options) + 1), answer)
        return options


# -- display-text helpers, shared by every country-fact builder ------------


def _place(strings: Strings, token: str) -> str:
    return strings.optional(f"place.{token}", token.replace("_", " ").title())


def _country_name(strings: Strings, facts: CountryFacts) -> str:
    return strings.optional(f"country.{facts.name}", facts.name.replace("_", " ").title())


def _continent_name(strings: Strings, token: str) -> str:
    return strings.optional(f"continent.{token}", token.replace("_", " ").title())


def _currency_name(strings: Strings, token: str) -> str:
    return strings.optional(f"currency.{token}", f"the {token.upper()}")


def _language_name(strings: Strings, code: str) -> str:
    return strings.optional(f"language.{code}", code.upper())


def _colour_name(strings: Strings, token: str) -> str:
    return strings.optional(f"colour.{token}", token.title())


def _flag_text(strings: Strings, colours: tuple[str, ...]) -> str:
    return strings.join([_colour_name(strings, colour) for colour in colours])
