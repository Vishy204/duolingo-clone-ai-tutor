from app.services.grading import compare_text, grade, normalize


def test_normalize_handles_case_punctuation_contractions():
    assert normalize("¿Dónde está el gato?") == "dónde está el gato"
    assert normalize("I don't have a dog.") == "i do not have a dog"


def test_exact_and_alternative_answers():
    payload = {"source": "Yo como pan", "source_lang": "es", "target_lang": "en",
               "answers": ["I eat bread", "I am eating bread"]}
    assert grade("type_answer", payload, {"text": "i am eating bread"}).correct
    assert grade("type_answer", payload, {"text": "I eat bread!"}).correct


def test_missing_accent_is_accepted_as_typo():
    r = compare_text("adios", "adiós")
    assert r.correct and r.typo and r.error_type == "accent"


def test_article_swap_is_a_gender_error_not_a_typo():
    r = compare_text("la pan", "el pan")
    assert not r.correct and r.error_type == "gender_article"
    r = compare_text("una café", "un café")
    assert not r.correct and r.error_type == "gender_article"


def test_word_order_and_missing_word():
    assert compare_text("pan como yo", "yo como pan").error_type == "word_order"
    assert compare_text("yo pan", "yo como pan").error_type == "missing_word"


def test_verb_form_and_agreement():
    assert compare_text("yo come pan", "yo como pan").error_type == "verb_form"
    assert compare_text("la manzana es rojo", "la manzana es roja").error_type == "agreement"


def test_one_letter_typo_in_content_word():
    r = compare_text("la manzna", "la manzana")
    assert r.correct and r.typo


def test_word_bank_tokens():
    payload = {"source": "The apple, please", "source_lang": "en", "target_lang": "es",
               "bank": [], "answers": ["La manzana, por favor"]}
    assert grade("translate", payload, {"tokens": ["La", "manzana", "por", "favor"]}).correct


def test_fill_blank_article():
    payload = {"sentence": "___ manzana", "translation": "The apple", "choices": ["La", "El"], "answer": "La"}
    r = grade("fill_blank", payload, {"choice": "El"})
    assert not r.correct and r.error_type == "gender_article"
