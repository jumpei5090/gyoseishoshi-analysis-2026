"""Pydantic schemas for API request/response validation."""

from pydantic import BaseModel
from typing import Optional


# === Response Schemas ===

class SubjectOut(BaseModel):
    id: int
    name: str
    display_order: int

    class Config:
        from_attributes = True


class LawOut(BaseModel):
    id: int
    subject_id: int
    name: str
    short_name: Optional[str] = None

    class Config:
        from_attributes = True


class TopicOut(BaseModel):
    id: int
    law_id: int
    name: str

    class Config:
        from_attributes = True


class ChoiceOut(BaseModel):
    id: int
    choice_number: int
    content: Optional[str] = None
    is_correct: bool

    class Config:
        from_attributes = True


class QuestionOut(BaseModel):
    id: int
    year: int
    question_number: int
    subject_id: int
    law_id: Optional[int] = None
    question_format: Optional[str] = None
    question_text: Optional[str] = None
    correct_answer: Optional[str] = None
    explanation: Optional[str] = None
    choices: list[ChoiceOut] = []

    class Config:
        from_attributes = True


class TopicDetail(BaseModel):
    id: int
    name: str
    law_name: str
    subject_name: str

    class Config:
        from_attributes = True


# === Analysis Schemas ===

class YearlyFrequency(BaseModel):
    year: int
    count: int


class FrequencyResult(BaseModel):
    keyword: str
    matched_topics: list[TopicDetail]
    yearly_data: list[YearlyFrequency]
    total_count: int


class SubjectBreakdownItem(BaseModel):
    subject_name: str
    count: int
    percentage: float


class HeatmapCell(BaseModel):
    topic_name: str
    law_name: str
    subject_name: str
    year: int
    count: int


class SearchSuggestion(BaseModel):
    type: str  # "subject", "law", "topic"
    id: int
    name: str
    parent_name: Optional[str] = None
