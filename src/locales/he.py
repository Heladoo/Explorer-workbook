"""Hebrew copy for the workbook pages.

Same keys as ``en.py``. ``DIRECTION`` makes the printed page right-to-left.

Image prompts are deliberately not translated — they stay English wherever the
workbook language goes, because that is what image models are trained on. A
translated destination pack carries an ``illustration_terms`` map so the prompt
generator can put the English term back into the prompt.
"""

LANGUAGE = "he"
DIRECTION = "rtl"

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
    "common.kind_animal": "חיה",
    "common.kind_place": "מקום",
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
    # -- workbook framing ---------------------------------------------
    "workbook.title_with_names": "חוברת ההרפתקה של {names} ב{destination}",
    "workbook.title_plain": "חוברת החוקרים של {destination}",
    "workbook.subtitle": "חוברת פעילות לחוקרים צעירים",
    # -- cover ---------------------------------------------------------
    "cover.title_with_names": "הטיול הגדול של {names} ל{destination}",
    "cover.title_plain": "ברוכים הבאים ל{destination}",
    "cover.instructions_with_names": (
        "חוברת ההרפתקה הזאת שייכת ל{names}. כתבו את השם שלכם על הקו, "
        "צבעו את השער, והתכוננו לגלות את {destination}!"
    ),
    "cover.instructions_plain": (
        "כתבו את השם שלכם על הקו, צבעו את השער, והתכוננו לגלות את {destination}!"
    ),
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
    "maze.instructions": (
        "עזרו ל{hero} להגיע מ{start} עד {goal}. מתחו קו אחד דרך המבוך בלי לחצות "
        "אף קיר."
    ),
    "maze.collect": "אספו בדרך {items}.",
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
        "אתם נוסעים ל{destination}! סמנו וי ליד כל דבר שארזתם, ואז ציירו במשבצת "
        "הריקה עוד דבר אחד שבא לכם לקחת."
    ),
    "packing.base_items": [
        "בקבוק מים",
        "נעליים נוחות",
        "תיק גב קטן",
        "חוברת הפעילות הזאת",
        "עפרונות וצבעים",
        "חטיף",
    ],
    "packing.hot_keywords": ["חם", "שמש", "מדבר", "יבש", "קיץ"],
    "packing.cold_keywords": ["קר", "שלג", "חורף", "קפוא", "צונן"],
    "packing.rain_keywords": ["גשם", "רטוב", "סוער", "לח"],
    "packing.hike_keywords": ["טיול", "הליכה", "מסלול", "הר", "טיפוס"],
    "packing.water_keywords": ["שחייה", "ים", "חוף", "אגם", "נהר", "סירה", "מעיין"],
    "packing.night_keywords": ["לילה", "כוכב", "מערה", "שקיעה", "מדורה"],
    "packing.wildlife_keywords": ["ציפור", "חיות", "חיה", "טבע", "צפייה"],
    "packing.hot_items": ["כובע שמש", "קרם הגנה", "משקפי שמש"],
    "packing.cold_items": ["מעיל חם", "כפפות", "כובע צמר"],
    "packing.rain_items": ["מעיל גשם", "מטרייה"],
    "packing.hike_items": ["נעלי הליכה", "מקל הליכה"],
    "packing.water_items": ["בגד ים", "מגבת"],
    "packing.night_items": ["פנס", "מפת כוכבים"],
    "packing.wildlife_items": ["משקפת", "מחברת חיות"],
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
    # -- word search --------------------------------------------------------
    "word_search.title": "תפזורת {destination}",
    "word_search.instructions": (
        "{count} מילים מהטיול שלכם מתחבאות בתפזורת — לרוחב, לאורך ולפעמים "
        "באלכסון. מצאו והקיפו כל אחת: {words}."
    ),
    # -- crossword ----------------------------------------------------------
    "crossword.title": "תשבץ {destination}",
    "crossword.instructions": (
        "קראו כל הגדרה וכתבו את התשובה במשבצות, אות אחת בכל משבצת. יש {count} "
        "הגדרות — המילים נחתכות זו בזו, אז אות שכבר גיליתם תעזור לכם בהמשך."
    ),
    "crossword.clue_wildlife": "חיה שאפשר לפגוש ב{destination}",
    "crossword.clue_landmarks": "מקום ששווה לבקר בו ב{destination}",
    "crossword.clue_plants": "משהו ירוק שגדל ב{destination}",
    "crossword.clue_local_food": "משהו טעים לאכול ב{destination}",
    "crossword.clue_activities": "משהו כיף לעשות ב{destination}",
    "crossword.across": "מאוזן",
    "crossword.down": "מאונך",
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
}
