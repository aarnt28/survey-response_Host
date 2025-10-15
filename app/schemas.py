from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, validator

from .models import QuestionType


class QuestionCreate(BaseModel):
    prompt: str
    type: QuestionType
    position: int = 0
    required: bool = False
    metadata: Optional[dict] = None

    @validator("metadata", pre=True, always=True)
    def default_metadata(cls, value: Optional[dict]) -> Optional[dict]:
        return value or None


class FormCreate(BaseModel):
    slug: str = Field(..., min_length=3, max_length=100)
    title: str
    description: Optional[str] = None
    questions: List[QuestionCreate]


class QuestionRead(BaseModel):
    id: int
    prompt: str
    type: QuestionType
    position: int
    required: bool
    metadata: Optional[dict]

    class Config:
        orm_mode = True


class FormRead(BaseModel):
    id: int
    slug: str
    title: str
    description: Optional[str]
    created_at: datetime
    questions: List[QuestionRead]

    class Config:
        orm_mode = True


class AnswerCreate(BaseModel):
    question_id: int
    value: str


class ResponseGroupCreate(BaseModel):
    respondent_identifier: Optional[str] = None
    notes: Optional[str] = None
    answers: List[AnswerCreate]


class AnswerRead(BaseModel):
    id: int
    question_id: int
    value: str

    class Config:
        orm_mode = True


class ResponseGroupRead(BaseModel):
    id: int
    form_id: int
    respondent_identifier: Optional[str]
    submitted_at: datetime
    notes: Optional[str]
    answers: List[AnswerRead]

    class Config:
        orm_mode = True
