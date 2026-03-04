"""API router for user answer history endpoints."""

from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from database import get_db
from models import UserAnswer, Question, QuestionTopic, Topic, Law, Subject

router = APIRouter(prefix="/api/answers", tags=["answers"])


@router.post("")
def save_answer(
    nickname: str = Query(..., min_length=1),
    question_id: int = Query(...),
    is_correct: bool = Query(...),
    mode: str = Query("practice"),
    db: Session = Depends(get_db),
):
    """Save a user's answer result."""
    answer = UserAnswer(
        nickname=nickname,
        question_id=question_id,
        is_correct=is_correct,
        answered_at=datetime.now(timezone.utc).isoformat(),
        mode=mode,
    )
    db.add(answer)
    db.commit()
    return {"ok": True}


@router.get("/{nickname}/history")
def get_history(
    nickname: str,
    db: Session = Depends(get_db),
):
    """Get all answer history for a nickname, returning only the most recent attempt per question."""
    # Get the latest answer per question for this user
    subq = (
        db.query(
            UserAnswer.question_id,
            func.max(UserAnswer.answered_at).label("latest_at"),
        )
        .filter(UserAnswer.nickname == nickname)
        .group_by(UserAnswer.question_id)
        .subquery()
    )

    rows = (
        db.query(UserAnswer)
        .join(
            subq,
            (UserAnswer.question_id == subq.c.question_id)
            & (UserAnswer.answered_at == subq.c.latest_at),
        )
        .filter(UserAnswer.nickname == nickname)
        .all()
    )

    return [
        {
            "question_id": r.question_id,
            "is_correct": r.is_correct,
            "answered_at": r.answered_at,
            "mode": r.mode,
        }
        for r in rows
    ]


@router.get("/{nickname}/analysis")
def get_analysis(
    nickname: str,
    db: Session = Depends(get_db),
):
    """Get strength/weakness analysis by topic for a nickname."""
    # Get all answers
    answers = db.query(UserAnswer).filter(UserAnswer.nickname == nickname).all()
    if not answers:
        return {
            "total_answered": 0,
            "total_correct": 0,
            "overall_rate": None,
            "last_answered_at": None,
            "by_subject": [],
            "strong_topics": [],
            "weak_topics": [],
        }

    # Build question_id → {correct_count, total} map (latest attempt only)
    # Use all attempts for analysis (more data = better analysis)
    q_stats = {}
    for a in answers:
        qid = a.question_id
        if qid not in q_stats:
            q_stats[qid] = {"correct": 0, "total": 0}
        q_stats[qid]["total"] += 1
        if a.is_correct:
            q_stats[qid]["correct"] += 1

    total_answered = len(q_stats)
    total_correct = sum(1 for s in q_stats.values() if s["correct"] > 0)
    overall_rate = round(total_correct / total_answered * 100, 1) if total_answered > 0 else None
    last_answered_at = max(a.answered_at for a in answers)

    # Group by topic
    topic_stats = {}  # topic_id → {name, law_name, subject_name, correct, total}
    for qid, stat in q_stats.items():
        q = db.query(Question).get(qid)
        if not q:
            continue
        qt_rows = db.query(QuestionTopic).filter(QuestionTopic.question_id == qid).all()
        for qt in qt_rows:
            t = db.query(Topic).get(qt.topic_id)
            l = db.query(Law).get(t.law_id) if t else None
            s = db.query(Subject).get(l.subject_id) if l else None
            tid = qt.topic_id
            if tid not in topic_stats:
                topic_stats[tid] = {
                    "topic_id": tid,
                    "topic_name": t.name if t else "不明",
                    "law_name": l.name if l else "",
                    "subject_name": s.name if s else "",
                    "subject_id": s.id if s else None,
                    "correct": 0,
                    "total": 0,
                }
            topic_stats[tid]["total"] += stat["total"]
            topic_stats[tid]["correct"] += stat["correct"]

    # Calculate rates
    for ts in topic_stats.values():
        ts["rate"] = round(ts["correct"] / ts["total"] * 100, 1) if ts["total"] > 0 else 0
        ts["answered"] = ts["total"]

    all_topics = sorted(topic_stats.values(), key=lambda x: x["rate"])

    # Filter topics with ≥2 questions answered for meaningful analysis
    qualified = [t for t in all_topics if t["answered"] >= 2]

    strong = sorted([t for t in qualified if t["rate"] >= 70], key=lambda x: -x["rate"])[:5]
    weak = sorted([t for t in qualified if t["rate"] < 60], key=lambda x: x["rate"])[:5]

    # Group by subject
    subject_map = {}
    for ts in topic_stats.values():
        sid = ts["subject_id"]
        sname = ts["subject_name"]
        if sid not in subject_map:
            subject_map[sid] = {"subject_name": sname, "correct": 0, "total": 0}
        subject_map[sid]["correct"] += ts["correct"]
        subject_map[sid]["total"] += ts["total"]

    by_subject = []
    for sid, sv in subject_map.items():
        rate = round(sv["correct"] / sv["total"] * 100, 1) if sv["total"] > 0 else 0
        by_subject.append({
            "subject_id": sid,
            "subject_name": sv["subject_name"],
            "correct": sv["correct"],
            "total": sv["total"],
            "rate": rate,
        })
    by_subject.sort(key=lambda x: -(x["subject_id"] or 0))

    return {
        "total_answered": total_answered,
        "total_correct": total_correct,
        "overall_rate": overall_rate,
        "last_answered_at": last_answered_at,
        "by_subject": by_subject,
        "strong_topics": strong,
        "weak_topics": weak,
    }
