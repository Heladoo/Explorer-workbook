"""Simple Quiz: picture-based multiple choice about the destination.

The options are *drawn*, not written, so the page works for pre-readers and in
any language. The question text lives in the page metadata for the layout stage.
"""

from __future__ import annotations

from typing import Any

from src.activities.base import (
    ActivityGenerator,
    ImageBrief,
    PlannedPage,
    RenderMode,
    register_activity,
)
from src.models.context import WorkbookContext
from src.models.page import ActivityDraft

_QUESTION_COUNT = {"easy": 3, "medium": 4, "hard": 5}

#: Knowledge category -> (question string key, distractor pool key).
_QUESTION_SOURCES: tuple[tuple[str, str, str], ...] = (
    ("wildlife", "quiz.q_wildlife", "quiz.distractor_wildlife"),
    ("landmarks", "quiz.q_landmark", "quiz.distractor_landmark"),
    ("local_food", "quiz.q_food", "quiz.distractor_food"),
    ("activities", "quiz.q_activity", "quiz.distractor_activity"),
)


@register_activity
class QuizActivity(ActivityGenerator):
    """Checks what the child has picked up, using only pictures."""

    activity_type = "quiz"
    display_name = "Simple Quiz"
    educational_goal = (
        "Consolidates what the child has learned about the destination and "
        "practises choosing between plausible options."
    )
    min_age = 5
    max_age = 12
    weight = 12
    energy = "calm"

    def supports(self, context: WorkbookContext) -> bool:
        if not super().supports(context):
            return False
        return sum(1 for category, _, _ in _QUESTION_SOURCES if context.knowledge.get(category)) >= 2

    def generate(self, context: WorkbookContext, planned: PlannedPage) -> ActivityDraft:
        strings = self.strings(context)
        wanted = _QUESTION_COUNT[planned.difficulty]
        questions: list[dict[str, Any]] = []

        for category, question_key, distractor_key in _QUESTION_SOURCES:
            if len(questions) >= wanted:
                break
            answers = self.pick(context, category, 1)
            if not answers:
                continue
            answer = answers[0]
            distractors = self._distractors(context, strings.items(distractor_key), category, answer)
            if len(distractors) < 2:
                continue
            options = self._arrange(context, answer, distractors[:2], len(questions))
            questions.append(
                {
                    "question": self.text(context, question_key, destination=context.display_destination),
                    "options": options,
                    "answer": answer,
                    "answer_index": options.index(answer) + 1,
                    "category": category,
                }
            )

        # Not enough categories for the requested length: ask a second question
        # from the richest category rather than padding with invented content.
        for category, question_key, distractor_key in _QUESTION_SOURCES:
            if len(questions) >= wanted:
                break
            pool = context.knowledge.get(category)
            used = {question["answer"] for question in questions}
            remaining = [item for item in pool if item not in used]
            if not remaining:
                continue
            answer = remaining[0]
            distractors = self._distractors(context, strings.items(distractor_key), category, answer)
            if len(distractors) < 2:
                continue
            options = self._arrange(context, answer, distractors[:2], len(questions))
            questions.append(
                {
                    "question": self.text(context, question_key, destination=context.display_destination),
                    "options": options,
                    "answer": answer,
                    "answer_index": options.index(answer) + 1,
                    "category": category,
                }
            )

        option_lines = [
            f"Question {index + 1} options: " + ", ".join(question["options"])
            for index, question in enumerate(questions)
        ]

        return self.draft(
            title=self.text(context, "quiz.title", destination=context.display_destination),
            instructions=self.text(context, "quiz.instructions", count=len(questions)),
            planned=planned,
            image_brief=ImageBrief(
                subject=f"a picture quiz sheet with {len(questions)} questions",
                scene=(
                    f"A quiz page about {context.destination}. Each row offers three small "
                    "drawings to choose between, with an empty circle under each one."
                ),
                elements=tuple(
                    option for question in questions for option in question["options"]
                ),
                render_mode=RenderMode.PUZZLE,
                composition=(
                    f"{len(questions)} rows stacked down the page. Each row has a blank strip "
                    "at the top for the question, then three equally sized option drawings "
                    "side by side, each with an empty circle beneath it."
                ),
                extra_constraints=(
                    *option_lines,
                    "Leave the question strips completely blank — the text is added later.",
                    "Do not mark, tick or highlight the correct answer in any way.",
                ),
            ),
            metadata={"questions": questions, "question_count": len(questions)},
        )

    def _distractors(
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
