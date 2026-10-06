"""Auth (guest), learner state, the learning path, profile, leaderboard, shop, settings."""
from fastapi import APIRouter, BackgroundTasks, Depends, Request
from sqlalchemy.orm import Session

from app.agents.pipeline import run_pipeline
from app.api.deps import current_user
from app.core.clock import user_now, user_today
from app.core.config import get_settings
from app.core.db import get_db
from app.core.rate_limit import client_ip, guest_limiter
from app.core.security import create_access_token
from app.models import User, UserSkillProgress
from app.schemas.api import GuestIn, SettingsIn
from app.services import achievements, guests, hearts, leaderboard, plans, progress, streaks, xp
from app.services.errors import GameError

router = APIRouter()


def user_state(db: Session, user: User) -> dict:
    hearts.regenerate(user)
    events = streaks.refresh(user)
    s = get_settings()
    nh = hearts.next_heart_at(user)
    return {
        "id": user.id,
        "display_name": user.display_name,
        "username": user.username,
        "avatar_color": user.avatar_color,
        "course": {"title": "Spanish", "flag": "🇪🇸"},
        "total_xp": user.total_xp,
        "gems": user.gems,
        "hearts": user.hearts,
        "max_hearts": s.max_hearts,
        "next_heart_at": nh.isoformat() if nh else None,
        "heart_regen_minutes": s.heart_regen_minutes,
        "refill_cost": s.refill_hearts_gem_cost,
        "streak": user.streak_count,
        "longest_streak": user.longest_streak,
        "streak_extended_today": streaks.is_extended_today(user),
        "streak_freezes": user.streak_freezes,
        "streak_events": events,
        "daily_goal_xp": user.daily_goal_xp,
        "xp_today": xp.xp_today(db, user),
        "today": user_today(user.clock_offset_days).isoformat(),
        "clock_offset_days": user.clock_offset_days,
        "settings": user.settings or {},
        "agents_enabled": s.agents_enabled,
        "demo_mode": s.demo_mode,
    }


@router.post("/auth/guest")
def create_guest(body: GuestIn, request: Request, background: BackgroundTasks, db: Session = Depends(get_db)):
    guest_limiter.check(client_ip(request))
    user = guests.create_guest(db, body.name)
    db.commit()
    # The demo learner arrives with history, so the tutor analyses it straight away.
    background.add_task(run_pipeline, user.id, "onboarding")
    return {"token": create_access_token(user.id), "user": user_state(db, user)}


@router.get("/me")
def me(user: User = Depends(current_user), db: Session = Depends(get_db)):
    state = user_state(db, user)
    db.commit()
    return state


@router.patch("/me/settings")
def update_settings(body: SettingsIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    if body.display_name:
        user.display_name = body.display_name.strip()
    if body.daily_goal_xp:
        user.daily_goal_xp = body.daily_goal_xp
    prefs = dict(user.settings or {})
    for key in ("sound", "dark_mode"):
        val = getattr(body, key)
        if val is not None:
            prefs[key] = val
    user.settings = prefs
    db.commit()
    return user_state(db, user)


@router.get("/path")
def path(user: User = Depends(current_user), db: Session = Depends(get_db)):
    course, states = progress.compute_path(db, user)
    plan = plans.latest_plan(db, user.id)
    units = []
    for unit in course.units:
        nodes = []
        for skill in unit.skills:
            st = states[skill.id]
            nodes.append({
                "id": skill.id, "title": skill.title, "icon": skill.icon, "kind": skill.kind,
                "status": st.status, "lessons_total": st.lessons_total, "lessons_completed": st.lessons_completed,
                "crowns": st.crowns, "is_legendary": st.is_legendary, "next_lesson_id": st.next_lesson_id,
            })
        units.append({
            "id": unit.id, "position": unit.position, "title": unit.title, "description": unit.description,
            "color": unit.color, "guidebook": unit.guidebook, "nodes": nodes,
        })
    return {
        "course": {"title": course.title, "flag": course.flag},
        "units": units,
        "duo_practice": _plan_card(plan),
    }


def _plan_card(plan) -> dict | None:
    if plan is None:
        return None
    return {
        "plan_id": plan.id, "status": plan.status, "engine": plan.engine, "summary": plan.summary,
        "focus_concepts": plan.focus_concepts, "exercise_count": len((plan.plan or {}).get("exercise_ids", [])),
        "created_at": plan.created_at.isoformat(),
    }


@router.post("/path/chest/{skill_id}")
def open_chest(skill_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    _, states = progress.compute_path(db, user)
    st = states.get(skill_id)
    if st is None or st.skill.kind != "chest":
        raise GameError("not_found", "Chest not found", 404)
    if st.status != "active":
        raise GameError("locked", "This chest is locked or already opened.", 409)
    gems = 15 + (skill_id * 7) % 20
    db.add(UserSkillProgress(user_id=user.id, skill_id=skill_id, lessons_completed=0, crowns=0,
                             is_legendary=False, completed_at=user_now(user.clock_offset_days)))
    user.gems += gems
    db.commit()
    return {"gems_awarded": gems, "gems": user.gems}


@router.get("/profile")
def profile(user: User = Depends(current_user), db: Session = Depends(get_db)):
    from app.agents.learner_data import concept_mastery

    m = achievements.metrics(db, user)
    return {
        "user": user_state(db, user),
        "stats": {**m, "joined": user.created_at.date().isoformat()},
        "achievements": achievements.list_for_user(db, user),
        "xp_history": xp.daily_history(db, user, 7),
        "active_days": xp.active_days(db, user, 35),
        "mastery": concept_mastery(db, user),
    }


@router.get("/quests")
def quests(user: User = Depends(current_user), db: Session = Depends(get_db)):
    return {"daily": achievements.daily_quests(db, user)}


@router.get("/leaderboard")
def get_leaderboard(user: User = Depends(current_user), db: Session = Depends(get_db)):
    board = leaderboard.weekly(db, user)
    db.commit()
    return board


@router.post("/shop/refill-hearts")
def refill_hearts(user: User = Depends(current_user), db: Session = Depends(get_db)):
    if not hearts.refill_with_gems(user):
        raise GameError("cannot_refill", "Hearts are full or you need more gems.", 409)
    db.commit()
    return user_state(db, user)


@router.post("/shop/streak-freeze")
def buy_streak_freeze(user: User = Depends(current_user), db: Session = Depends(get_db)):
    cost = get_settings().streak_freeze_gem_cost
    if user.streak_freezes >= 2 or user.gems < cost:
        raise GameError("cannot_buy", "You can equip at most 2 streak freezes.", 409)
    user.gems -= cost
    user.streak_freezes += 1
    db.commit()
    return user_state(db, user)


@router.post("/dev/advance-day")
def advance_day(user: User = Depends(current_user), db: Session = Depends(get_db)):
    """Demo/testing: move this learner's clock forward one day (streaks, hearts, quests, league)."""
    if not get_settings().demo_mode:
        raise GameError("disabled", "Demo mode is off", 403)
    user.clock_offset_days += 1
    state = user_state(db, user)
    db.commit()
    return state
