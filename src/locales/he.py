"""Hebrew copy for the workbook pages.

Same keys as ``en.py``. ``DIRECTION`` makes the printed page right-to-left.

Image prompts are deliberately not translated — they stay English wherever the
workbook language goes, because that is what image models are trained on. A
translated destination pack carries an ``illustration_terms`` map so the prompt
generator can put the English term back into the prompt.
"""

LANGUAGE = "he"
DIRECTION = "rtl"

#: Letters used to fill the gaps of a word-search grid. Final (sofit) forms
#: — ך ם ן ף ץ — are excluded: they are only correct Hebrew at the true end
#: of a word, so a filler letter must never use one.
ALPHABET = "אבגדהוזחטיכלמנסעפצקרשת"

#: Hebrew term -> English, for copy that ends up inside an image brief
#: (packing items, quiz options). The pack supplies the same map for its own
#: entries; the prompt generator merges the two.
TERMS: dict[str, str] = {
    # packing items
    "בקבוק מים": "water bottle",
    "נעליים נוחות": "comfortable shoes",
    "תיק גב קטן": "small backpack",
    "חוברת הפעילות הזאת": "this activity book",
    "עפרונות וצבעים": "pencils and crayons",
    "חטיף": "snack",
    "כובע שמש": "sun hat",
    "קרם הגנה": "sunscreen",
    "משקפי שמש": "sunglasses",
    "מעיל חם": "warm coat",
    "כפפות": "gloves",
    "כובע צמר": "woolly hat",
    "מעיל גשם": "raincoat",
    "מטרייה": "umbrella",
    "נעלי הליכה": "hiking shoes",
    "מקל הליכה": "walking stick",
    "בגד ים": "swimsuit",
    "מגבת": "towel",
    "פנס": "flashlight",
    "מפת כוכבים": "star map",
    "משקפת": "binoculars",
    "מחברת חיות": "animal notebook",
    # quiz distractors
    "פינגווין": "penguin",
    "דוב קוטב": "polar bear",
    "קנגורו": "kangaroo",
    "טוקן": "toucan",
    "ולרוס": "walrus",
    "טירת קרח": "an ice castle",
    "מסלול שיגור לחלל": "a rocket launch pad",
    "הר של שוקולד": "a chocolate mountain",
    "ספינת פיראטים": "a pirate ship",
    "גבינת ירח": "moon cheese",
    "מרק בצבעי הקשת": "rainbow soup",
    "פאי דרקון": "dragon pie",
    "ריבת מדוזה": "jellyfish jam",
    "רכיבה על דינוזאור": "riding a dinosaur",
    "שחייה עד הירח": "swimming to the moon",
    "לגדל כנפיים": "growing wings",
    "לונגל עננים": "juggling clouds",
}

