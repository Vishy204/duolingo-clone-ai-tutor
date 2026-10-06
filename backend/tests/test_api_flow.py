"""End-to-end lesson loop through the HTTP API (agents disabled -> rules engine)."""
import os

from app.models import Exercise


def _correct_answer(ex: Exercise) -> dict:
    p = ex.payload
    if ex.type == "multiple_choice":
        return {"choice": p["answer"]}
    if ex.type == "fill_blank":
        return {"choice": p["answer"]}
    if ex.type in ("translate", "type_answer"):
        return {"text": p["answers"][0]}
    return {"mistakes": 0}


def test_guest_has_demo_progress(client, auth):
    me = client.get("/api/v1/me", headers=auth).json()
    assert me["streak"] == 3 and me["hearts"] == 5 and me["total_xp"] > 0
    path = client.get("/api/v1/path", headers=auth).json()
    statuses = [n["status"] for u in path["units"] for n in u["nodes"]]
    assert statuses[:3] == ["completed", "completed", "active"]
    assert statuses[-1] == "locked"


def test_requires_auth(client):
    assert client.get("/api/v1/me").status_code == 401
    assert client.get("/api/v1/me", headers={"Authorization": "Bearer nope"}).status_code == 401


def test_locked_lesson_is_rejected(client, auth):
    path = client.get("/api/v1/path", headers=auth).json()
    locked = next(n for u in path["units"] for n in u["nodes"] if n["status"] == "locked" and n["next_lesson_id"])
    r = client.post("/api/v1/sessions", json={"mode": "lesson", "lesson_id": locked["next_lesson_id"]}, headers=auth)
    assert r.status_code == 403


def test_full_lesson_loop_with_mistake_requeue_and_rewards(client, auth, db):
    path = client.get("/api/v1/path", headers=auth).json()
    active = next(n for u in path["units"] for n in u["nodes"] if n["status"] == "active")
    s = client.post("/api/v1/sessions", json={"mode": "lesson", "lesson_id": active["next_lesson_id"]},
                    headers=auth).json()
    assert "answers" not in str(s["exercises"][0]["data"])  # answers never leak to the client
    queue = [e["id"] for e in s["exercises"]]

    first = True
    i = 0
    while i < len(queue):
        ex = db.get(Exercise, queue[i])
        answer = {"text": "zzz wrong"} if first and ex.type in ("translate", "type_answer") else _correct_answer(ex)
        r = client.post(f"/api/v1/sessions/{s['id']}/answers", json={"exercise_id": ex.id, "answer": answer},
                        headers=auth).json()
        if answer.get("text") == "zzz wrong":
            first = False
            assert not r["correct"] and r["requeued"] and r["hearts"] == 4
            queue.append(ex.id)
        else:
            assert r["correct"], (ex.type, ex.payload, r)
        i += 1

    done = client.post(f"/api/v1/sessions/{s['id']}/complete", headers=auth).json()
    assert done["xp_earned"] == 10 and done["streak_extended"] and done["streak"] == 4
    path2 = client.get("/api/v1/path", headers=auth).json()
    node = next(n for u in path2["units"] for n in u["nodes"] if n["id"] == active["id"])
    assert node["lessons_completed"] == active["lessons_completed"] + 1

    # The background tutor run (rules engine without an API key) produced a ready plan.
    insights = client.get("/api/v1/tutor/insights", headers=auth).json()
    assert insights["ready_plan"] and insights["ready_plan"]["engine"] == "rules"
    p = client.post("/api/v1/sessions", json={"mode": "personalized"}, headers=auth)
    assert p.status_code == 200 and len(p.json()["exercises"]) > 0


def test_out_of_order_answer_rejected(client, auth):
    s = client.post("/api/v1/sessions", json={"mode": "practice"}, headers=auth).json()
    wrong_id = s["exercises"][1]["id"] if s["exercises"][1]["id"] != s["exercises"][0]["id"] else -1
    r = client.post(f"/api/v1/sessions/{s['id']}/answers", json={"exercise_id": wrong_id, "answer": {"choice": 0}},
                    headers=auth)
    assert r.status_code == 409


def test_cannot_touch_other_learners_session(client, auth):
    s = client.post("/api/v1/sessions", json={"mode": "practice"}, headers=auth).json()
    other = client.post("/api/v1/auth/guest", json={}, headers={"x-forwarded-for": "10.9.9.9"}).json()["token"]
    r = client.post(f"/api/v1/sessions/{s['id']}/complete", headers={"Authorization": f"Bearer {other}"})
    assert r.status_code == 404


