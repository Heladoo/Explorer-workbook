"""English copy for the workbook pages.

Keys are namespaced by activity type. Values are either text with ``{}``
placeholders or lists used as content pools.
"""

LANGUAGE = "en"

STRINGS: dict[str, object] = {
    # -- shared -------------------------------------------------------
    "common.and": "and",
    "common.explorer": "the explorer",
    "common.kind_animal": "animal",
    "common.kind_place": "place",
    "common.this_place": "this place",
    # -- workbook framing ---------------------------------------------
    "workbook.title_with_names": "{names}'s {destination} Adventure Book",
    "workbook.title_plain": "The {destination} Explorer Workbook",
    "workbook.subtitle": "An activity book for young explorers",
    # -- cover ---------------------------------------------------------
    "cover.title_with_names": "{names}'s Big Trip to {destination}",
    "cover.title_plain": "Welcome to {destination}",
    "cover.instructions_with_names": (
        "This adventure book belongs to {names}. Write your name on the line, "
        "color the cover, and get ready to explore {destination}!"
    ),
    "cover.instructions_plain": (
        "Write your name on the line, color the cover, and get ready to "
        "explore {destination}!"
    ),
    # -- coloring ------------------------------------------------------
    "coloring.title": "Color {subject}",
    "coloring.instructions": (
        "Color this picture of {subject}. Look closely for {extras} — you may "
        "see them for real on your trip!"
    ),
    "coloring.instructions_plain": (
        "Color this picture of {subject}. Use any colors you like, then show "
        "someone what you made."
    ),
    # -- maze ----------------------------------------------------------
    "maze.title": "The Path to {goal}",
    "maze.instructions": (
        "Help {hero} get from {start} all the way to {goal}. Draw one line "
        "through the maze without crossing any walls."
    ),
    "maze.collect": "Pick up {items} along the way.",
    # -- spot the difference -------------------------------------------
    "spot_difference.title": "Spot the Differences",
    "spot_difference.instructions": (
        "These two pictures of {subject} look the same — but {count} things "
        "are different. Circle every difference you find."
    ),
    "spot_difference.change_missing": "{item} is missing from the second picture",
    "spot_difference.change_extra": "an extra {item} appears in the second picture",
    "spot_difference.change_moved": "{item} has moved to the other side",
    "spot_difference.change_resized": "{item} is a different size",
    # -- hidden objects -------------------------------------------------
    "hidden_objects.title": "Find the Hidden Things",
    "hidden_objects.instructions": (
        "{count} things are hiding in this picture of {subject}: {items}. "
        "Circle each one as you find it."
    ),
    # -- packing --------------------------------------------------------
    "packing.title": "Pack Your Explorer Bag",
    "packing.instructions": (
        "You are going to {destination}! Tick the box next to everything you "
        "have packed, then draw one more thing you want to bring in the empty box."
    ),
    "packing.base_items": [
        "water bottle",
        "comfortable shoes",
        "small backpack",
        "this activity book",
        "pencils and crayons",
        "snack",
    ],
    "packing.hot_items": ["sun hat", "sunscreen", "sunglasses"],
    "packing.cold_items": ["warm coat", "gloves", "woolly hat"],
    "packing.rain_items": ["raincoat", "umbrella"],
    "packing.hike_items": ["hiking shoes", "walking stick"],
    "packing.water_items": ["swimsuit", "towel"],
    "packing.night_items": ["flashlight", "star map"],
    "packing.wildlife_items": ["binoculars", "animal notebook"],
    # -- matching -------------------------------------------------------
    "matching.title": "Match the Shadows",
    "matching.instructions": (
        "Each {kind} on the left has a shadow on the right. Draw a line from "
        "every {kind} to its own shadow."
    ),
    # -- wildlife facts --------------------------------------------------
    "wildlife_facts.title": "Amazing Animals of {destination}",
    "wildlife_facts.instructions": (
        "Meet {count} animals that live around {destination}. Color each one, "
        "then put a star next to the animal you would most like to see."
    ),
    "wildlife_facts.fact_line": "{animal} — look for one near {place}.",
    "wildlife_facts.fact_line_plain": "{animal} — keep your eyes open for this one!",
    # -- quiz -------------------------------------------------------------
    "quiz.title": "The {destination} Quiz",
    "quiz.instructions": (
        "Circle the answer you think is right. There are {count} questions — "
        "ask a grown-up if you get stuck."
    ),
    "quiz.q_wildlife": "Which animal can you meet at {destination}?",
    "quiz.q_landmark": "Which of these can you visit at {destination}?",
    "quiz.q_food": "Which of these is a local food at {destination}?",
    "quiz.q_activity": "Which of these can you do at {destination}?",
    "quiz.distractor_wildlife": ["penguin", "polar bear", "kangaroo", "toucan", "walrus"],
    "quiz.distractor_landmark": [
        "an ice castle",
        "a rocket launch pad",
        "a chocolate mountain",
        "a pirate ship",
    ],
    "quiz.distractor_food": ["moon cheese", "rainbow soup", "dragon pie", "jellyfish jam"],
    "quiz.distractor_activity": [
        "riding a dinosaur",
        "swimming to the moon",
        "growing wings",
        "juggling clouds",
    ],
    # -- drawing ----------------------------------------------------------
    "drawing.title": "Draw What You Saw",
    "drawing.instructions": (
        "Draw the most interesting thing you saw today inside the frame. Add "
        "as many small details as you can remember."
    ),
    "drawing.instructions_prompted": (
        "Draw what you remember about {subject} inside the frame — the way *you* "
        "saw it. Add as many small details as you can."
    ),
    # -- reflection --------------------------------------------------------
    "reflection.title": "My {destination} Memories",
    "reflection.instructions": (
        "Your trip is nearly over! Draw or write your favorite moment, answer "
        "the questions, and color one star for every day you had fun."
    ),
    "reflection.prompt_favorite": "The best thing I saw was...",
    "reflection.prompt_learned": "Something new I learned was...",
    "reflection.prompt_next": "Next time I want to...",
    "reflection.prompt_taste": "The food I liked most was...",
}
