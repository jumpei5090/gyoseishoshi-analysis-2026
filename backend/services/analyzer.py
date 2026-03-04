"""Analysis service using Pandas for aggregation."""

import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy import func
from models import Question, QuestionTopic, Topic, Law, Subject


def get_yearly_frequency(db: Session, topic_ids: list[int], min_year: int = 2015, max_year: int = 2025) -> list[dict]:
    """Get yearly question count for given topic IDs."""
    if not topic_ids:
        return [{"year": y, "count": 0} for y in range(min_year, max_year + 1)]

    results = (
        db.query(Question.year, func.count(Question.id.distinct()).label("count"))
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


def get_heatmap_data(db: Session, subject_id: int = None, min_year: int = 2015, max_year: int = 2025) -> list[dict]:
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


from sqlalchemy import or_, and_
from models import KeywordMapping

def get_topic_ids_by_keyword(db: Session, keyword: str) -> dict[int, float]:
    """
    Search topics by keyword and return a dict of {topic_id: total_weight}.
    Supports multi-word AND search, keyword mappings, and full-text fallbacks.
    """
    if not keyword:
        return {}

    # Split keyword by spaces for AND search
    words = [w.strip() for w in keyword.replace("　", " ").split(" ") if w.strip()]
    if not words:
        return {}

    final_topics = {} # {topic_id: weight}

    for word in words:
        word_topics = {}
        
        # 1. Search Subjects (Weight: 100 for exact, 50 for partial)
        # Match topics belonging to these subjects
        subjects = db.query(Subject).filter(Subject.name.contains(word)).all()
        for s in subjects:
            weight = 100 if s.name == word else 50
            for l in s.laws:
                for t in l.topics:
                    word_topics[t.id] = max(word_topics.get(t.id, 0), weight)

        # 2. Search Laws (Weight: 80 for exact, 40 for partial)
        # Match topics belonging to these laws
        laws = db.query(Law).filter(Law.name.contains(word)).all()
        for l in laws:
            weight = 80 if l.name == word else 40
            for t in l.topics:
                word_topics[t.id] = max(word_topics.get(t.id, 0), weight)

        # 3. Search Topics (Weight: 60 for exact, 30 for partial)
        topics = db.query(Topic).filter(Topic.name.contains(word)).all()
        for t in topics:
            weight = 60 if t.name == word else 30
            word_topics[t.id] = max(word_topics.get(t.id, 0), weight)

        # 4. Search KeywordMappings (Weight: 20 per keyword match)
        k_mappings = db.query(KeywordMapping).filter(KeywordMapping.keyword.contains(word)).all()
        for km in k_mappings:
            word_topics[km.topic_id] = word_topics.get(km.topic_id, 0) + 20

        # 5. Search Question Text/Explanation (Weight: 10 per match)
        questions = db.query(Question).filter(
            or_(
                Question.question_text.contains(word),
                Question.explanation.contains(word)
            )
        ).limit(50).all()
        
        for q in questions:
            for qt in q.question_topics:
                word_topics[qt.topic_id] = word_topics.get(qt.topic_id, 0) + 10

        # AND logic intersection
        if not final_topics:
            final_topics = word_topics
        else:
            new_final = {}
            for tid, weight in word_topics.items():
                if tid in final_topics:
                    new_final[tid] = weight + final_topics[tid]
            final_topics = new_final
            if not final_topics:
                break

    return final_topics


def search_topics(db: Session, keyword: str) -> list[dict]:
    """Search for suggestions by keyword."""
    topic_weights = get_topic_ids_by_keyword(db, keyword)
    if not topic_weights:
        return []
    
    # Also search for subjects and laws directly for suggestions (not just their topics)
    # These are handled separately because they aren't "topics" themselves
    direct_results = []
    words = [w.strip() for w in keyword.replace("　", " ").split(" ") if w.strip()]
    if words:
        # Simple implementation for suggestion prioritization of subjects/laws
        # In a real AND search for suggestions, we'd intersect these too, 
        # but for simplicity we'll just add them if they match the whole query or parts
        for s in db.query(Subject).filter(Subject.name.contains(keyword)).all():
            direct_results.append({
                "type": "subject", "id": s.id, "name": s.name, 
                "parent_name": None, "weight": 100 if s.name == keyword else 50
            })
        for l in db.query(Law).filter(Law.name.contains(keyword)).all():
            subject = db.query(Subject).get(l.subject_id)
            direct_results.append({
                "type": "law", "id": l.id, "name": l.name, 
                "parent_name": subject.name if subject else None, "weight": 80 if l.name == keyword else 40
            })

    # Convert topic weights to results
    topic_results = []
    for tid, weight in topic_weights.items():
        t = db.query(Topic).get(tid)
        law = db.query(Law).get(t.law_id)
        topic_results.append({
            "type": "topic", "id": t.id, "name": t.name,
            "parent_name": law.name if law else None, "weight": weight
        })

    results = direct_results + topic_results
    sorted_results = sorted(results, key=lambda x: x["weight"], reverse=True)
    
    # Deduplicate and return top 20
    seen = set()
    final = []
    for item in sorted_results:
        key = f"{item['type']}_{item['id']}"
        if key not in seen:
            seen.add(key)
            # Remove weight for frontend
            clean_item = {k: v for k, v in item.items() if k != 'weight'}
            final.append(clean_item)
            if len(final) >= 20:
                break
                
    return final
