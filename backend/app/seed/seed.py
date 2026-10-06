"""Idempotent database seeding: content, achievements and leaderboard learners.

Runs on startup (the Render free tier has an ephemeral disk, so the DB may be fresh on boot).
`python -m app.seed.seed --reset` rebuilds from scratch locally.
"""
import sys

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import Base, SessionLocal, engine
from app.models import Achievement, Concept, Course, Exercise, Lesson, Lexeme, Skill, Unit, User
from app.seed.builder import build_lesson_exercises, tile_tokens
from app.seed.content_es import ACHIEVEMENTS, BOTS, CONCEPTS, COURSE


def seed_content(db: Session) -> Course:
    existing = db.scalar(select(Course).where(Course.slug == COURSE["slug"]))
    if existing:
        _sync_display(db, existing)
        return existing

    concepts = {}
    for key, name, category, tip in CONCEPTS:
        c = Concept(key=key, name=name, category=category, tip=tip)
        db.add(c)
        concepts[key] = c

    course = Course(
        slug=COURSE["slug"], title=COURSE["title"], from_lang=COURSE["from_lang"],
        to_lang=COURSE["to_lang"], flag=COURSE["flag"],
    )
    db.add(course)
    db.flush()

    # Token pools for word-bank distractors, collected over the whole course.
    es_pool, en_pool = [], []
    for unit in COURSE["units"]:
        for skill in unit["skills"]:
            for lesson in skill.get("lessons", []):
                for s in lesson["sentences"]:
                    es_pool += tile_tokens(s["es"][0])
                    en_pool += tile_tokens(s["en"][0])
    es_pool, en_pool = list(dict.fromkeys(es_pool)), list(dict.fromkeys(en_pool))
    # Distractor tiles prefer words the learner has already met (falls back to the whole course).
    es_seen: list[str] = []
    en_seen: list[str] = []

    prior_words: list[tuple] = []
    for u_pos, unit_data in enumerate(COURSE["units"], 1):
        unit = Unit(
            course_id=course.id, position=u_pos, title=unit_data["title"],
            description=unit_data["description"], color=unit_data["color"], guidebook=unit_data["guidebook"],
        )
        db.add(unit)
        db.flush()
        for s_pos, skill_data in enumerate(unit_data["skills"], 1):
            skill = Skill(
                unit_id=unit.id, position=s_pos, title=skill_data["title"], icon=skill_data["icon"],
                kind=skill_data.get("kind", "lesson"),
            )
            db.add(skill)
            db.flush()
            for l_pos, lesson_data in enumerate(skill_data.get("lessons", []), 1):
                lesson = Lesson(skill_id=skill.id, position=l_pos, title=f"{skill_data['title']} {l_pos}")
                db.add(lesson)
                db.flush()
                for es, en, emoji, cs in lesson_data["words"]:
                    lex = Lexeme(course_id=course.id, lesson_id=lesson.id, text=es, translation=en, emoji=emoji)
                    lex.concepts = [concepts[k] for k in dict.fromkeys(cs + skill_data["concepts"][:1])]
                    db.add(lex)
                for snt in lesson_data["sentences"]:
                    es_seen += [t for t in tile_tokens(snt["es"][0]) if t not in es_seen]
                    en_seen += [t for t in tile_tokens(snt["en"][0]) if t not in en_seen]
                items = build_lesson_exercises(
                    lesson_data, skill_data["concepts"], prior_words,
                    es_seen if len(es_seen) > 12 else es_pool, en_seen if len(en_seen) > 12 else en_pool,
                    seed=lesson.id * 7919,
                )
                for e_pos, item in enumerate(items, 1):
                    ex = Exercise(
                        lesson_id=lesson.id, position=e_pos, type=item["type"], prompt=item["prompt"],
                        payload=item["payload"], difficulty=item["difficulty"], source="seed",
                    )
                    ex.concepts = [concepts[k] for k in item["concepts"] if k in concepts]
                    db.add(ex)
                prior_words += lesson_data["words"]
    db.flush()
    return course


def _sync_display(db: Session, course: Course) -> None:
    """Keep presentational fields (unit colours) in step with the authored content on existing DBs."""
    units = {u.position: u for u in db.scalars(select(Unit).where(Unit.course_id == course.id))}
    for u_pos, unit_data in enumerate(COURSE["units"], 1):
        if u_pos in units:
            units[u_pos].color = unit_data["color"]


def seed_achievements(db: Session) -> None:
    have = {a.key: a for a in db.scalars(select(Achievement))}
    for key, title, desc, icon, color, metric, threshold in ACHIEVEMENTS:
        if key in have:  # keep names and descriptions current (e.g. after a rename)
            have[key].title, have[key].description = title, desc
        else:
            db.add(Achievement(key=key, title=title, description=desc, icon=icon, color=color,
                               metric=metric, threshold=threshold))


def seed_bots(db: Session, course: Course) -> None:
    have = set(db.scalars(select(User.username).where(User.is_bot.is_(True))))
    for username, name, color, daily_xp in BOTS:
        if username in have:
            continue
        db.add(User(
            username=username, display_name=name, avatar_color=color, is_guest=False, is_bot=True,
            course_id=course.id, total_xp=daily_xp * 40, streak_count=daily_xp // 3,
            longest_streak=daily_xp // 2, settings={"daily_xp": daily_xp},
        ))


def run(reset: bool = False) -> None:
    import app.models  # noqa: F401  (register tables)

    if reset:
        Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        course = seed_content(db)
        seed_achievements(db)
        seed_bots(db, course)
        db.commit()


if __name__ == "__main__":
    run(reset="--reset" in sys.argv)
    with SessionLocal() as db:
        print("courses", db.query(Course).count(), "lessons", db.query(Lesson).count(),
              "exercises", db.query(Exercise).count(), "lexemes", db.query(Lexeme).count())
