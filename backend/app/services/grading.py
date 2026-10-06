"""Server-side answer grading with Duolingo-style leniency and error classification.

Leniency: case, punctuation, contractions and missing accents are forgiven (accents are flagged
as a typo, "Pay attention to the accents"). A one-letter slip in a long content word is a typo.
Grammar-bearing words (articles, verb forms, pronouns) are never forgiven: "la pan" is wrong.

Every wrong answer gets an `error_type`, which feeds the learner model and the tutor agents:
    accent | spelling | gender_article | agreement | verb_form | word_order |
    missing_word | extra_word | vocabulary
"""
import re
import unicodedata
from dataclasses import dataclass

from app.services.exercise_types import display_answer

ARTICLES = {"el", "la", "los", "las", "un", "una", "unos", "unas"}
PRONOUNS = {"yo", "tu", "tú", "el", "él", "ella", "nosotros", "nosotras", "ellos", "ellas", "usted", "mi", "mis"}
VERB_FORMS = {
    "soy", "eres", "es", "somos", "son",
    "como", "comes", "come", "comemos", "comen",
    "bebo", "bebes", "bebe", "bebemos", "beben",
    "tengo", "tienes", "tiene", "tenemos", "tienen",
    "estoy", "estás", "estas", "está", "esta", "estamos", "están",
}
PROTECTED = ARTICLES | PRONOUNS | VERB_FORMS

CONTRACTIONS = {
    "don't": "do not", "doesn't": "does not", "isn't": "is not", "aren't": "are not",
    "i'm": "i am", "you're": "you are", "he's": "he is", "she's": "she is", "it's": "it is",
    "we're": "we are", "they're": "they are", "what's": "what is", "where's": "where is",
    "who's": "who is", "that's": "that is", "i've": "i have", "can't": "cannot",
}

_PUNCT = re.compile(r"[¿?¡!.,;:\"“”«»()\-]")


def strip_accents(s: str) -> str:
    # keep ñ distinct from n? Duolingo treats ñ as an accent typo too; so do we.
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


def normalize(text: str) -> str:
    t = unicodedata.normalize("NFC", text).lower().replace("’", "'").replace("‘", "'")
    t = _PUNCT.sub(" ", t)
    t = " ".join(t.split())
    for short, long in CONTRACTIONS.items():
        t = re.sub(rf"(?<![\w']){re.escape(short)}(?![\w'])", long, t)
    return t.replace("'", "").strip()


def tokens(text: str) -> list[str]:
    return normalize(text).split()


def edit_distance(a: str, b: str) -> int:
    if a == b:
        return 0
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


@dataclass
class GradeResult:
    correct: bool
    typo: bool = False
    error_type: str | None = None
    correct_answer: str = ""
    feedback: str | None = None  # short deterministic hint ("Pay attention to the accents")


def _is_agreement_pair(a: str, b: str) -> bool:
    # rojo/roja, pequeños/pequeñas
    for x, y in (("o", "a"), ("os", "as")):
        if (a.endswith(x) and b.endswith(y) and a[: -len(x)] == b[: -len(y)]) or (
            b.endswith(x) and a.endswith(y) and b[: -len(x)] == a[: -len(y)]
        ):
            return True
    return False