def test_simulator_shifts_diagnosis(client, auth):
    r = client.post("/api/v1/tutor/simulate", json={"profile": "word_order"}, headers=auth).json()
    assert r["injected"] > 0
    brain = client.get("/api/v1/tutor/brain", headers=auth).json()
    # A scrambled answer can occasionally also read as an extra/missing word; word order must dominate.
    assert brain["error_breakdown"]["errors_by_type"].get("word_order", 0) >= r["injected"] // 2
    assert brain["plans"][0]["status"] == "ready"


def test_advance_day_and_leaderboard(client, auth):
    before = client.get("/api/v1/me", headers=auth).json()
    after = client.post("/api/v1/dev/advance-day", headers=auth).json()
    assert after["clock_offset_days"] == before["clock_offset_days"] + 1
    board = client.get("/api/v1/leaderboard", headers=auth).json()
    assert len(board["rows"]) == 16 and any(r["is_me"] for r in board["rows"])


def test_custom_practice_tab_builds_and_keeps_practices(client, auth):
    """Custom Practice: build on a picked topic (even one not studied yet), start it by id, and an
    automatic tutor update must not replace it."""
    r = client.post("/api/v1/tutor/custom", json={"concepts": ["vocab.animals"]}, headers=auth)
    assert r.status_code == 200 and r.json()["status"] == "building"
    data = client.get("/api/v1/tutor/custom", headers=auth).json()
    assert any(t["key"] == "vocab.animals" for t in data["topics"])
    practice = data["practices"][0]
    assert practice["trigger"] == "custom" and practice["status"] == "ready"
    assert practice["focus_concepts"] == ["vocab.animals"] and practice["exercise_count"] > 0

    client.post("/api/v1/tutor/plan", json={"focus": []}, headers=auth)  # automatic-family update
    again = client.get("/api/v1/tutor/custom", headers=auth).json()["practices"][0]
    assert again["id"] == practice["id"] and again["status"] == "ready"
    insights = client.get("/api/v1/tutor/insights", headers=auth).json()
    assert insights["latest_custom"]["id"] == practice["id"]

    s = client.post("/api/v1/sessions", json={"mode": "personalized", "plan_id": practice["id"]}, headers=auth)
    assert s.status_code == 200, s.text
    assert s.json()["mode"] == "personalized"


def test_custom_practice_rejects_unknown_topics_and_other_learners_plans(client, auth):
    assert client.post("/api/v1/tutor/custom", json={"concepts": ["vocab.dragons"]}, headers=auth).status_code == 422
    other_ip = f"10.9.{os.urandom(1)[0]}.{os.urandom(1)[0]}"
    other = client.post("/api/v1/auth/guest", json={}, headers={"x-forwarded-for": other_ip}).json()["token"]
    other_auth = {"Authorization": f"Bearer {other}"}
    client.post("/api/v1/tutor/custom", json={"concepts": ["verb.ser"]}, headers=other_auth)
    theirs = client.get("/api/v1/tutor/custom", headers=other_auth).json()["practices"][0]["id"]
    r = client.post("/api/v1/sessions", json={"mode": "personalized", "plan_id": theirs}, headers=auth)
    assert r.status_code == 409


def test_custom_practice_costs_no_hearts_and_skip_has_no_error_type(client, auth):
    client.post("/api/v1/tutor/custom", json={"concepts": ["vocab.food"]}, headers=auth)
    plan = client.get("/api/v1/tutor/custom", headers=auth).json()["practices"][0]
    s = client.post("/api/v1/sessions", json={"mode": "personalized", "plan_id": plan["id"]}, headers=auth).json()
    assert s["custom"] is True and s["uses_hearts"] is False
    before = client.get("/api/v1/me", headers=auth).json()["hearts"]
    ex = s["exercises"][0]
    r = client.post(f"/api/v1/sessions/{s['id']}/answers", headers=auth, json={
        "exercise_id": ex["id"], "answer": {"text": "", "tokens": [], "choice": -1, "mistakes": 1, "skipped": True}})
    body = r.json()
    assert body["correct"] is False and body["error_type"] is None and not body.get("feedback")
    assert client.get("/api/v1/me", headers=auth).json()["hearts"] == before