STRINGS: dict[str, object] = {
    # -- shared -------------------------------------------------------
    "common.and": "ו",
    "common.join_last": "{first} ו{last}",
    "common.explorer": "החוקר",
    "common.kind_picture": "ציור",
    "common.this_place": "המקום הזה",
    # -- printed page furniture ---------------------------------------
    "pdf.contents": "מה יש בחוברת",
    "pdf.name_label": "החוברת הזאת שייכת ל:",
    "pdf.illustration": "כאן יבוא האיור",
    "pdf.art_note": "צרו את התמונה לפי קובץ ההנחיות, ואז שימו אותה כאן.",
    "pdf.draw_here": "כאן מציירים",
    "pdf.your_own": "משהו משלכם",
    "pdf.match_gutter": "מתחו קווים כאן",
    "pdf.panel_top": "תמונה 1",
    "pdf.panel_bottom": "תמונה 2",
    "toc.column_number": "#",
    "toc.column_page": "עמוד",
    "toc.column_activity": "פעילות",
    "toc.footer_label": "תוכן",
    # -- workbook framing ---------------------------------------------
    "workbook.title_with_names": "חוברת ההרפתקה של {names} ב{destination}",
    "workbook.title_plain": "חוברת החוקרים של {destination}",
    "workbook.subtitle": "חוברת פעילות לחוקרים צעירים",
    # -- cover ---------------------------------------------------------
    "cover.title_with_names": "הטיול הגדול של {names} ל{destination}",
    "cover.title_plain": "ברוכים הבאים ל{destination}",
    "cover.subtitle": "תתכוננו להרפתקה!",
    # -- coloring ------------------------------------------------------
    "coloring.title": "צבעו את {subject}",
    "coloring.instructions": (
        "צבעו את התמונה של {subject}. חפשו בה גם את {extras} — אולי תראו אותם "
        "באמת בטיול!"
    ),
    "coloring.instructions_plain": (
        "צבעו את התמונה של {subject}. השתמשו בכל הצבעים שבא לכם, ואז הראו למישהו "
        "מה יצרתם."
    ),
    # -- maze ----------------------------------------------------------
    "maze.title": "הדרך אל {goal}",
    "maze.start_label": "הבית",
    # Matches the icon actually drawn as the start marker (see
    # maze.py::_start_label) — the first maze in a book always starts at the
    # airplane, a later one at one of `_REPEAT_START_ICONS`, never a house.
    # Definite-article form ("the X"), not "from the X" — maze.instructions
    # already prefixes a literal מ onto {start} ("מ{start}"), so the label
    # itself must stay bare or the rendered text would double up ("ממה...").
    "maze.start_label.airplane": "המטוס",
    "maze.start_label.dog": "הכלב",
    "maze.start_label.bicycle": "האופניים",
    "maze.start_label.truck": "המשאית",
    "maze.instructions": (
        "עזרו ל{hero} להגיע מ{start} עד {goal}. מתחו קו אחד דרך המבוך בלי לחצות "
        "אף קיר."
    ),
    # Used only when none of the destination's own landmarks resolves to a
    # real, drawable icon (see maze.py::_generic_goal) — pairs the fallback
    # icon's own bare label with the destination name, both so the goal text
    # still agrees with the icon and so the page stays destination-aware
    # (see test_activities_are_destination_aware). Same "X ליד Y" pattern as
    # wildlife_facts.fact_line.
    "maze.goal_fallback": "{subject} ליד {destination}",
    # -- map ---------------------------------------------------------------
    "map.title": "הדרך אל {destination}",
    "map.instructions": (
        "הנה כל הטיול, תחנה אחר תחנה: {stops}. עקבו עם האצבע אחרי המסלול "
        "מהתחנה הראשונה ועד האחרונה."
    ),
    # -- spot the difference -------------------------------------------
    "spot_difference.title": "מצאו את ההבדלים",
    "spot_difference.instructions": (
        "שתי התמונות של {subject} נראות אותו דבר — אבל {count} דברים שונים בהן. "
        "הקיפו כל הבדל שמצאתם."
    ),
    "spot_difference.change_missing": "{item} חסר בתמונה השנייה",
    "spot_difference.change_extra": "נוסף {item} בתמונה השנייה",
    "spot_difference.change_moved": "{item} עבר לצד השני",
    "spot_difference.change_resized": "{item} בגודל אחר",
    # -- hidden objects -------------------------------------------------
    "hidden_objects.title": "מצאו את הדברים המוסתרים",
    "hidden_objects.instructions": (
        "{count} דברים מתחבאים בתמונה של {subject}: {items}. הקיפו כל אחד "
        "כשאתם מוצאים אותו."
    ),
    # -- packing --------------------------------------------------------
    "packing.title": "ארזו את תיק החוקרים",
    "packing.instructions": (
        "אתם נוסעים ל{destination}! חברו בקו כל דבר שכדאי לארוז אל התיק — אבל לא "
        "הכל שייך לשם, אז הביטו היטב. אחר כך ציירו במעגל הריק עוד דבר אחד משלכם "
        "וחברו גם אותו."
    ),
    "packing.hot_keywords": ["חם", "שמש", "מדבר", "יבש", "קיץ"],
    "packing.cold_keywords": ["קר", "שלג", "חורף", "קפוא", "צונן"],
    "packing.rain_keywords": ["גשם", "רטוב", "סוער", "לח"],
    "packing.hike_keywords": ["טיול", "הליכה", "מסלול", "הר", "טיפוס"],
    "packing.water_keywords": ["שחייה", "ים", "חוף", "אגם", "נהר", "סירה", "מעיין"],
    "packing.night_keywords": ["לילה", "כוכב", "מערה", "שקיעה", "מדורה"],
    "packing.wildlife_keywords": ["ציפור", "חיות", "חיה", "טבע", "צפייה"],
    # -- matching -------------------------------------------------------
    "matching.title": "התאימו את הצללים",
    "matching.instructions": (
        "לכל {kind} בצד אחד יש צל בצד השני. מתחו קו מכל {kind} אל הצל שלו."
    ),
    # -- wildlife facts --------------------------------------------------
    "wildlife_facts.title": "חיות מדהימות של {destination}",
    "wildlife_facts.instructions": (
        "הכירו {count} חיות שחיות באזור {destination}. צבעו כל אחת, ואז סמנו "
        "כוכב ליד החיה שהכי בא לכם לפגוש."
    ),
    "wildlife_facts.fact_line": "{animal} — חפשו אותה ליד {place}.",
    "wildlife_facts.fact_line_plain": "{animal} — פקחו עיניים, אולי תראו אותה!",
    # -- quiz -------------------------------------------------------------
    "quiz.title": "החידון של {destination}",
    "quiz.instructions": (
        "הקיפו את התשובה שנראית לכם נכונה. יש {count} שאלות — אם נתקעתם, שאלו "
        "מבוגר."
    ),
    "quiz.q_wildlife": "איזו חיה אפשר לפגוש ב{destination}?",
    "quiz.q_landmark": "מה מהדברים האלה אפשר לבקר ב{destination}?",
    "quiz.q_food": "מה מהדברים האלה הוא אוכל מקומי ב{destination}?",
    "quiz.q_activity": "מה מהדברים האלה אפשר לעשות ב{destination}?",
    "quiz.q_capital": "מה בירת {country}?",
    "quiz.q_flag": "אילו צבעים יש בדגל של {country}?",
    "quiz.q_language": "באיזו שפה מדברים ב{country}?",
    "quiz.q_continent": "באיזו יבשת נמצאת {country}?",
    "quiz.q_currency": "באיזה כסף משתמשים ב{country}?",
    "quiz.distractor_wildlife": ["פינגווין", "דוב קוטב", "קנגורו", "טוקן", "ולרוס"],
    "quiz.distractor_landmark": [
        "טירת קרח",
        "מסלול שיגור לחלל",
        "הר של שוקולד",
        "ספינת פיראטים",
    ],
    "quiz.distractor_food": ["גבינת ירח", "מרק בצבעי הקשת", "פאי דרקון", "ריבת מדוזה"],
    "quiz.distractor_activity": [
        "רכיבה על דינוזאור",
        "שחייה עד הירח",
        "לגדל כנפיים",
        "לונגל עננים",
    ],
    # -- scavenger hunt -------------------------------------------------
    "scavenger_hunt.title": "ציד המטמון של {destination}",
    "scavenger_hunt.instructions": (
        "פקחו עיניים לאורך כל הדרך! יש בדף הזה {count} דברים למצוא. סמנו וי "
        "במשבצת שמתחת לכל ציור ברגע שראיתם את הדבר האמיתי — בכל מקום ובכל "
        "יום של הטיול."
    ),
    # תוויות לסמלים שב-src/activities/_symbols.py
    "symbol.stop-sign": "תמרור עצור",
    "symbol.traffic-light": "רמזור",
    "symbol.police-car": "ניידת משטרה",
    "symbol.bus": "אוטובוס",
    "symbol.bicycle": "אופניים",
    "symbol.red-car": "מכונית אדומה",
    "symbol.truck": "משאית",
    "symbol.zebra-crossing": "מעבר חצייה",
    "symbol.street-lamp": "פנס רחוב",
    "symbol.road-sign-arrow": "תמרור עם חץ",
    "symbol.bridge": "גשר",
    "symbol.clock-tower": "שעון על בניין",
    "symbol.fountain": "מזרקה",
    "symbol.statue": "פסל",
    "symbol.staircase": "גרם מדרגות",
    "symbol.front-door": "דלת מעניינת",
    "symbol.chimney": "ארובה",
    "symbol.flag": "דגל",
    "symbol.dog-on-lead": "כלב ברצועה",
    "symbol.dog": "כלב",
    "symbol.cat": "חתול",
    "symbol.pigeon": "ציפור על הרצפה",
    "symbol.butterfly": "פרפר",
    "symbol.insect": "חרק",
    "symbol.big-tree": "עץ ענק",
    "symbol.flower-pot": "פרח בעציץ",
    "symbol.ice-cream": "גלידה",
    "symbol.postbox": "תיבת דואר",
    "symbol.bench": "ספסל",
    "symbol.rubbish-bin": "פח אשפה",
    "symbol.umbrella": "מטרייה פתוחה",
    "symbol.suitcase": "מזוודה",
    "symbol.hat": "מישהו עם כובע",
    "symbol.balloon": "בלון",
    "symbol.airplane": "מטוס",
    "symbol.taxi": "מונית",
    "symbol.tractor": "טרקטור",
    "symbol.train": "רכבת",
    "symbol.boat": "סירה",
    "symbol.fish": "דג",
    "symbol.man-with-mustache": "איש עם שפם",
    "symbol.house": "בית",
    "symbol.sunglasses": "משקפי שמש",
    # Destination-flavoured library entries (see data/symbols/library.json) —
    # not in the always-findable pool, but still need a label the moment a
    # future consumer picks one for a matching destination.
    "symbol.winter-coat": "מעיל חורף",
    "symbol.skis-and-poles": "מגלשי סקי ומקלות סקי",
    "symbol.mountain": "הר",
    "symbol.campfire": "מדורה",
    "symbol.chairlift": "רכבל כיסאות",
    "symbol.souvlaki": "סובלאקי",
    "symbol.pasta": "קערת פסטה",
    "symbol.owl": "ינשוף",
    "symbol.dolphins": "דולפינים",
    "symbol.brown-bear": "דוב חום",
    "symbol.swallows-nesting": "סנוניות בקן",
    "symbol.goat": "עז",
    "symbol.kestrel": "בז מצוי",
    "symbol.squirrel": "סנאי",
    "symbol.swan": "ברבור",
    "symbol.fox": "שועל",
    "symbol.monkey": "קוף",
    "symbol.camel": "גמל",
    "symbol.horse": "סוס",
    "symbol.cow": "פרה",
    "symbol.nubian-ibex": "יעל נובי",
    "symbol.seal": "כלב ים",
    "symbol.eagle": "נשר",
    "symbol.turtle": "צב יבשה",
    "symbol.donkey": "חמור",
    "symbol.water-bottle": "בקבוק מים",
    "symbol.baseball-cap": "כובע בייסבול",
    "symbol.binoculars": "משקפת",
    "symbol.rain-coat": "מעיל גשם",
    "symbol.sunscreen": "קרם הגנה",
    "symbol.tuxedo": "חליפת ערב",
    "symbol.hiking-shoes": "נעלי הליכה",
    "symbol.flip-flops": "כפכפים",
    "symbol.gloves": "כפפות",
    "symbol.woolly-hat": "כובע צמר",
    "symbol.apple-tree": "עץ תפוחים",
    "symbol.palm-tree": "עץ דקל",
    "symbol.cactus": "קקטוס",
    "symbol.honey": "צנצנת דבש",
    "symbol.pomegranate": "רימון",
    "symbol.greek-vase": "אגרטל יווני",
    "symbol.village": "כפר על גבעה",
    "symbol.chestnuts": "ערמונים",
    "symbol.old-church": "כנסייה קטנה מאבן",
    "symbol.greek-flag": "הדגל היווני",
    "symbol.bouzouki": "בוזוקי",
    "symbol.olives": "זיתים",
    "symbol.grapes": "אשכול ענבים",
    "symbol.backpack": "תיק חוקרים",
    # -- word search ----------------------------------------------------------
    "word_search.title": "תפזורת {destination}",
    # Split by whether this difficulty's directions include a diagonal (see
    # word_search.py's _DIRECTIONS/_has_diagonal) — "easy" never places a
    # word on the slant, so its instructions must not claim it does.
    "word_search.instructions_straight": (
        "{count} מילים מהטיול שלכם מתחבאות בתפזורת — לרוחב ולאורך. מצאו "
        "והקיפו כל אחת: {words}."
    ),
    "word_search.instructions_diagonal": (
        "{count} מילים מהטיול שלכם מתחבאות בתפזורת — לרוחב, לאורך ולפעמים "
        "באלכסון. מצאו והקיפו כל אחת: {words}."
    ),
    # -- drawing ----------------------------------------------------------
    "drawing.title": "ציירו מה ראיתם",
    "drawing.instructions": (
        "ציירו במסגרת את הדבר הכי מעניין שראיתם היום. הוסיפו כמה שיותר פרטים "
        "קטנים שאתם זוכרים."
    ),
    "drawing.instructions_prompted": (
        "ציירו במסגרת מה שאתם זוכרים מ{subject} — בדיוק כמו שאתם ראיתם. הוסיפו "
        "כמה שיותר פרטים קטנים."
    ),
    # -- reflection --------------------------------------------------------
    "reflection.title": "הזיכרונות שלי מ{destination}",
    "reflection.instructions": (
        "הטיול כמעט נגמר! ציירו או כתבו את הרגע הכי אהוב עליכם, ענו על השאלות, "
        "וצבעו כוכב אחד על כל יום שהיה בו כיף."
    ),
    "reflection.prompt_favorite": "הדבר הכי יפה שראיתי היה...",
    "reflection.prompt_learned": "משהו חדש שלמדתי הוא...",
    "reflection.prompt_next": "בפעם הבאה בא לי...",
    "reflection.prompt_taste": "האוכל שהכי אהבתי היה...",
    # -- country facts — mirrors the tokens in data/countries.json ------
    "place.athens": "אתונה",
    "place.prague": "פראג",
    "place.paris": "פריז",
    "place.rome": "רומא",
    "place.madrid": "מדריד",
    "place.berlin": "ברלין",
    "place.london": "לונדון",
    "place.jerusalem": "ירושלים",
    "place.tokyo": "טוקיו",
    "place.beijing": "בייג'ינג",
    "place.new_delhi": "ניו דלהי",
    "place.ankara": "אנקרה",
    "place.cairo": "קהיר",
    "place.pretoria": "פרטוריה",
    "place.rabat": "רבאט",
    "place.nairobi": "ניירובי",
    "place.washington_dc": "וושינגטון הבירה",
    "place.ottawa": "אוטווה",
    "place.mexico_city": "מקסיקו סיטי",
    "place.brasilia": "ברזיליה",
    "place.buenos_aires": "בואנוס איירס",
    "place.lima": "לימה",
    "place.canberra": "קנברה",
    "place.wellington": "וולינגטון",
    "country.greece": "יוון",
    "country.czechia": "צ'כיה",
    "country.france": "צרפת",
    "country.italy": "איטליה",
    "country.spain": "ספרד",
    "country.germany": "גרמניה",
    "country.united_kingdom": "בריטניה",
    "country.israel": "ישראל",
    "country.japan": "יפן",
    "country.china": "סין",
    "country.india": "הודו",
    "country.turkey": "טורקיה",
    "country.egypt": "מצרים",
    "country.south_africa": "דרום אפריקה",
    "country.morocco": "מרוקו",
    "country.kenya": "קניה",
    "country.united_states": "ארצות הברית",
    "country.canada": "קנדה",
    "country.mexico": "מקסיקו",
    "country.brazil": "ברזיל",
    "country.argentina": "ארגנטינה",
    "country.peru": "פרו",
    "country.australia": "אוסטרליה",
    "country.new_zealand": "ניו זילנד",
    "continent.europe": "אירופה",
    "continent.asia": "אסיה",
    "continent.africa": "אפריקה",
    "continent.north_america": "צפון אמריקה",
    "continent.south_america": "דרום אמריקה",
    "continent.oceania": "אוקיאניה",
    "currency.eur": "האירו",
    "currency.czk": "הקורונה",
    "currency.gbp": "הלירה הבריטית",
    "currency.ils": "השקל",
    "currency.jpy": "היין",
    "currency.cny": "היואן",
    "currency.inr": "הרופי",
    "currency.try": "הלירה הטורקית",
    "currency.egp": "הלירה המצרית",
    "currency.zar": "הרנד",
    "currency.mad": "הדירהם",
    "currency.kes": "השילינג",
    "currency.usd": "הדולר",
    "currency.cad": "הדולר הקנדי",
    "currency.mxn": "הפסו",
    "currency.brl": "הריאל",
    "currency.ars": "הפסו הארגנטינאי",
    "currency.pen": "הסול",
    "currency.aud": "הדולר האוסטרלי",
    "currency.nzd": "הדולר הניו זילנדי",
    "colour.red": "אדום",
    "colour.blue": "כחול",
    "colour.white": "לבן",
    "colour.green": "ירוק",
    "colour.yellow": "צהוב",
    "colour.black": "שחור",
    "colour.orange": "כתום",
    "colour.gold": "זהב",
    "language.el": "יוונית",
    "language.cs": "צ'כית",
    "language.fr": "צרפתית",
    "language.it": "איטלקית",
    "language.es": "ספרדית",
    "language.de": "גרמנית",
    "language.en": "אנגלית",
    "language.he": "עברית",
    "language.ja": "יפנית",
    "language.zh": "סינית",
    "language.hi": "הינדי",
    "language.tr": "טורקית",
    "language.ar": "ערבית",
    "language.pt": "פורטוגזית",
    # -- dictionary (the quiz page's local-language word list) ----------
    "dictionary.title": "בואו נלמד כמה מילים",
    "dictionary.instructions": (
        "הנה {count} מילים שימושיות ב{language}. סמנו וי בתיבה אחרי "
        "שאמרתם מילה בקול."
    ),
    "dictionary.col_meaning": "משמעות",
    "dictionary.col_native": "המילה",
    "dictionary.col_say": "איך אומרים",
    "phrasebook.concept.yes": "כן",
    "phrasebook.concept.no": "לא",
    "phrasebook.concept.please": "בבקשה",
    "phrasebook.concept.thank_you": "תודה",
    "phrasebook.concept.sorry": "סליחה",
    "phrasebook.concept.good_morning": "בוקר טוב",
    "phrasebook.concept.good_night": "לילה טוב",
    "phrasebook.concept.water": "מים",
    "phrasebook.concept.bathroom": "שירותים",
    "phrasebook.concept.family": "משפחה",
}
