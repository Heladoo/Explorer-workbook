"""UI copy for the web form's review and saved screens.

Separate from ``src/locales/`` on purpose: those modules are the *workbook's*
reader-facing copy (validated by tests, fed to activities and the print
layout). This is chrome around the product — the step indicator, the review
page, the saved page — shown in whichever language the generated workbook
came out in, so a Hebrew book gets a Hebrew review page. Only the two
languages the form itself offers (``en``, ``he``) are covered; any other
requested language falls back to English.
"""

from __future__ import annotations

from typing import Any

WEB_COPY: dict[str, dict[str, str]] = {
    "en": {
        "step.create": "Create",
        "step.review": "Review",
        "step.save": "Save",
        "review.eyebrow_almost": "Almost ready",
        "review.eyebrow_ready": "All done",
        "review.subtitle_almost": "{page_count} pages, almost ready to print.",
        "review.subtitle_ready": "{page_count} pages, ready to print.",
        "review.browser_view": "Open in your browser",
        "review.browser_view_note": "See it, add photos, tweak the text — and save it from there",
        "review.checklist_heading": "Before you print",
        "review.checklist_missing_one": "Only 1 page still needs a picture.",
        "review.checklist_missing_many": "Only {missing} pages still need a picture.",
        "review.checklist_done": "Every page already has its picture.",
        "review.checklist_invite": (
            "Open it in your browser to see exactly which ones, add photos, or tweak "
            "any of the text."
        ),
        "review.recommendation": "We recommend giving the whole thing a look before you print.",
        "review.prompts_heading": "Drawing prompts",
        "review.prompts_hint": "Tap one to reveal it, then copy it into your favourite image tool.",
        "review.copy_button": "Copy",
        "review.copy_done": "Copied",
        "review.make_another": "Make another one",
        "review.reference_heading": "Your photos made it into the prompts",
        "review.reference_attach_one": "Attach it when you make the artwork",
        "review.reference_attach_many": "Attach all {count} when you make the artwork",
        "review.reference_body_one": (
            "Every prompt now asks for a child who looks like this — most image "
            "tools take a reference picture alongside the prompt."
        ),
        "review.reference_body_many": (
            "Every prompt now asks for children who look like these — most image "
            "tools take a reference picture alongside the prompt."
        ),
        "saved.eyebrow": "Saved",
        "saved.subtitle": "Your book is ready to print.",
        "saved.booklet_label": "Print it — A5 booklet",
        "saved.booklet_note": (
            "{sheets} A4 sheet(s), with everything you just edited — print both sides, "
            "fold in half, staple the fold"
        ),
        "saved.a4_label": "Print it — A4, no folding",
        "saved.a4_note": (
            "One activity per sheet, nothing to fold or staple — this is the original "
            "version; edits made in the browser aren't in it"
        ),
        "saved.browser_label": "Keep editing",
        "saved.browser_note": "Open it in your browser again",
        "saved.back_label": "Back",
        "saved.start_over_label": "Start over",
        "saved.share_label": "Share",
        "saved.share_copied": "Link copied",
        "saved.feedback_heading": "Quick one — how'd that go?",
        "saved.feedback_great": "🙌 Loved it",
        "saved.feedback_fine": "🙂 It's fine",
        "saved.feedback_poor": "😕 Not really",
        "saved.feedback_placeholder": "Anything you want to tell us? (optional)",
        "saved.feedback_send": "Send",
        "saved.feedback_thanks": "Thanks — that helps.",
        "saved.not_found": "We can't find that book — maybe it was never saved from this machine.",
    },
    "he": {
        "step.create": "יצירה",
        "step.review": "בדיקה",
        "step.save": "שמירה",
        "review.eyebrow_almost": "כמעט מוכן",
        "review.eyebrow_ready": "הכול מוכן",
        "review.subtitle_almost": "{page_count} עמודים, כמעט מוכנים להדפסה.",
        "review.subtitle_ready": "{page_count} עמודים, מוכנים להדפסה.",
        "review.browser_view": "פתחו בדפדפן",
        "review.browser_view_note": "לצפייה, הוספת תמונות, עריכת הטקסט — ושמירה משם",
        "review.checklist_heading": "לפני שמדפיסים",
        "review.checklist_missing_one": "רק עמוד אחד עדיין צריך תמונה.",
        "review.checklist_missing_many": "רק {missing} עמודים עדיין צריכים תמונה.",
        "review.checklist_done": "לכל עמוד כבר יש תמונה משלו.",
        "review.checklist_invite": (
            "פתחו בדפדפן כדי לראות בדיוק אילו עמודים, להוסיף תמונות או לערוך את הטקסט."
        ),
        "review.recommendation": "מומלץ לעבור על החוברת פעם אחת לפני ההדפסה.",
        "review.prompts_heading": "הנחיות לציורים",
        "review.prompts_hint": "לחצו כדי לחשוף, ואז העתיקו לכלי יצירת התמונות שאתם אוהבים.",
        "review.copy_button": "העתקה",
        "review.copy_done": "הועתק",
        "review.make_another": "ליצור חוברת נוספת",
        "review.reference_heading": "התמונות שלכם נכנסו להנחיות",
        "review.reference_attach_one": "צרפו אותה כשיוצרים את האיור",
        "review.reference_attach_many": "צרפו את כל {count} כשיוצרים את האיור",
        "review.reference_body_one": (
            "כל הנחיה מבקשת עכשיו ילד שדומה לזה שבתמונה — רוב כלי היצירה מקבלים "
            "תמונת ייחוס לצד ההנחיה."
        ),
        "review.reference_body_many": (
            "כל הנחיה מבקשת עכשיו ילדים שדומים לאלה שבתמונות — רוב כלי היצירה מקבלים "
            "תמונת ייחוס לצד ההנחיה."
        ),
        "saved.eyebrow": "נשמר",
        "saved.subtitle": "החוברת מוכנה להדפסה.",
        "saved.booklet_label": "הדפסה — חוברת A5",
        "saved.booklet_note": (
            "{sheets} גיליונות A4, כולל כל מה שערכתם עכשיו — הדפיסו משני הצדדים, "
            "קפלו לשניים והדקו בקיפול"
        ),
        "saved.a4_label": "הדפסה — A4, בלי קיפול",
        "saved.a4_note": (
            "פעילות אחת בכל גיליון, בלי לקפל ובלי להדק — זו הגרסה המקורית, "
            "בלי העריכות שעשיתם בדפדפן"
        ),
        "saved.browser_label": "להמשיך לערוך",
        "saved.browser_note": "פתחו שוב בדפדפן",
        "saved.back_label": "חזרה",
        "saved.start_over_label": "התחלה מחדש",
        "saved.share_label": "שיתוף",
        "saved.share_copied": "הקישור הועתק",
        "saved.feedback_heading": "שאלה קצרה — איך היה?",
        "saved.feedback_great": "🙌 אהבנו מאוד",
        "saved.feedback_fine": "🙂 סבבה",
        "saved.feedback_poor": "😕 לא כל כך",
        "saved.feedback_placeholder": "משהו שתרצו לספר לנו? (לא חובה)",
        "saved.feedback_send": "שליחה",
        "saved.feedback_thanks": "תודה — זה עוזר לנו.",
        "saved.not_found": "לא מצאנו את החוברת הזו — ייתכן שהיא מעולם לא נשמרה מהמחשב הזה.",
    },
}

_DEFAULT_LANGUAGE = "en"


def web_text(language: str | None, key: str, **kwargs: Any) -> str:
    """Look up ``key`` for ``language``, falling back to English.

    Falls back key-by-key, not whole-table — a language present in
    ``WEB_COPY`` but missing one newer key still gets everything else in its
    own language rather than the whole page reverting to English.
    """
    table = WEB_COPY.get(language or _DEFAULT_LANGUAGE, {})
    value = table.get(key, WEB_COPY[_DEFAULT_LANGUAGE].get(key, key))
    return value.format(**kwargs) if kwargs else value
