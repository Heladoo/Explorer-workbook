"""English copy for the workbook pages.

Keys are namespaced by activity type. Values are either text with ``{}``
placeholders or lists used as content pools.
"""

LANGUAGE = "en"

#: Letters used to fill the gaps of a word-search grid in this language.
ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

STRINGS: dict[str, object] = {
    # -- shared -------------------------------------------------------
    "common.and": "and",
    "common.join_last": "{first} and {last}",
    "common.explorer": "the explorer",
    "common.kind_picture": "picture",
    "common.this_place": "this place",
    # -- printed page furniture (used by the PDF/HTML renderer) --------
    "pdf.contents": "What's inside this book",
    "pdf.name_label": "This book belongs to:",
    "pdf.illustration": "Illustration goes here",
    "pdf.art_note": "Generate this picture from the prompt file, then drop it in.",
    "pdf.draw_here": "Your drawing goes here",
    "pdf.your_own": "one thing of your own",
    "pdf.match_gutter": "draw your lines across here",
    "pdf.panel_top": "Picture 1",
    "pdf.panel_bottom": "Picture 2",
    "toc.column_number": "#",
    "toc.column_page": "Page",
    "toc.column_activity": "Activity",
    "toc.footer_label": "Contents",
    # -- workbook framing ---------------------------------------------
    "workbook.title_with_names": "{names}'s {destination} Adventure Book",
    "workbook.title_plain": "The {destination} Explorer Workbook",
    "workbook.subtitle": "An activity book for young explorers",
    # -- cover ---------------------------------------------------------
    "cover.title_with_names": "{names}'s Big Trip to {destination}",
    "cover.title_plain": "Welcome to {destination}",
    "cover.subtitle": "Get ready for adventure!",
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
    "maze.start_label": "home",
    # Matches the icon actually drawn as the start marker (see
    # maze.py::_start_label) — the first maze in a book always starts at the
    # airplane, a later one at one of `_REPEAT_START_ICONS`, never a house.
    "maze.start_label.airplane": "the airplane",
    "maze.start_label.dog": "the dog",
    "maze.start_label.bicycle": "the bicycle",
    "maze.start_label.truck": "the lorry",
    "maze.instructions": (
        "Help {hero} get from {start} all the way to {goal}. Draw one line "
        "through the maze without crossing any walls."
    ),
    # Used only when none of the destination's own landmarks resolves to a
    # real, drawable icon (see maze.py::_generic_goal) — pairs the fallback
    # icon's own bare label with the destination name, both so the goal text
    # still agrees with the icon and so the page stays destination-aware
    # (see test_activities_are_destination_aware).
    "maze.goal_fallback": "{subject} near {destination}",
    # -- map -------------------------------------------------------------
    "map.title": "The Route to {destination}",
    "map.instructions": (
        "Here is the whole trip, stop by stop: {stops}. Trace the path with "
        "your finger from the very first stop to the very last."
    ),
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
        "You are going to {destination}! Draw a line from everything you should "
        "pack to the backpack — but a few things don't belong, so look closely. "
        "Then draw one more thing of your own in the empty circle and connect it too."
    ),
    "packing.hot_keywords": ["hot", "sun", "desert", "warm", "dry", "summer", "heat"],
    "packing.cold_keywords": ["cold", "snow", "winter", "freez", "chilly", "ice", "alpine"],
    "packing.rain_keywords": ["rain", "wet", "monsoon", "shower", "humid", "storm"],
    "packing.hike_keywords": ["hike", "hiking", "trek", "trail", "walk", "climb", "mountain"],
    "packing.water_keywords": ["swim", "beach", "lake", "river", "sea", "boat", "spring"],
    "packing.night_keywords": ["night", "star", "stargaz", "cave", "sunset", "campfire"],
    "packing.wildlife_keywords": ["bird", "wildlife", "safari", "animal", "watch"],
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
    "quiz.q_capital": "What is the capital city of {country}?",
    "quiz.q_flag": "Which colors are on the flag of {country}?",
    "quiz.q_language": "What language do people speak in {country}?",
    "quiz.q_continent": "Which continent is {country} in?",
    "quiz.q_currency": "What money do people use in {country}?",
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
    # -- scavenger hunt -------------------------------------------------
    "scavenger_hunt.title": "{destination} Scavenger Hunt",
    "scavenger_hunt.instructions": (
        "Keep your eyes open the whole way! There are {count} things to find on "
        "this page. Tick the box under each picture the moment you spot the real "
        "thing — anywhere, on any day of the trip."
    ),
    # Labels for the spottable symbols in src/activities/_symbols.py. The key
    # after "symbol." is the symbol's slug; a missing one falls back to the
    # English label recorded in the bank.
    "symbol.stop-sign": "a stop sign",
    "symbol.traffic-light": "a traffic light",
    "symbol.police-car": "a police car",
    "symbol.bus": "a bus",
    "symbol.bicycle": "a bicycle",
    "symbol.red-car": "a red car",
    "symbol.truck": "a lorry",
    "symbol.zebra-crossing": "a zebra crossing",
    "symbol.street-lamp": "a street lamp",
    "symbol.road-sign-arrow": "an arrow road sign",
    "symbol.bridge": "a bridge",
    "symbol.clock-tower": "a clock on a building",
    "symbol.fountain": "a fountain",
    "symbol.statue": "a statue",
    "symbol.staircase": "a staircase",
    "symbol.front-door": "an interesting door",
    "symbol.chimney": "a chimney",
    "symbol.flag": "a flag",
    "symbol.dog-on-lead": "a dog on a lead",
    "symbol.dog": "a dog",
    "symbol.cat": "a cat",
    "symbol.pigeon": "a bird on the ground",
    "symbol.butterfly": "a butterfly",
    "symbol.insect": "an insect",
    "symbol.big-tree": "a very big tree",
    "symbol.flower-pot": "a flower in a pot",
    "symbol.ice-cream": "an ice cream",
    "symbol.postbox": "a postbox",
    "symbol.bench": "a bench",
    "symbol.rubbish-bin": "a rubbish bin",
    "symbol.umbrella": "an open umbrella",
    "symbol.suitcase": "a suitcase",
    "symbol.hat": "someone wearing a hat",
    "symbol.balloon": "a balloon",
    "symbol.airplane": "an airplane",
    "symbol.taxi": "a taxi",
    "symbol.tractor": "a tractor",
    "symbol.train": "a train",
    "symbol.boat": "a boat",
    "symbol.fish": "a fish",
    "symbol.man-with-mustache": "a man with a mustache",
    "symbol.house": "a house",
    "symbol.sunglasses": "sunglasses",
    # Destination-flavoured library entries (see data/symbols/library.json) —
    # not in the always-findable pool, but still need a label the moment a
    # future consumer picks one for a matching destination.
    "symbol.winter-coat": "a winter coat",
    "symbol.skis-and-poles": "skis and ski poles",
    "symbol.mountain": "a mountain",
    "symbol.campfire": "a campfire",
    "symbol.chairlift": "a chairlift",
    "symbol.souvlaki": "souvlaki",
    "symbol.pasta": "a bowl of pasta",
    "symbol.owl": "an owl",
    "symbol.dolphins": "dolphins",
    "symbol.brown-bear": "a bear",
    "symbol.swallows-nesting": "swallows in a nest",
    "symbol.goat": "a goat",
    "symbol.kestrel": "a kestrel",
    "symbol.squirrel": "a squirrel",
    "symbol.swan": "a swan",
    "symbol.fox": "a fox",
    "symbol.monkey": "a monkey",
    "symbol.camel": "a camel",
    "symbol.horse": "a horse",
    "symbol.cow": "a cow",
    "symbol.nubian-ibex": "a Nubian ibex",
    "symbol.seal": "a seal",
    "symbol.eagle": "an eagle",
    "symbol.turtle": "a tortoise",
    "symbol.donkey": "a donkey",
    "symbol.water-bottle": "a water bottle",
    "symbol.baseball-cap": "a baseball cap",
    "symbol.binoculars": "binoculars",
    "symbol.rain-coat": "a rain coat",
    "symbol.sunscreen": "sunscreen",
    "symbol.tuxedo": "a tuxedo",
    "symbol.hiking-shoes": "hiking shoes",
    "symbol.flip-flops": "flip-flops",
    "symbol.gloves": "gloves",
    "symbol.woolly-hat": "a woolly hat",
    "symbol.apple-tree": "an apple tree",
    "symbol.palm-tree": "a palm tree",
    "symbol.cactus": "a cactus",
    "symbol.honey": "a jar of honey",
    "symbol.pomegranate": "a pomegranate",
    "symbol.greek-vase": "a Greek vase",
    "symbol.village": "a hillside village",
    "symbol.chestnuts": "chestnuts",
    "symbol.old-church": "a small stone church",
    "symbol.greek-flag": "the Greek flag",
    "symbol.bouzouki": "a bouzouki",
    "symbol.olives": "olives",
    "symbol.grapes": "a bunch of grapes",
    "symbol.backpack": "an explorer backpack",
    # -- word search ----------------------------------------------------------
    "word_search.title": "{destination} Word Search",
    # Split by whether this difficulty's directions include a diagonal (see
    # word_search.py's _DIRECTIONS/_has_diagonal) — "easy" never places a
    # word on the slant, so its instructions must not claim it does.
    "word_search.instructions_straight": (
        "{count} words from your trip are hiding in the grid — across and "
        "down. Find and circle each one: {words}."
    ),
    "word_search.instructions_diagonal": (
        "{count} words from your trip are hiding in the grid — across, down and "
        "sometimes slanted. Find and circle each one: {words}."
    ),
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
    # -- country facts (data/countries.json is tokens; this is the display
    # text) — used by the quiz's capital/flag/language/continent/currency
    # questions and their distractors. Looked up with Strings.optional(),
    # so a token this locale hasn't caught up on degrades to English rather
    # than crashing a book. --------------------------------------------
    "place.athens": "Athens",
    "place.prague": "Prague",
    "place.paris": "Paris",
    "place.rome": "Rome",
    "place.madrid": "Madrid",
    "place.berlin": "Berlin",
    "place.london": "London",
    "place.jerusalem": "Jerusalem",
    "place.tokyo": "Tokyo",
    "place.beijing": "Beijing",
    "place.new_delhi": "New Delhi",
    "place.ankara": "Ankara",
    "place.cairo": "Cairo",
    "place.pretoria": "Pretoria",
    "place.rabat": "Rabat",
    "place.nairobi": "Nairobi",
    "place.washington_dc": "Washington, D.C.",
    "place.ottawa": "Ottawa",
    "place.mexico_city": "Mexico City",
    "place.brasilia": "Brasília",
    "place.buenos_aires": "Buenos Aires",
    "place.lima": "Lima",
    "place.canberra": "Canberra",
    "place.wellington": "Wellington",
    "country.greece": "Greece",
    "country.czechia": "Czechia",
    "country.france": "France",
    "country.italy": "Italy",
    "country.spain": "Spain",
    "country.germany": "Germany",
    "country.united_kingdom": "the United Kingdom",
    "country.israel": "Israel",
    "country.japan": "Japan",
    "country.china": "China",
    "country.india": "India",
    "country.turkey": "Turkey",
    "country.egypt": "Egypt",
    "country.south_africa": "South Africa",
    "country.morocco": "Morocco",
    "country.kenya": "Kenya",
    "country.united_states": "the United States",
    "country.canada": "Canada",
    "country.mexico": "Mexico",
    "country.brazil": "Brazil",
    "country.argentina": "Argentina",
    "country.peru": "Peru",
    "country.australia": "Australia",
    "country.new_zealand": "New Zealand",
    "continent.europe": "Europe",
    "continent.asia": "Asia",
    "continent.africa": "Africa",
    "continent.north_america": "North America",
    "continent.south_america": "South America",
    "continent.oceania": "Oceania",
    "currency.eur": "the euro",
    "currency.czk": "the koruna",
    "currency.gbp": "the pound sterling",
    "currency.ils": "the shekel",
    "currency.jpy": "the yen",
    "currency.cny": "the yuan",
    "currency.inr": "the rupee",
    "currency.try": "the lira",
    "currency.egp": "the Egyptian pound",
    "currency.zar": "the rand",
    "currency.mad": "the dirham",
    "currency.kes": "the shilling",
    "currency.usd": "the dollar",
    "currency.cad": "the Canadian dollar",
    "currency.mxn": "the peso",
    "currency.brl": "the real",
    "currency.ars": "the Argentine peso",
    "currency.pen": "the sol",
    "currency.aud": "the Australian dollar",
    "currency.nzd": "the New Zealand dollar",
    "colour.red": "red",
    "colour.blue": "blue",
    "colour.white": "white",
    "colour.green": "green",
    "colour.yellow": "yellow",
    "colour.black": "black",
    "colour.orange": "orange",
    "colour.gold": "gold",
    "language.el": "Greek",
    "language.cs": "Czech",
    "language.fr": "French",
    "language.it": "Italian",
    "language.es": "Spanish",
    "language.de": "German",
    "language.en": "English",
    "language.he": "Hebrew",
    "language.ja": "Japanese",
    "language.zh": "Chinese",
    "language.hi": "Hindi",
    "language.tr": "Turkish",
    "language.ar": "Arabic",
    "language.pt": "Portuguese",
    # -- dictionary (the quiz page's local-language word list) ----------
    "dictionary.title": "Learn Some Words",
    "dictionary.instructions": (
        "Here are {count} useful words in {language}. Tick the box once "
        "you've said one out loud!"
    ),
    "dictionary.col_meaning": "Meaning",
    "dictionary.col_native": "The word",
    "dictionary.col_say": "How to say it",
    "phrasebook.concept.yes": "yes",
    "phrasebook.concept.no": "no",
    "phrasebook.concept.please": "please",
    "phrasebook.concept.thank_you": "thank you",
    "phrasebook.concept.sorry": "sorry",
    "phrasebook.concept.good_morning": "good morning",
    "phrasebook.concept.good_night": "good night",
    "phrasebook.concept.water": "water",
    "phrasebook.concept.bathroom": "bathroom",
    "phrasebook.concept.family": "family",
}
