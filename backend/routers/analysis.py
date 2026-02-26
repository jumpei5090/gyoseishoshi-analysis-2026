"""API router for analysis endpoints."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from database import get_db
from models import Topic, Law, Subject, Question, QuestionTopic
from services.analyzer import get_yearly_frequency, get_subject_breakdown, get_heatmap_data, search_topics
from services.predictor import generate_predictions, generate_subject_predictions

router = APIRouter(prefix="/api/analysis", tags=["analysis"])


@router.get("/search")
def search(keyword: str = Query(..., min_length=1), db: Session = Depends(get_db)):
    """Search for subjects, laws, and topics matching a keyword."""
    return search_topics(db, keyword)


@router.get("/frequency")
def frequency(
    keyword: str = Query(..., min_length=1),
    min_year: int = Query(2015),
    max_year: int = Query(2024),
    db: Session = Depends(get_db),
):
    """Get yearly frequency for a keyword (searches across topics, laws, subjects)."""
    # Find matching topic IDs
    topic_ids = set()
    matched_items = []

    # Match topics
    topics = db.query(Topic).filter(Topic.name.contains(keyword)).all()
    for t in topics:
        topic_ids.add(t.id)
        law = db.query(Law).get(t.law_id)
        subject = db.query(Subject).get(law.subject_id) if law else None
        matched_items.append({
            "id": t.id, "name": t.name,
            "law_name": law.name if law else "",
            "subject_name": subject.name if subject else "",
        })

    # Match laws -> all their topics
    laws = db.query(Law).filter(Law.name.contains(keyword)).all()
    for l in laws:
        law_topics = db.query(Topic).filter(Topic.law_id == l.id).all()
        for t in law_topics:
            topic_ids.add(t.id)
        subject = db.query(Subject).get(l.subject_id)
        matched_items.append({
            "id": l.id, "name": l.name,
            "law_name": l.name,
            "subject_name": subject.name if subject else "",
        })

    # Match subjects -> all their topics
    subjects = db.query(Subject).filter(Subject.name.contains(keyword)).all()
    for s in subjects:
        s_laws = db.query(Law).filter(Law.subject_id == s.id).all()
        for l in s_laws:
            law_topics = db.query(Topic).filter(Topic.law_id == l.id).all()
            for t in law_topics:
                topic_ids.add(t.id)
        matched_items.append({
            "id": s.id, "name": s.name,
            "law_name": "", "subject_name": s.name,
        })

    yearly = get_yearly_frequency(db, list(topic_ids), min_year, max_year)
    total = sum(y["count"] for y in yearly)

    return {
        "keyword": keyword,
        "matched_topics": matched_items,
        "yearly_data": yearly,
        "total_count": total,
    }


@router.get("/subject-breakdown")
def subject_breakdown(year: int = Query(None), db: Session = Depends(get_db)):
    """Get question count breakdown by subject."""
    return get_subject_breakdown(db, year)


@router.get("/heatmap")
def heatmap(
    subject_id: int = Query(None),
    min_year: int = Query(2015),
    max_year: int = Query(2024),
    db: Session = Depends(get_db),
):
    """Get topic × year heatmap data."""
    return get_heatmap_data(db, subject_id, min_year, max_year)


@router.get("/subjects")
def list_subjects(db: Session = Depends(get_db)):
    """List all subjects."""
    subjects = db.query(Subject).order_by(Subject.display_order).all()
    return [{"id": s.id, "name": s.name} for s in subjects]


@router.get("/laws")
def list_laws(subject_id: int = Query(None), db: Session = Depends(get_db)):
    """List laws, optionally filtered by subject."""
    query = db.query(Law)
    if subject_id:
        query = query.filter(Law.subject_id == subject_id)
    laws = query.all()
    return [{"id": l.id, "name": l.name, "subject_id": l.subject_id} for l in laws]


@router.get("/topics")
def list_topics(law_id: int = Query(None), db: Session = Depends(get_db)):
    """List topics, optionally filtered by law."""
    query = db.query(Topic)
    if law_id:
        query = query.filter(Topic.law_id == law_id)
    topics = query.all()
    return [{"id": t.id, "name": t.name, "law_id": t.law_id} for t in topics]


@router.get("/taxonomy")
def get_taxonomy(db: Session = Depends(get_db)):
    """Get full taxonomy tree: subjects → laws → topics."""
    subjects = db.query(Subject).order_by(Subject.display_order).all()
    result = []
    for s in subjects:
        laws_data = []
        s_laws = db.query(Law).filter(Law.subject_id == s.id).all()
        for l in s_laws:
            l_topics = db.query(Topic).filter(Topic.law_id == l.id).all()
            laws_data.append({
                "id": l.id,
                "name": l.name,
                "short_name": l.short_name,
                "topics": [{"id": t.id, "name": t.name} for t in l_topics],
            })
        result.append({
            "id": s.id,
            "name": s.name,
            "laws": laws_data,
        })
    return result


@router.get("/questions")
def get_questions(
    keyword: str = Query(..., min_length=1),
    year: int = Query(...),
    db: Session = Depends(get_db),
):
    """Get individual questions matching a keyword for a specific year."""
    # Find matching topic IDs (same logic as frequency)
    topic_ids = set()

    topics = db.query(Topic).filter(Topic.name.contains(keyword)).all()
    for t in topics:
        topic_ids.add(t.id)

    laws = db.query(Law).filter(Law.name.contains(keyword)).all()
    for l in laws:
        law_topics = db.query(Topic).filter(Topic.law_id == l.id).all()
        for t in law_topics:
            topic_ids.add(t.id)

    subjects = db.query(Subject).filter(Subject.name.contains(keyword)).all()
    for s in subjects:
        s_laws = db.query(Law).filter(Law.subject_id == s.id).all()
        for l in s_laws:
            law_topics = db.query(Topic).filter(Topic.law_id == l.id).all()
            for t in law_topics:
                topic_ids.add(t.id)

    if not topic_ids:
        return []

    # Get questions for the year that have any of these topics
    from sqlalchemy import distinct
    question_ids = (
        db.query(distinct(QuestionTopic.question_id))
        .filter(QuestionTopic.topic_id.in_(topic_ids))
        .subquery()
    )

    questions = (
        db.query(Question)
        .filter(Question.id.in_(question_ids), Question.year == year)
        .order_by(Question.question_number)
        .all()
    )

    result = []
    for q in questions:
        subject = db.query(Subject).get(q.subject_id)
        law = db.query(Law).get(q.law_id) if q.law_id else None
        q_topics = (
            db.query(Topic)
            .join(QuestionTopic)
            .filter(QuestionTopic.question_id == q.id)
            .all()
        )
        from models import Choice
        q_choices = (
            db.query(Choice)
            .filter_by(question_id=q.id)
            .order_by(Choice.choice_number)
            .all()
        )
        result.append({
            "id": q.id,
            "year": q.year,
            "question_number": q.question_number,
            "subject_name": subject.name if subject else "",
            "law_name": law.name if law else "",
            "format": q.question_format or "",
            "question_text": q.question_text or "",
            "correct_answer": q.correct_answer or "",
            "explanation": q.explanation or "",
            "choices": [
                {
                    "choice_number": c.choice_number,
                    "content": c.content or "",
                    "is_correct": c.is_correct,
                }
                for c in q_choices
            ],
            "topics": [t.name for t in q_topics],
        })

    return result


@router.get("/question/{year}/{question_number}")
def get_single_question(year: int, question_number: int, db: Session = Depends(get_db)):
    """Get a single question by year and question number."""
    from models import Choice

    q = (
        db.query(Question)
        .filter(Question.year == year, Question.question_number == question_number)
        .first()
    )
    if not q:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Question not found")

    subject = db.query(Subject).get(q.subject_id)
    law = db.query(Law).get(q.law_id) if q.law_id else None
    q_topics = (
        db.query(Topic)
        .join(QuestionTopic)
        .filter(QuestionTopic.question_id == q.id)
        .all()
    )
    q_choices = (
        db.query(Choice)
        .filter_by(question_id=q.id)
        .order_by(Choice.choice_number)
        .all()
    )

    return {
        "id": q.id,
        "year": q.year,
        "question_number": q.question_number,
        "subject_name": subject.name if subject else "",
        "law_name": law.name if law else "",
        "format": q.question_format or "",
        "question_text": q.question_text or "",
        "correct_answer": q.correct_answer or "",
        "explanation": q.explanation or "",
        "choices": [
            {
                "choice_number": c.choice_number,
                "content": c.content or "",
                "is_correct": c.is_correct,
            }
            for c in q_choices
        ],
        "topics": [t.name for t in q_topics],
    }


@router.get("/topic-breakdown")
def topic_breakdown(
    min_year: int = Query(2015),
    max_year: int = Query(2024),
    db: Session = Depends(get_db),
):
    """
    Get topic-level breakdown grouped by subject, with per-year question data.
    Returns: [{subject_name, subject_id, topics: [{topic_name, total, yearly: [{year, count, questions}]}]}]
    """
    from sqlalchemy import func, distinct

    subjects = db.query(Subject).order_by(Subject.display_order).all()
    result = []

    for s in subjects:
        # Get all topics under this subject
        s_laws = db.query(Law).filter(Law.subject_id == s.id).all()
        law_ids = [l.id for l in s_laws]
        if not law_ids:
            continue

        s_topics = db.query(Topic).filter(Topic.law_id.in_(law_ids)).all()
        topics_data = []

        for t in s_topics:
            yearly = []
            total = 0
            for year in range(min_year, max_year + 1):
                # Get questions for this topic in this year
                questions = (
                    db.query(Question)
                    .join(QuestionTopic, Question.id == QuestionTopic.question_id)
                    .filter(
                        QuestionTopic.topic_id == t.id,
                        Question.year == year,
                    )
                    .order_by(Question.question_number)
                    .all()
                )
                count = len(questions)
                total += count
                yearly.append({
                    "year": year,
                    "count": count,
                    "questions": [
                        {
                            "id": q.id,
                            "question_number": q.question_number,
                            "format": q.question_format or "",
                            "question_text": (q.question_text or "")[:80],
                        }
                        for q in questions
                    ],
                })

            if total > 0:
                # Find which law this topic belongs to
                law = db.query(Law).get(t.law_id)
                topics_data.append({
                    "topic_id": t.id,
                    "topic_name": t.name,
                    "law_name": law.name if law else "",
                    "total": total,
                    "yearly": yearly,
                })

        # Sort by total descending
        topics_data.sort(key=lambda x: x["total"], reverse=True)

        subject_total = sum(td["total"] for td in topics_data)
        result.append({
            "subject_id": s.id,
            "subject_name": s.name,
            "subject_total": subject_total,
            "topics": topics_data,
        })

    return result


@router.get("/predictions/topics")
def get_topic_predictions(db: Session = Depends(get_db)):
    """Get 2026 exam topic-level predictions ranked by composite score."""
    return generate_predictions(db)


@router.get("/predictions/laws")
def get_law_predictions(db: Session = Depends(get_db)):
    """Get 2026 exam law/chapter-level predictions ranked by score."""
    return generate_subject_predictions(db)
