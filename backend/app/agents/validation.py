"""Deterministic validation of LLM-generated exercises, then conversion into the same payload
format as seeded exercises (so the lesson player and grader treat them identically).

An LLM is never trusted to be self-consistent: we check that the answer is among the choices, the
blank exists exactly once, pairs are unique, concepts are real, and (the grounding check) that the
Spanish only uses words the learner has been taught.
"""
import random
import re
from dataclasses import dataclass

from app.agents.schemas import GeneratedExercise
from app.seed.builder import tile_tokens
from app.services.exercise_types import DEFAULT_PROMPTS
from app.services.grading import grade, normalize, strip_accents, tokens

MAX_UNKNOWN_WORDS = 1  # proper names, a harmless new word


@dataclass
class Converted:
    type: str
    prompt: str
    payload: dict
    difficulty: int
    concepts: list[str]
    rationale: str


def _spanish_texts(g: GeneratedExercise) -> list[str]:
    if g.type == "match_pairs":
        return [p.spanish for p in g.pairs]
    if g.type == "fill_blank":
        return [g.sentence_with_blank.replace("___", g.answer)]
    if g.type == "multiple_choice":
        return [g.answer, *g.choices]
    if g.direction == "es_to_en":
        return [g.source_text]
    return [g.answer, *g.accepted_answers]


_INSTRUCTION_PREFIX = re.compile(
    r"^\s*(translate|type|write|choose|select|pick|fill|english|spanish|meaning|sentence)\b[^:]{0,60}:\s*",
    re.IGNORECASE,
)
_QUOTES = "'\"“”‘’«»"


def clean_text(text: str) -> str:
    """Strip instruction prefixes and wrapping quotes an LLM sometimes adds to raw phrases."""
    t = _INSTRUCTION_PREFIX.sub("", text.strip())
    t = re.sub(r"\s+[—–-]\s+(fill|type|choose|write)\b.*$", "", t, flags=re.IGNORECASE)
    return t.strip().strip(_QUOTES).strip()


def validate(
    g: GeneratedExercise, known_concepts: set[str], vocab: set[str], lexicon_emoji: dict[str, str]
) -> tuple[Converted | None, str | None]:
    g.source_text = clean_text(g.source_text)
    g.answer = clean_text(g.answer)
    concepts = [c for c in g.concept_keys if c in known_concepts]
    if not concepts:
        return None, f"unknown concept keys {g.concept_keys}"
    if not 1 <= g.difficulty <= 3:
        g.difficulty = 2

    unknown = sorted({
        t for text in _spanish_texts(g) for t in tokens(text) if strip_accents(t) not in vocab
    })
    if len(unknown) > MAX_UNKNOWN_WORDS:
        return None, f"uses words the learner hasn't been taught: {unknown[:5]}"

    rng = random.Random(hash(g.answer) & 0xFFFF)
    try:
        if g.type == "multiple_choice":
            choices = list(dict.fromkeys(c.strip() for c in g.choices if c.strip()))
            if g.answer not in choices:
                choices = [g.answer, *choices]
            choices = choices[:3] if g.answer in choices[:3] else [g.answer, *choices[:2]]
            if len(choices) < 2:
                return None, "multiple_choice needs at least 2 distinct choices"
            rng.shuffle(choices)
            payload = {
                "question": f"Which one of these is “{g.source_text}”?",
                "choices": [{"text": c, "emoji": lexicon_emoji.get(normalize(c))} for c in choices],
                "answer": choices.index(g.answer),
                "speak": g.answer,
            }
            prompt = "Select the correct option"

        elif g.type == "fill_blank":
            if g.sentence_with_blank.count("___") != 1:
                return None, "fill_blank sentence must contain exactly one ___"
            choices = list(dict.fromkeys([g.answer, *[c for c in g.choices if c != g.answer]]))[:3]
            if len(choices) < 2:
                return None, "fill_blank needs at least 2 distinct choices"
            rng.shuffle(choices)
            payload = {"sentence": g.sentence_with_blank, "translation": g.source_text, "choices": choices,
                       "answer": g.answer}
            prompt = DEFAULT_PROMPTS["fill_blank"]

        elif g.type in ("translate", "type_answer"):
            if not g.source_text.strip() or not g.answer.strip():
                return None, "missing source_text or answer"
            src, tgt = ("es", "en") if g.direction == "es_to_en" else ("en", "es")
            answers = list(dict.fromkeys([g.answer, *g.accepted_answers]))
            payload = {"source": g.source_text, "source_lang": src, "target_lang": tgt, "answers": answers}
            if g.type == "translate":
                answer_tiles = tile_tokens(g.answer)
                lowered = {t.lower() for t in answer_tiles}
                distractors = [d for d in dict.fromkeys(g.choices) if d.lower() not in lowered and " " not in d]
                bank = answer_tiles + distractors[:4]
                rng.shuffle(bank)
                payload["bank"] = bank
                prompt = f"Write this in {'English' if tgt == 'en' else 'Spanish'}"
            else:
                prompt = f"Type this in {'English' if tgt == 'en' else 'Spanish'}"

        elif g.type == "match_pairs":
            pairs = [(p.spanish.strip(), p.english.strip()) for p in g.pairs if p.spanish.strip() and p.english.strip()]
            if len({p[0].lower() for p in pairs}) != len(pairs) or len({p[1].lower() for p in pairs}) != len(pairs):
                return None, "match_pairs has duplicate items"
            if not 3 <= len(pairs) <= 6:
                return None, "match_pairs needs 3-6 pairs"
            payload = {"pairs": [list(p) for p in pairs]}
            prompt = DEFAULT_PROMPTS["match_pairs"]
        else:
            return None, f"unknown type {g.type}"
    except (ValueError, KeyError, IndexError) as e:
        return None, f"malformed exercise: {e}"

    # Self-check: the canonical answer must grade as correct through the real grader.
    probe = {
        "multiple_choice": lambda: {"choice": payload.get("answer")},
        "fill_blank": lambda: {"choice": g.answer},
        "translate": lambda: {"tokens": tile_tokens(g.answer)},
        "type_answer": lambda: {"text": g.answer},
        "match_pairs": lambda: {"mistakes": 0},
    }[g.type]()
    if not grade(g.type, payload, probe).correct:
        return None, "the answer does not grade as correct against its own payload"

    return Converted(g.type, prompt, payload, g.difficulty, concepts, g.rationale), None


def validate_all(items: list[GeneratedExercise], known_concepts: set[str], vocab: set[str],
                 lexicon_emoji: dict[str, str]) -> tuple[list[Converted], list[str]]:
    ok, errors, seen = [], [], set()
    for i, g in enumerate(items):
        key = (g.type, normalize(g.source_text or g.sentence_with_blank or g.answer))
        if key in seen:
            errors.append(f"#{i + 1}: duplicate of an earlier exercise")
            continue
        conv, err = validate(g, known_concepts, vocab, lexicon_emoji)
        if conv:
            seen.add(key)
            ok.append(conv)
        else:
            errors.append(f"#{i + 1} ({g.type}): {err}")
    return ok, errors
