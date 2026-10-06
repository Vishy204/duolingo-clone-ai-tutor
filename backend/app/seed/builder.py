"""Turns authored lesson content (words + sentences) into a varied exercise sequence.

Deterministic (seeded RNG per lesson) so re-seeding produces identical lessons.
"""
import random
import re

_WORD = re.compile(r"[\wáéíóúñü']+", re.IGNORECASE)


def tile_tokens(sentence: str) -> list[str]:
    return _WORD.findall(sentence)


def build_lesson_exercises(
    lesson: dict,
    skill_concepts: list[str],
    prior_words: list[tuple],
    es_token_pool: list[str],
    en_token_pool: list[str],
    seed: int,
) -> list[dict]:
    """Returns a list of {type, prompt, payload, difficulty, concepts}."""
    rng = random.Random(seed)
    words = lesson["words"]
    sentences = lesson["sentences"]
    out: list[dict] = []

    def concepts_for(extra: list[str]) -> list[str]:
        base = [c for c in skill_concepts if c.startswith("vocab.")][:1]
        return list(dict.fromkeys(base + extra))

    # 1) Picture multiple choice for each new word ("Which one of these is 'the apple'?")
    mc_items = []
    for es, en, emoji, cs in words[:3]:
        others = list({w[2]: w for w in words + prior_words if w[0] != es and w[2] != emoji}.values())
        rng.shuffle(others)
        choices = [{"text": es, "emoji": emoji}] + [{"text": w[0], "emoji": w[2]} for w in others[:2]]
        rng.shuffle(choices)
        answer = next(i for i, c in enumerate(choices) if c["text"] == es)
        mc_items.append({
            "type": "multiple_choice",
            "prompt": "Select the correct image",
            "payload": {"question": f"Which one of these is “{en}”?", "choices": choices, "answer": answer, "speak": es},
            "difficulty": 1,
            "concepts": concepts_for(cs),
        })

    # 2) Match pairs with all the lesson's words (topped up from earlier lessons)
    pair_words = list(words)
    extra = [w for w in prior_words if w not in pair_words]
    rng.shuffle(extra)
    pair_words += extra[: max(0, 5 - len(pair_words))]
    match = {
        "type": "match_pairs",
        "prompt": "Select the matching pairs",
        "payload": {"pairs": [[w[0], w[1]] for w in pair_words[:5]]},
        "difficulty": 1,
        "concepts": concepts_for([c for w in pair_words[:5] for c in w[3]]),
    }

    # 3) Translations (alternate direction) and fill-in-the-blanks from sentences
    translations, blanks = [], []
    for i, s in enumerate(sentences):
        to_english = i % 2 == 0
        source = s["es"][0] if to_english else s["en"][0]
        answers = s["en"] if to_english else s["es"]
        answer_tiles = tile_tokens(answers[0])
        pool = en_token_pool if to_english else es_token_pool
        lowered = {t.lower() for t in answer_tiles}
        distractors = list(dict.fromkeys(t for t in pool if t.lower() not in lowered))
        rng.shuffle(distractors)
        bank = answer_tiles + distractors[: max(3, 7 - len(answer_tiles))]
        rng.shuffle(bank)
        translations.append({
            "type": "translate",
            "prompt": "Write this in English" if to_english else "Write this in Spanish",
            "payload": {
                "source": source, "source_lang": "es" if to_english else "en",
                "target_lang": "en" if to_english else "es", "bank": bank, "answers": answers,
            },
            "difficulty": 2 if to_english else 3,
            "concepts": concepts_for(s["c"]),
        })
        if s.get("blank"):
            word, wrong = s["blank"]
            sentence = s["es"][0]
            blanked = re.sub(rf"(?<![\wáéíóúñ]){re.escape(word)}(?![\wáéíóúñ])", "___", sentence, count=1)
            if "___" in blanked:
                choices = [word, *wrong]
                rng.shuffle(choices)
                blanks.append({
                    "type": "fill_blank",
                    "prompt": "Fill in the blank",
                    "payload": {"sentence": blanked, "translation": s["en"][0], "choices": choices, "answer": word},
                    "difficulty": 2,
                    "concepts": concepts_for(s["c"]),
                })

    # 4) Type-the-answer: produce a word, and the last sentence, from memory
    typed = []
    if words:
        es, en, _, cs = words[-1]
        typed.append({
            "type": "type_answer",
            "prompt": "Type this in Spanish",
            "payload": {"source": en, "source_lang": "en", "target_lang": "es", "answers": [es]},
            "difficulty": 3,
            "concepts": concepts_for(cs),
        })
    if sentences:
        s = sentences[-1]
        typed.append({
            "type": "type_answer",
            "prompt": "Type this in English",
            "payload": {"source": s["es"][0], "source_lang": "es", "target_lang": "en", "answers": s["en"]},
            "difficulty": 2,
            "concepts": concepts_for(s["c"]),
        })

    # Interleave: recognise first, then build, then produce.
    sequence = []
    sequence += mc_items[:2]
    sequence += translations[:1]
    sequence += blanks[:1]
    sequence += mc_items[2:]
    sequence.append(match)
    sequence += translations[1:2]
    sequence += blanks[1:2]
    sequence += translations[2:]
    sequence += blanks[2:3]
    sequence += typed
    return sequence[:12]
