"""API router for data export endpoints."""

import csv
import io
from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from database import get_db
from models import Question, QuestionTopic, Topic, Law, Subject

router = APIRouter(prefix="/api/export", tags=["export"])


@router.get("/csv")
def export_csv(
    subject_id: int = Query(None),
    min_year: int = Query(2015),
    max_year: int = Query(2024),
    db: Session = Depends(get_db),
):
    """Export question data as CSV."""
    query = (
        db.query(Question)
        .filter(Question.year >= min_year, Question.year <= max_year)
        .order_by(Question.year.desc(), Question.question_number)
    )
    if subject_id:
        query = query.filter(Question.subject_id == subject_id)

    questions = query.all()

    output = io.StringIO()
    # BOM for Excel Japanese compatibility
    output.write('\ufeff')
    writer = csv.writer(output)
    writer.writerow(["年度", "問題番号", "分野", "法律", "出題形式", "テーマ"])

    for q in questions:
        subject = db.query(Subject).get(q.subject_id)
        law = db.query(Law).get(q.law_id) if q.law_id else None
        topics = (
            db.query(Topic.name)
            .join(QuestionTopic, Topic.id == QuestionTopic.topic_id)
            .filter(QuestionTopic.question_id == q.id)
            .all()
        )
        topic_names = ", ".join(t.name for t in topics)

        writer.writerow([
            q.year,
            q.question_number,
            subject.name if subject else "",
            law.name if law else "",
            q.question_format or "",
            topic_names,
        ])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=gyoseishoshi_analysis.csv"},
    )
