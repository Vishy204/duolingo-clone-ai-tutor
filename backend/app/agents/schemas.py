"""Structured outputs for every agent. These are the contracts between agents (and with the app):
the SDK enforces them via `output_type`, so the pipeline passes typed objects, not prose."""
from typing import Literal

from pydantic import BaseModel, Field

ExerciseType = Literal["multiple_choice", "translate", "match_pairs", "fill_blank", "type_answer"]


# ---------------------------------------------------------------- Learner Analyst

class WeakConcept(BaseModel):
    concept_key: str = Field(description="Exact concept key from the tools, e.g. grammar.gender_articles")
    severity: Literal["high", "medium", "low"]
    weakness_mode: Literal["recognition", "production", "both"] = Field(
        description="recognition = fails when choosing; production = fails when typing/building; both"
    )
    evidence: str = Field(description="Concrete numbers/examples from the data, e.g. '5 of 8 article errors'")
    likely_misconception: str = Field(description="What the learner probably believes that is wrong")


class LearnerDiagnosis(BaseModel):
    weak_concepts: list[WeakConcept] = Field(description="Most important first, at most 4")
    strengths: list[str] = Field(description="Concept keys the learner is solid on")
    error_patterns: list[str] = Field(description="Short observations about how they make mistakes")
    overall_summary: str = Field(description="2-3 sentences for the tutor dashboard")
    confidence: float = Field(description="0-1, how much data supports this diagnosis")


# ---------------------------------------------------------------- Curriculum Planner

class PlanItem(BaseModel):
    concept_key: str
    exercise_count: int = Field(description="1-4 new exercises for this concept")
    exercise_types: list[ExerciseType] = Field(description="Which formats to use, best first")
    difficulty: int = Field(description="1 easy - 3 hard")
    reason: str = Field(description="Why this concept, why these formats")


class PracticePlan(BaseModel):
    items: list[PlanItem] = Field(description="2-4 items, total exercise_count between 6 and 10")
    review_concepts: list[str] = Field(description="Concept keys due for spaced review (light touch)")
    strategy: str = Field(description="One sentence: the pedagogical strategy behind this plan")
    learner_message: str = Field(
        description="Message from Duo the owl to the learner, max 200 chars, second person, warm and "
        "specific, e.g. 'You keep mixing up el/la, so I made you 4 gender drills, now with typing!'"
    )


# ---------------------------------------------------------------- Exercise Generator

class Pair(BaseModel):
    spanish: str
    english: str


class GeneratedExercise(BaseModel):
    type: ExerciseType
    concept_keys: list[str]
    direction: Literal["es_to_en", "en_to_es"] = Field(
        description="Translation direction. For multiple_choice/fill_blank/match_pairs use en_to_es."
    )
    source_text: str = Field(
        description="multiple_choice: the English meaning asked for; translate/type_answer: the sentence "
        "to translate; fill_blank: the English translation of the full sentence; match_pairs: empty"
    )
    answer: str = Field(description="The single correct answer (for fill_blank: the missing word)")
    accepted_answers: list[str] = Field(description="Other fully correct variants (may be empty)")
    choices: list[str] = Field(
        description="multiple_choice: 3 options incl. the answer; fill_blank: 3 options incl. the answer; "
        "translate: 3-4 distractor words for the word bank; others: empty"
    )
    sentence_with_blank: str = Field(description="fill_blank only: Spanish sentence with ___ for the gap, else empty")
    pairs: list[Pair] = Field(description="match_pairs only: 4-5 pairs, else empty")
    difficulty: int
    rationale: str = Field(description="Why this exercise targets the learner's weakness")


class GeneratedSet(BaseModel):
    exercises: list[GeneratedExercise]


# ---------------------------------------------------------------- Explainer / guardrails

class Explanation(BaseModel):
    headline: str = Field(description="Max 8 words, e.g. 'Pan is masculine: el pan'")
    explanation: str = Field(description="1-2 short sentences, friendly, specific to their answer")
    example_es: str
    example_en: str


class TopicVerdict(BaseModel):
    allowed: bool
    category: Literal["language_learning", "app_help", "small_talk", "off_topic", "prompt_injection", "abusive"]
    reason: str
