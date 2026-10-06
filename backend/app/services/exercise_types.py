"""The five exercise types and their payload contracts.

Internal payloads (stored in exercises.payload) contain the answers. `public_payload` produces
the client view, which never includes the answer (except match_pairs, where matching happens
client-side tap by tap, like in Duolingo, and the server only records the mistake count).

    multiple_choice  {"question", "choices": [{"text", "emoji"?}], "answer": int}
    translate        {"source", "source_lang", "target_lang", "bank": [str], "answers": [str]}
    match_pairs      {"pairs": [[target, source], ...]}
    fill_blank       {"sentence": "___ manzana", "translation", "choices": [str], "answer": str}
    type_answer      {"source", "source_lang", "target_lang", "answers": [str]}
"""
import random

EXERCISE_TYPES = ("multiple_choice", "translate", "match_pairs", "fill_blank", "type_answer")

# Recognition = pick the right thing; production = build/type it yourself. The learner model
# tracks both separately so the tutor can tell "knows it when sees it" from "can produce it".
RECOGNITION_TYPES = {"multiple_choice", "match_pairs", "fill_blank"}
PRODUCTION_TYPES = {"translate", "type_answer"}

DEFAULT_PROMPTS = {
    "multiple_choice": "Select the correct image",
    "translate": "Write this in {lang}",
    "match_pairs": "Select the matching pairs",
    "fill_blank": "Fill in the blank",
    "type_answer": "Type this in {lang}",
}

LANG_NAMES = {"es": "Spanish", "en": "English"}


def public_payload(ex_type: str, payload: dict, rng_seed: int | None = None) -> dict:
    rng = random.Random(rng_seed)
    if ex_type == "multiple_choice":
        choices = [{"text": c["text"]} for c in payload["choices"]]
        return {"question": payload["question"], "choices": choices, "speak": payload.get("speak")}
    if ex_type == "translate":
        return {
            "source": payload["source"],
            "source_lang": payload["source_lang"],
            "target_lang": payload["target_lang"],
            "bank": payload["bank"],
        }
    if ex_type == "match_pairs":
        left = [{"id": i, "text": p[0]} for i, p in enumerate(payload["pairs"])]
        right = [{"id": i, "text": p[1]} for i, p in enumerate(payload["pairs"])]
        rng.shuffle(left)
        rng.shuffle(right)
        return {"left": left, "right": right}
    if ex_type == "fill_blank":
        return {
            "sentence": payload["sentence"],
            "translation": payload.get("translation"),
            "choices": payload["choices"],
        }
    if ex_type == "type_answer":
        return {
            "source": payload["source"],
            "source_lang": payload["source_lang"],
            "target_lang": payload["target_lang"],
        }
    raise ValueError(f"unknown exercise type {ex_type}")


def display_answer(ex_type: str, payload: dict) -> str:
    """The canonical correct answer as shown in the red feedback bar."""
    if ex_type == "multiple_choice":
        return payload["choices"][payload["answer"]]["text"]
    if ex_type in ("translate", "type_answer"):
        return payload["answers"][0]
    if ex_type == "fill_blank":
        return payload["sentence"].replace("___", payload["answer"])
    if ex_type == "match_pairs":
        return ", ".join(f"{a} = {b}" for a, b in payload["pairs"])
    raise ValueError(ex_type)


def speakable_text(ex_type: str, payload: dict) -> str | None:
    """Target-language text the client can read aloud with TTS."""
    if ex_type == "multiple_choice":
        return payload.get("speak")
    if ex_type in ("translate", "type_answer") and payload["source_lang"] == "es":
        return payload["source"]
    if ex_type == "fill_blank":
        return payload["sentence"].replace("___", payload["answer"])
    return None
