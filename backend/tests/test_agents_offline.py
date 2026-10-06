"""Agent-layer logic that must hold without any LLM: validation/grounding and the rules fallback."""
from app.agents import fallback
from app.agents.schemas import GeneratedExercise, Pair
from app.agents.validation import clean_text, validate, validate_all
from app.models import User
from app.services import guests, simulator

KNOWN = {"grammar.gender_articles", "vocab.food", "vocab.people"}
VOCAB = {"el", "la", "un", "una", "y", "pan", "leche", "cafe", "nino", "nina", "mujer", "hombre", "manzana"}


def gen(**kw) -> GeneratedExercise:
    base = dict(type="translate", concept_keys=["grammar.gender_articles"], direction="en_to_es",
                source_text="The bread and the milk", answer="El pan y la leche", accepted_answers=[],
                choices=["una", "hombre"], sentence_with_blank="", pairs=[], difficulty=2, rationale="r")
    base.update(kw)
    return GeneratedExercise(**base)


def test_valid_translate_becomes_word_bank_exercise():
    conv, err = validate(gen(), KNOWN, VOCAB, {})
    assert err is None and conv.type == "translate"
    assert set(["El", "pan", "y", "la", "leche"]) <= set(conv.payload["bank"])


def test_grounding_rejects_untaught_vocabulary():
    conv, err = validate(gen(answer="El perro come la carne rápidamente"), KNOWN, VOCAB, {})
    assert conv is None and "taught" in err


def test_fill_blank_needs_single_gap_and_answer_in_choices():
    bad = gen(type="fill_blank", sentence_with_blank="___ pan y ___ leche", answer="El", choices=["El", "La"])
    assert validate(bad, KNOWN, VOCAB, {})[0] is None
    good = gen(type="fill_blank", sentence_with_blank="___ pan y la leche", answer="El", choices=["La", "Un"],
               source_text="The bread and the milk")
    conv, err = validate(good, KNOWN, VOCAB, {})
    assert err is None and "El" in conv.payload["choices"]


def test_unknown_concepts_and_duplicates_rejected():
    ok, errors = validate_all([gen(concept_keys=["made.up"]), gen(), gen()], KNOWN, VOCAB, {})
    assert len(ok) == 1 and len(errors) == 2


def test_match_pairs_duplicates_rejected():
    pairs = [Pair(spanish="el pan", english="the bread"), Pair(spanish="el pan", english="bread"),
             Pair(spanish="la leche", english="the milk")]
    assert validate(gen(type="match_pairs", pairs=pairs), KNOWN, VOCAB, {})[0] is None


def test_clean_text_strips_llm_instructions():
    assert clean_text("Translate to Spanish: 'The boy and the girl'") == "The boy and the girl"
    assert clean_text("English: 'The coffee and the milk' — fill the missing Spanish word") == "The coffee and the milk"
    assert clean_text("la niña") == "la niña"


def test_rules_fallback_follows_injected_profile(db):
    user = guests.create_guest(db)
    simulator.inject(db, user, "accents", n=14)
    db.flush()
    diagnosis = fallback.diagnose(db, user)
    assert any("accent" in p for p in diagnosis["error_patterns"])
    plan, ids, message = fallback.plan_and_pick(db, user, diagnosis)
    assert ids and message
    db.rollback()


def test_demo_learner_history_points_at_gender(db):
    user: User = guests.create_guest(db)
    diagnosis = fallback.diagnose(db, user)
    assert "grammar.gender_articles" in [w["concept_key"] for w in diagnosis["weak_concepts"]]
    db.rollback()


def test_explicit_request_overrides_planner_focus():
    """'Practise animals' must produce an animals session even if the planner preferred other topics."""
    from app.agents.pipeline import _sanitize_plan
    from app.agents.schemas import LearnerDiagnosis, PlanItem, PracticePlan

    planned = PracticePlan(
        items=[PlanItem(concept_key="grammar.gender_articles", exercise_count=4,
                        exercise_types=["fill_blank"], difficulty=2, reason="weakest")],
        review_concepts=["spelling.accents"], strategy="s", learner_message="Smarto: hi",
    )
    diagnosis = LearnerDiagnosis(weak_concepts=[], strengths=[], error_patterns=[], overall_summary="", confidence=0.5)
    known = {"grammar.gender_articles", "vocab.animals", "spelling.accents"}
    plan = _sanitize_plan(planned, known, diagnosis, requested=["vocab.animals"])
    assert [i.concept_key for i in plan.items] == ["vocab.animals"]
    assert plan.review_concepts == []
    assert plan.learner_message == "hi"