def compare_text(user: str, expected: str) -> GradeResult:
    """Compare one free-text answer against one accepted answer."""
    u, e = tokens(user), tokens(expected)
    if u == e:
        return GradeResult(True)
    if [strip_accents(t) for t in u] == [strip_accents(t) for t in e]:
        return GradeResult(True, typo=True, error_type="accent", feedback="Pay attention to the accents.")
    if sorted(u) == sorted(e):
        return GradeResult(False, error_type="word_order")
    if len(u) < len(e):
        return GradeResult(False, error_type="missing_word")
    if len(u) > len(e):
        return GradeResult(False, error_type="extra_word")

    diffs = [(a, b) for a, b in zip(u, e, strict=True) if a != b]
    if len(diffs) == 1:
        a, b = diffs[0]
        sa, sb = strip_accents(a), strip_accents(b)
        if sa == sb:
            return GradeResult(True, typo=True, error_type="accent", feedback="Pay attention to the accents.")
        if _is_agreement_pair(sa, sb):
            return GradeResult(False, error_type="agreement")
        if b not in PROTECTED and len(b) >= 4 and edit_distance(sa, sb) == 1:
            return GradeResult(True, typo=True, error_type="spelling", feedback=f"You have a typo: {b}")
    if all(a in ARTICLES and b in ARTICLES for a, b in diffs):
        return GradeResult(False, error_type="gender_article")
    if all(_is_agreement_pair(a, b) for a, b in diffs):
        return GradeResult(False, error_type="agreement")
    if any(a in VERB_FORMS and b in VERB_FORMS for a, b in diffs) or all(
        len(a) >= 3 and a[:3] == b[:3] for a, b in diffs
    ):
        return GradeResult(False, error_type="verb_form")
    return GradeResult(False, error_type="vocabulary")


_SEVERITY = {
    None: 0, "accent": 1, "spelling": 1, "agreement": 2, "gender_article": 2, "verb_form": 2,
    "word_order": 3, "extra_word": 4, "missing_word": 4, "vocabulary": 5,
}


def best_match(user: str, accepted: list[str]) -> GradeResult:
    """Grade against every accepted answer and keep the most forgiving / most specific result."""
    results = [compare_text(user, a) for a in accepted]
    for r in results:
        if r.correct and not r.typo:
            return r
    typos = [r for r in results if r.correct]
    if typos:
        return typos[0]
    return min(results, key=lambda r: _SEVERITY.get(r.error_type, 5))


def grade(ex_type: str, payload: dict, answer: dict) -> GradeResult:
    correct_answer = display_answer(ex_type, payload)

    if ex_type == "multiple_choice":
        choice = answer.get("choice")
        ok = isinstance(choice, int) and choice == payload["answer"]
        result = GradeResult(ok)
        if not ok and isinstance(choice, int) and 0 <= choice < len(payload["choices"]):
            picked = payload["choices"][choice]["text"]
            r = compare_text(picked, correct_answer)
            result.error_type = r.error_type if r.error_type in ("gender_article", "agreement") else "vocabulary"
        elif not ok:
            result.error_type = "vocabulary"

    elif ex_type == "fill_blank":
        picked = str(answer.get("choice") or answer.get("text") or "")
        expected = payload["answer"]
        if normalize(picked) == normalize(expected):
            result = GradeResult(True)
        else:
            r = compare_text(picked, expected)
            result = GradeResult(False, error_type=r.error_type or "vocabulary")
            if picked.lower() in ARTICLES and expected.lower() in ARTICLES:
                result.error_type = "gender_article"

    elif ex_type in ("translate", "type_answer"):
        text = answer.get("text")
        if text is None and isinstance(answer.get("tokens"), list):
            text = " ".join(str(t) for t in answer["tokens"])
        result = best_match(str(text or ""), payload["answers"])
        if not (text or "").strip():
            result = GradeResult(False, error_type="missing_word")

    elif ex_type == "match_pairs":
        mistakes = int(answer.get("mistakes") or 0)
        result = GradeResult(mistakes == 0, error_type=None if mistakes == 0 else "vocabulary")

    else:
        raise ValueError(f"unknown exercise type {ex_type}")

    result.correct_answer = correct_answer
    if not result.correct and result.feedback is None:
        result.feedback = ERROR_HINTS.get(result.error_type)
    return result


ERROR_HINTS = {
    "gender_article": "Check the article: is the noun masculine (el/un) or feminine (la/una)?",
    "agreement": "Adjectives match the noun: -o for masculine, -a for feminine.",
    "verb_form": "Check the verb ending: it changes with who is doing the action.",
    "word_order": "All the right words, but the order is off.",
    "missing_word": "Looks like a word is missing.",
    "extra_word": "There's an extra word in there.",
}
