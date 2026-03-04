"""SQLAlchemy ORM models for the exam analysis database."""

from sqlalchemy import Column, Integer, Text, Float, Boolean, ForeignKey, UniqueConstraint, Index
from sqlalchemy.orm import relationship
from database import Base


class Subject(Base):
    """Lv1: 分野 (Field) - e.g., 行政法, 民法"""
    __tablename__ = "subjects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(Text, nullable=False, unique=True)
    display_order = Column(Integer, default=0)

    laws = relationship("Law", back_populates="subject")
    questions = relationship("Question", back_populates="subject")


class Law(Base):
    """Lv2: 個別法 (Individual Law) - e.g., 行政手続法"""
    __tablename__ = "laws"

    id = Column(Integer, primary_key=True, index=True)
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=False)
    name = Column(Text, nullable=False)
    short_name = Column(Text, nullable=True)

    subject = relationship("Subject", back_populates="laws")
    topics = relationship("Topic", back_populates="law")
    questions = relationship("Question", back_populates="law")


class Topic(Base):
    """Lv3: テーマ/論点 (Theme/Issue) - e.g., 聴聞, 抵当権"""
    __tablename__ = "topics"

    id = Column(Integer, primary_key=True, index=True)
    law_id = Column(Integer, ForeignKey("laws.id"), nullable=False)
    name = Column(Text, nullable=False)

    law = relationship("Law", back_populates="topics")
    question_topics = relationship("QuestionTopic", back_populates="topic")
    keyword_mappings = relationship("KeywordMapping", back_populates="topic")


class Question(Base):
    """過去問 (Past Exam Question)"""
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)
    year = Column(Integer, nullable=False)
    question_number = Column(Integer, nullable=False)
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=False)
    law_id = Column(Integer, ForeignKey("laws.id"), nullable=True)
    question_format = Column(Text, nullable=True)
    question_text = Column(Text, nullable=True)
    correct_answer = Column(Text, nullable=True)
    explanation = Column(Text, nullable=True)

    __table_args__ = (
        UniqueConstraint("year", "question_number", name="uq_year_question"),
    )

    subject = relationship("Subject", back_populates="questions")
    law = relationship("Law", back_populates="questions")
    choices = relationship("Choice", back_populates="question", cascade="all, delete-orphan")
    question_topics = relationship("QuestionTopic", back_populates="question", cascade="all, delete-orphan")


class Choice(Base):
    """選択肢 (Answer Choice)"""
    __tablename__ = "choices"

    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False)
    choice_number = Column(Integer, nullable=False)
    content = Column(Text, nullable=True)
    is_correct = Column(Boolean, default=False)

    question = relationship("Question", back_populates="choices")


class QuestionTopic(Base):
    """問題×テーマ 多対多 (Many-to-Many: Question ↔ Topic)"""
    __tablename__ = "question_topics"

    question_id = Column(Integer, ForeignKey("questions.id"), primary_key=True)
    topic_id = Column(Integer, ForeignKey("topics.id"), primary_key=True)

    question = relationship("Question", back_populates="question_topics")
    topic = relationship("Topic", back_populates="question_topics")


class KeywordMapping(Base):
    """キーワード→テーマ マッピング (Keyword → Topic Mapping)"""
    __tablename__ = "keyword_mappings"

    id = Column(Integer, primary_key=True, index=True)
    topic_id = Column(Integer, ForeignKey("topics.id"), nullable=False)
    keyword = Column(Text, nullable=False)
    weight = Column(Float, default=1.0)

    topic = relationship("Topic", back_populates="keyword_mappings")


class UserAnswer(Base):
    """ユーザーの回答履歴 (User Answer History)"""
    __tablename__ = "user_answers"

    id = Column(Integer, primary_key=True, index=True)
    nickname = Column(Text, nullable=False, index=True)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False)
    is_correct = Column(Boolean, nullable=False)
    answered_at = Column(Text, nullable=False)  # ISO8601 string
    mode = Column(Text, nullable=True)           # 'practice' | 'mock'

    question = relationship("Question")

    __table_args__ = (
        Index("ix_user_answers_nickname_question", "nickname", "question_id"),
    )
