"""Function tools exposed to the agents. Each one is a thin, read-only wrapper over learner_data,
scoped to the learner in the run context. Docstrings are what the model sees."""
import json

from agents import RunContextWrapper, function_tool

from app.agents import learner_data
from app.agents.context import TutorContext
from app.models import User


def _with_user(ctx: RunContextWrapper[TutorContext], fn, *args):
    with ctx.context.session_factory() as db:
        user = db.get(User, ctx.context.user_id)
        return json.dumps(fn(db, user, *args), ensure_ascii=False)


@function_tool
def get_concept_mastery(ctx: RunContextWrapper[TutorContext]) -> str:
    """Per-concept mastery for this learner (0-1, weakest first), with attempt counts, overall,
    recognition (choosing) and production (typing/building) accuracy, and whether it's due for review."""
    return _with_user(ctx, learner_data.concept_mastery)


@function_tool
def get_recent_mistakes(ctx: RunContextWrapper[TutorContext], limit: int = 15) -> str:
    """The learner's most recent wrong answers and typos: exercise type, concepts, the task,
    what they answered, the correct answer and the classified error type.

    Args:
        limit: how many mistakes to return (max 30).
    """
    return _with_user(ctx, learner_data.recent_mistakes, max(1, min(limit, 30)))


@function_tool
def get_error_breakdown(ctx: RunContextWrapper[TutorContext]) -> str:
    """Aggregates over the last ~150 attempts: counts per error type (gender_article, accent,
    verb_form, word_order...), error rate per concept, and recognition vs production accuracy."""
    return _with_user(ctx, learner_data.error_breakdown)


@function_tool
def get_session_history(ctx: RunContextWrapper[TutorContext]) -> str:
    """The learner's last few lessons/practices with accuracy and mistakes (to see trends)."""
    return _with_user(ctx, learner_data.session_history)


@function_tool
def get_course_lexicon(ctx: RunContextWrapper[TutorContext], concept_keys: list[str]) -> str:
    """Vocabulary and example sentences the learner has ALREADY been taught, prioritising the given
    concepts. Exercises must only use these words.

    Args:
        concept_keys: concepts to prioritise, e.g. ["grammar.gender_articles"].
    """
    with ctx.context.session_factory() as db:
        user = db.get(User, ctx.context.user_id)
        return json.dumps(
            {
                "words": learner_data.taught_lexicon(db, user, concept_keys, limit=40),
                "sentences": learner_data.taught_sentences(db, user, concept_keys, limit=15),
            },
            ensure_ascii=False,
        )


ANALYST_TOOLS = [get_concept_mastery, get_error_breakdown, get_recent_mistakes, get_session_history]
GENERATOR_TOOLS = [get_course_lexicon]
