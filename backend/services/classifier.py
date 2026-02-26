"""Keyword-based automatic classification engine for exam questions."""

import json
import os
from typing import Optional
from sqlalchemy.orm import Session
from models import Topic, KeywordMapping, QuestionTopic


def load_keyword_mappings(db: Session) -> list[dict]:
    """Load keyword mappings from database."""
    mappings = db.query(KeywordMapping).all()
    return [{"topic_id": m.topic_id, "keyword": m.keyword, "weight": m.weight} for m in mappings]


def classify_text(text: str, mappings: list[dict], threshold: float = 1.0) -> list[int]:
    """Classify text by matching keywords and return list of topic IDs."""
    if not text:
        return []

    scores: dict[int, float] = {}
    for mapping in mappings:
        if mapping["keyword"] in text:
            tid = mapping["topic_id"]
            scores[tid] = scores.get(tid, 0) + mapping["weight"]

    return [tid for tid, score in scores.items() if score >= threshold]


def classify_question(
    question_text: str,
    choices_text: Optional[list[str]],
    mappings: list[dict],
    threshold: float = 1.0
) -> list[int]:
    """Classify a question by its text and choices."""
    combined = question_text or ""
    if choices_text:
        combined += " " + " ".join(choices_text)
    return classify_text(combined, mappings, threshold)


def auto_classify_all(db: Session):
    """Re-classify all questions in the database."""
    from models import Question
    mappings = load_keyword_mappings(db)
    questions = db.query(Question).all()

    for q in questions:
        choices_text = [c.content for c in q.choices if c.content]
        topic_ids = classify_question(q.question_text, choices_text, mappings)

        # Clear existing tags
        db.query(QuestionTopic).filter(QuestionTopic.question_id == q.id).delete()

        # Add new tags
        for tid in topic_ids:
            db.add(QuestionTopic(question_id=q.id, topic_id=tid))

    db.commit()
