"""Database seeder — imports taxonomy and question data from JSON files."""

import json
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import engine, SessionLocal, init_db, Base
from models import Subject, Law, Topic, Question, QuestionTopic, KeywordMapping, Choice


def seed_taxonomy(db, data_dir: str):
    """Seed subjects, laws, topics, and keyword mappings from taxonomy JSON."""
    path = os.path.join(data_dir, "seed_taxonomy.json")
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    for subj_data in data["subjects"]:
        subject = Subject(
            id=subj_data["id"],
            name=subj_data["name"],
            display_order=subj_data["display_order"],
        )
        db.merge(subject)

        for law_data in subj_data["laws"]:
            law = Law(
                id=law_data["id"],
                subject_id=subj_data["id"],
                name=law_data["name"],
                short_name=law_data.get("short_name"),
            )
            db.merge(law)

            for topic_data in law_data["topics"]:
                topic = Topic(
                    id=topic_data["id"],
                    law_id=law_data["id"],
                    name=topic_data["name"],
                )
                db.merge(topic)

                # Seed keyword mappings
                for keyword in topic_data.get("keywords", []):
                    existing = (
                        db.query(KeywordMapping)
                        .filter_by(topic_id=topic_data["id"], keyword=keyword)
                        .first()
                    )
                    if not existing:
                        db.add(KeywordMapping(
                            topic_id=topic_data["id"],
                            keyword=keyword,
                            weight=1.0,
                        ))

    db.commit()
    print("✅ Taxonomy seeded successfully")


def seed_questions(db, data_dir: str):
    """Seed questions from questions JSON."""
    path = os.path.join(data_dir, "seed_questions.json")
    with open(path, "r", encoding="utf-8") as f:
        questions_data = json.load(f)

    # Build lookup maps
    subjects = {s.name: s for s in db.query(Subject).all()}
    laws = {l.name: l for l in db.query(Law).all()}
    topics = {t.name: t for t in db.query(Topic).all()}

    # Name aliases to map seed_questions.json names to taxonomy names
    SUBJECT_ALIASES = {"一般知識等": "一般知識"}
    LAW_ALIASES = {
        "政治・経済・社会": "一般知識",
        "情報通信・個人情報保護": "一般知識",
        "文章理解": "一般知識",
        "商法": "商法",
    }
    # Topic aliases
    TOPIC_ALIASES = {
        "法の基礎理論": "法の分類・効力",
        "裁判制度・法令用語": "裁判制度",
        "憲法総合": "人権総論",
        "人権": "人権総論",
        "統治機構": "国会",
        "行政法総論": "法律による行政の原理",
        "行政手続法": "申請に対する処分",
        "行政不服審査法": "審査請求",
        "行政事件訴訟法": "取消訴訟",
        "国家賠償法": "国家賠償（1条）",
        "地方自治法": "地方公共団体の組織",
        "行政法総合": "行政行為",
        "民法総則": "意思表示",
        "民法総合": "意思表示",
        "物権": "物権変動",
        "担保物権": "抵当権",
        "債権総論": "債務不履行",
        "債権各論": "契約総論",
        "親族・相続": "相続",
        "商法・会社法": "商人・商行為",
        "商法総則": "商人・商行為",
        "会社法": "株式",
        "憲法多肢選択": "人権総論",
        "行政法多肢選択": "行政行為",
        "行政法記述": "行政行為",
        "民法記述": "意思表示",
        "政治・経済・社会": "政治",
        "情報通信・個人情報保護": "情報通信",
        "文章理解": "文章理解",
    }

    for q_data in questions_data:
        subj_name = SUBJECT_ALIASES.get(q_data["subject"], q_data["subject"])
        subject = subjects.get(subj_name)
        law_name = q_data.get("law", "")
        law_name = LAW_ALIASES.get(law_name, law_name)
        law = laws.get(law_name)

        if not subject:
            print(f"⚠️  Subject not found: {q_data['subject']}")
            continue

        # Check if question already exists
        existing = (
            db.query(Question)
            .filter_by(year=q_data["year"], question_number=q_data["question_number"])
            .first()
        )
        if existing:
            question = existing
            # Always update fields with latest data
            if q_data.get("question_text"):
                existing.question_text = q_data["question_text"]
            if q_data.get("correct_answer"):
                existing.correct_answer = q_data["correct_answer"]
            if q_data.get("explanation"):
                existing.explanation = q_data["explanation"]
            if q_data.get("format"):
                existing.question_format = q_data["format"]
        else:
            question = Question(
                year=q_data["year"],
                question_number=q_data["question_number"],
                subject_id=subject.id,
                law_id=law.id if law else None,
                question_format=q_data.get("format"),
                question_text=q_data.get("question_text"),
                correct_answer=q_data.get("correct_answer"),
                explanation=q_data.get("explanation"),
            )
            db.add(question)
            db.flush()

        # Seed choices (delete old ones first)
        if q_data.get("choices"):
            db.query(Choice).filter_by(question_id=question.id).delete()
            for ch in q_data["choices"]:
                db.add(Choice(
                    question_id=question.id,
                    choice_number=ch["choice_number"],
                    content=ch["content"],
                    is_correct=ch.get("is_correct", False),
                ))

        # Add topic tags
        for topic_name in q_data.get("topics", []):
            resolved_name = TOPIC_ALIASES.get(topic_name, topic_name)
            topic = topics.get(resolved_name)
            if topic:
                existing_qt = (
                    db.query(QuestionTopic)
                    .filter_by(question_id=question.id, topic_id=topic.id)
                    .first()
                )
                if not existing_qt:
                    db.add(QuestionTopic(question_id=question.id, topic_id=topic.id))

    db.commit()
    print(f"✅ {len(questions_data)} questions seeded successfully")


def run_seed():
    """Run the full seeding process."""
    init_db()
    db = SessionLocal()
    data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

    try:
        seed_taxonomy(db, data_dir)
        seed_questions(db, data_dir)
        print("🎉 Database seeding complete!")
    finally:
        db.close()


if __name__ == "__main__":
    run_seed()
