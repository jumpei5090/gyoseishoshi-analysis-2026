"""Analysis service using Pandas for aggregation."""

import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy import func
from models import Question, QuestionTopic, Topic, Law, Subject


def get_yearly_frequency(db: Session, topic_ids: list[int], min_year: int = 2015, max_year: int = 2024) -> list[dict]:
    """Get yearly question count for given topic IDs."""
    if not topic_ids:
        return [{"year": y, "count": 0} for y in range(min_year, max_year + 1)]

    results = (
        db.query(Question.year, func.count(Question.id).label("count"))
        .join(QuestionTopic, Question.id == QuestionTopic.question_id)
        .filter(QuestionTopic.topic_id.in_(topic_ids))
        .filter(Question.year >= min_year, Question.year <= max_year)
        .group_by(Question.year)
        .order_by(Question.year)
        .all()
    )

    count_map = {r.year: r.count for r in results}
    return [{"year": y, "count": count_map.get(y, 0)} for y in range(min_year, max_year + 1)]


def get_subject_breakdown(db: Session, year: int = None) -> list[dict]:
    """Get question count breakdown by subject."""
    query = db.query(Subject.name, func.count(Question.id).label("count")).join(
        Question, Subject.id == Question.subject_id
    )
    if year:
        query = query.filter(Question.year == year)
    results = query.group_by(Subject.name).all()

    total = sum(r.count for r in results)
    return [
        {"subject_name": r.name, "count": r.count, "percentage": round(r.count / total * 100, 1) if total > 0 else 0}
        for r in results
    ]


def get_heatmap_data(db: Session, subject_id: int = None, min_year: int = 2015, max_year: int = 2024) -> list[dict]:
    """Get topic × year heatmap data."""
    query = (
        db.query(
            Topic.name.label("topic_name"),
            Law.name.label("law_name"),
            Subject.name.label("subject_name"),
            Question.year,
            func.count(Question.id).label("count"),
        )
        .join(QuestionTopic, Topic.id == QuestionTopic.topic_id)
        .join(Question, QuestionTopic.question_id == Question.id)
        .join(Law, Topic.law_id == Law.id)
        .join(Subject, Law.subject_id == Subject.id)
        .filter(Question.year >= min_year, Question.year <= max_year)
    )

    if subject_id:
        query = query.filter(Subject.id == subject_id)

    results = query.group_by(Topic.name, Law.name, Subject.name, Question.year).all()

    return [
        {
            "topic_name": r.topic_name,
            "law_name": r.law_name,
            "subject_name": r.subject_name,
            "year": r.year,
            "count": r.count,
        }
        for r in results
    ]


def search_topics(db: Session, keyword: str) -> list[dict]:
    """Search topics, laws, and subjects by keyword."""
    results = []

    # Search subjects
    subjects = db.query(Subject).filter(Subject.name.contains(keyword)).all()
    for s in subjects:
        results.append({"type": "subject", "id": s.id, "name": s.name, "parent_name": None})

    # Search laws
    laws = db.query(Law).filter(Law.name.contains(keyword)).all()
    for l in laws:
        subject = db.query(Subject).get(l.subject_id)
        results.append({"type": "law", "id": l.id, "name": l.name, "parent_name": subject.name if subject else None})

    # Search topics
    topics = db.query(Topic).filter(Topic.name.contains(keyword)).all()
    for t in topics:
        law = db.query(Law).get(t.law_id)
        results.append({"type": "topic", "id": t.id, "name": t.name, "parent_name": law.name if law else None})

    return results
