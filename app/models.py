from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import List, Optional

from sqlalchemy import (
    JSON,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class QuestionType(str, Enum):
    SHORT_TEXT = "short_text"
    LONG_TEXT = "long_text"
    INTEGER = "integer"
    DECIMAL = "decimal"
    SINGLE_CHOICE = "single_choice"
    MULTIPLE_CHOICE = "multiple_choice"


class Form(Base):
    __tablename__ = "forms"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    slug: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    questions: Mapped[List["Question"]] = relationship(
        "Question",
        back_populates="form",
        cascade="all, delete-orphan",
        order_by="Question.position",
    )
    response_groups: Mapped[List["ResponseGroup"]] = relationship(
        "ResponseGroup", back_populates="form", cascade="all, delete-orphan"
    )


class Question(Base):
    __tablename__ = "questions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    form_id: Mapped[int] = mapped_column(ForeignKey("forms.id", ondelete="CASCADE"))
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    type: Mapped[QuestionType] = mapped_column(SAEnum(QuestionType), nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    required: Mapped[bool] = mapped_column(default=False, nullable=False)
    metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    form: Mapped[Form] = relationship("Form", back_populates="questions")
    answers: Mapped[List["Answer"]] = relationship(
        "Answer", back_populates="question", cascade="all, delete-orphan"
    )

    __table_args__ = (UniqueConstraint("form_id", "position", name="uq_question_position"),)


class ResponseGroup(Base):
    __tablename__ = "response_groups"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    form_id: Mapped[int] = mapped_column(ForeignKey("forms.id", ondelete="CASCADE"))
    respondent_identifier: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    submitted_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    form: Mapped[Form] = relationship("Form", back_populates="response_groups")
    answers: Mapped[List["Answer"]] = relationship(
        "Answer", back_populates="response_group", cascade="all, delete-orphan"
    )


class Answer(Base):
    __tablename__ = "answers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    response_group_id: Mapped[int] = mapped_column(
        ForeignKey("response_groups.id", ondelete="CASCADE")
    )
    question_id: Mapped[int] = mapped_column(
        ForeignKey("questions.id", ondelete="CASCADE"), nullable=False
    )
    value: Mapped[str] = mapped_column(Text, nullable=False)

    response_group: Mapped[ResponseGroup] = relationship(
        "ResponseGroup", back_populates="answers"
    )
    question: Mapped[Question] = relationship("Question", back_populates="answers")
