"""Learning-path state: which nodes are completed / active / locked for a learner."""
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import Course, Lesson, Skill, Unit, User, UserSkillProgress


@dataclass
class NodeState:
    skill: Skill
    status: str  # completed | active | locked
    lessons_total: int
    lessons_completed: int
    crowns: int
    is_legendary: bool
    next_lesson_id: int | None


def load_course(db: Session, course_id: int) -> Course:
    return db.scalar(
        select(Course)
        .where(Course.id == course_id)
        .options(selectinload(Course.units).selectinload(Unit.skills).selectinload(Skill.lessons))
    )


def progress_map(db: Session, user_id: int) -> dict[int, UserSkillProgress]:
    rows = db.scalars(select(UserSkillProgress).where(UserSkillProgress.user_id == user_id)).all()
    return {r.skill_id: r for r in rows}


def compute_path(db: Session, user: User) -> tuple[Course, dict[int, NodeState]]:
    course = load_course(db, user.course_id)
    prog = progress_map(db, user.id)
    states: dict[int, NodeState] = {}
    gate_open = True  # every node before this one is completed
    for unit in course.units:
        unit_lessons_done = True
        for skill in unit.skills:
            p = prog.get(skill.id)
            total = len(skill.lessons)
            done = p.lessons_completed if p else 0
            if skill.kind == "lesson":
                completed = done >= total
                status = "completed" if completed else ("active" if gate_open else "locked")
                unit_lessons_done = unit_lessons_done and completed
                gate_open = gate_open and completed
            elif skill.kind == "chest":
                claimed = bool(p and p.completed_at)
                status = "completed" if claimed else ("active" if gate_open else "locked")
            else:  # trophy marks the end of a unit
                status = "completed" if unit_lessons_done and gate_open else "locked"
            # Next lesson to play; once a skill is completed, replays cycle through its lessons.
            next_lesson = skill.lessons[done % total].id if skill.lessons else None
            states[skill.id] = NodeState(
                skill=skill,
                status=status,
                lessons_total=total,
                lessons_completed=min(done, total),
                crowns=p.crowns if p else 0,
                is_legendary=bool(p and p.is_legendary),
                next_lesson_id=next_lesson,
            )
    return course, states


def studied_lesson_ids(db: Session, user: User) -> list[int]:
    """Lessons the learner has already completed (practice only draws from what was taught)."""
    _, states = compute_path(db, user)
    ids: list[int] = []
    first_active: list[int] = []
    for st in states.values():
        ids.extend(lesson.id for lesson in st.skill.lessons[: st.lessons_completed])
        if st.status == "active" and st.skill.lessons and not first_active:
            first_active = [st.skill.lessons[0].id]
    return ids or first_active


def lesson_with_skill(db: Session, lesson_id: int) -> Lesson | None:
    return db.scalar(select(Lesson).where(Lesson.id == lesson_id).options(selectinload(Lesson.skill)))
