from __future__ import annotations

from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from . import schemas
from .models import Answer, Form, Question, ResponseGroup


class FormAlreadyExistsError(ValueError):
    pass


def create_form(session: Session, payload: schemas.FormCreate) -> Form:
    if session.scalar(select(Form).where(Form.slug == payload.slug)):
        raise FormAlreadyExistsError(f"Form with slug '{payload.slug}' already exists")

    form = Form(slug=payload.slug, title=payload.title, description=payload.description)

    form.questions = [
        Question(
            prompt=question.prompt,
            type=question.type,
            position=question.position,
            required=question.required,
            metadata=question.metadata,
        )
        for question in sorted(payload.questions, key=lambda q: q.position)
    ]

    session.add(form)
    session.flush()
    session.refresh(form)
    return form


def list_forms(session: Session) -> List[Form]:
    return session.scalars(select(Form).order_by(Form.created_at.desc())).all()


def get_form_by_slug(session: Session, slug: str) -> Optional[Form]:
    return session.scalar(select(Form).where(Form.slug == slug))


def create_response_group(
    session: Session, form: Form, payload: schemas.ResponseGroupCreate
) -> ResponseGroup:
    response_group = ResponseGroup(
        form=form,
        respondent_identifier=payload.respondent_identifier,
        notes=payload.notes,
    )

    questions = {question.id: question for question in form.questions}
    answers: List[Answer] = []

    for answer_payload in payload.answers:
        question = questions.get(answer_payload.question_id)
        if question is None:
            raise ValueError(
                f"Question id {answer_payload.question_id} is not part of form {form.slug}"
            )
        answers.append(
            Answer(
                question=question,
                value=answer_payload.value,
            )
        )

    response_group.answers = answers
    session.add(response_group)
    session.flush()
    session.refresh(response_group)
    return response_group


def list_responses_for_form(session: Session, form: Form) -> List[ResponseGroup]:
    stmt = (
        select(ResponseGroup)
        .where(ResponseGroup.form_id == form.id)
        .order_by(ResponseGroup.submitted_at.desc())
    )
    return session.scalars(stmt).all()
