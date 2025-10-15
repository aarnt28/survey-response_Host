from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, root_validator, validator

from .models import QuestionType


class ChoiceOption(BaseModel):
    value: str
    label: str


class QuestionMetadata(BaseModel):
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    pattern: Optional[str] = None
    placeholder: Optional[str] = None
    options: Optional[List[ChoiceOption]] = None

    @root_validator
    def validate_range(cls, values: dict) -> dict:
        min_value = values.get("min_value")
        max_value = values.get("max_value")
        if min_value is not None and max_value is not None and min_value > max_value:
            raise ValueError("min_value cannot be greater than max_value")
        return values


class QuestionCreate(BaseModel):
    prompt: str
    type: QuestionType
    position: int = 0
    required: bool = False
    metadata: Optional[QuestionMetadata] = None

    @validator("metadata", pre=True, always=True)
    def default_metadata(cls, value: Optional[dict]) -> Optional[dict]:
        return value or None

    @root_validator
    def validate_metadata_for_type(cls, values: dict) -> dict:
        metadata: Optional[QuestionMetadata] = values.get("metadata")
        question_type: QuestionType = values.get("type")

        if metadata is None:
            return values

        if question_type in {QuestionType.INTEGER, QuestionType.DECIMAL}:
            if metadata.options:
                raise ValueError("Numeric questions cannot define choice options")
        elif question_type in {QuestionType.SINGLE_CHOICE, QuestionType.MULTIPLE_CHOICE}:
            if not metadata.options:
                raise ValueError("Choice questions must define at least one option")
        else:
            if metadata.options:
                raise ValueError("Text questions cannot define choice options")
            if metadata.min_value is not None or metadata.max_value is not None:
                raise ValueError("Text questions cannot define numeric ranges")
        return values


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
    metadata: Optional[QuestionMetadata]

    class Config:
        orm_mode = True


class FormRead(BaseModel):
    id: int
    slug: str
    title: str
    description: Optional[str]
    created_at: datetime
    updated_at: datetime
    version: int
    is_archived: bool
    archived_at: Optional[datetime]
    questions: List[QuestionRead]

    class Config:
        orm_mode = True


class FormUpdate(BaseModel):
    title: str
    description: Optional[str] = None
    questions: List[QuestionCreate]


class FormVersionRead(BaseModel):
    id: int
    version: int
    title: str
    description: Optional[str]
    questions_snapshot: dict
    created_at: datetime

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
    form_version: int
    is_archived: bool
    archived_at: Optional[datetime]
    answers: List[AnswerRead]

    class Config:
        orm_mode = True


class ArchiveAction(BaseModel):
    archived: bool
