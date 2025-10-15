from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from . import schemas
from .models import (
    Answer,
    Form,
    FormVersion,
    PracticeOverviewResponse,
    Question,
    QuestionType,
    ResponseGroup,
)


class FormAlreadyExistsError(ValueError):
    pass


def _serialize_questions(questions: List[Question]) -> List[dict]:
    return [
        {
            "prompt": question.prompt,
            "type": question.type.value,
            "position": question.position,
            "required": question.required,
            "metadata": question.metadata,
        }
        for question in sorted(questions, key=lambda q: q.position)
    ]


def _build_question_model(question: schemas.QuestionCreate) -> Question:
    metadata_dict = (
        question.metadata.dict(exclude_none=True)
        if isinstance(question.metadata, schemas.QuestionMetadata)
        else question.metadata
    )
    return Question(
        prompt=question.prompt,
        type=question.type,
        position=question.position,
        required=question.required,
        metadata=metadata_dict,
    )


def create_form(session: Session, payload: schemas.FormCreate) -> Form:
    if session.scalar(select(Form).where(Form.slug == payload.slug)):
        raise FormAlreadyExistsError(f"Form with slug '{payload.slug}' already exists")

    form = Form(
        slug=payload.slug,
        title=payload.title,
        description=payload.description,
        version=1,
    )

    form.questions = [
        _build_question_model(question) for question in sorted(payload.questions, key=lambda q: q.position)
    ]

    session.add(form)
    session.flush()

    version_snapshot = FormVersion(
        form=form,
        version=form.version,
        title=form.title,
        description=form.description,
        questions_snapshot={"questions": _serialize_questions(form.questions)},
    )
    session.add(version_snapshot)
    session.refresh(form)
    return form


def list_forms(session: Session, include_archived: bool = False) -> List[Form]:
    stmt = select(Form).order_by(Form.created_at.desc())
    if not include_archived:
        stmt = stmt.where(Form.is_archived.is_(False))
    return session.scalars(stmt).all()


def get_form_by_slug(session: Session, slug: str) -> Optional[Form]:
    return session.scalar(select(Form).where(Form.slug == slug))


def list_form_versions(session: Session, form: Form) -> List[FormVersion]:
    stmt = (
        select(FormVersion)
        .where(FormVersion.form_id == form.id)
        .order_by(FormVersion.version.desc())
    )
    return session.scalars(stmt).all()


def update_form(session: Session, form: Form, payload: schemas.FormUpdate) -> Form:
    if form.is_archived:
        raise ValueError("Archived forms cannot be modified")

    form.title = payload.title
    form.description = payload.description
    form.version += 1
    form.updated_at = datetime.utcnow()

    new_questions = [
        _build_question_model(question)
        for question in sorted(payload.questions, key=lambda q: q.position)
    ]
    form.questions.clear()
    form.questions.extend(new_questions)

    session.flush()

    version_snapshot = FormVersion(
        form=form,
        version=form.version,
        title=form.title,
        description=form.description,
        questions_snapshot={"questions": _serialize_questions(form.questions)},
    )
    session.add(version_snapshot)
    session.refresh(form)
    return form


def set_form_archived(session: Session, form: Form, archived: bool) -> Form:
    form.is_archived = archived
    form.archived_at = datetime.utcnow() if archived else None
    form.updated_at = datetime.utcnow()
    session.flush()
    session.refresh(form)
    return form


def create_response_group(
    session: Session, form: Form, payload: schemas.ResponseGroupCreate
) -> ResponseGroup:
    if form.is_archived:
        raise ValueError("Archived forms cannot accept responses")

    response_group = ResponseGroup(
        form=form,
        respondent_identifier=payload.respondent_identifier,
        notes=payload.notes,
        form_version=form.version,
    )

    questions = {question.id: question for question in form.questions}
    answers: List[Answer] = []
    provided_question_ids: set[int] = set()

    for answer_payload in payload.answers:
        question = questions.get(answer_payload.question_id)
        if question is None:
            raise ValueError(
                f"Question id {answer_payload.question_id} is not part of form {form.slug}"
            )

        _validate_answer(question, answer_payload.value)
        provided_question_ids.add(question.id)
        answers.append(
            Answer(
                question=question,
                value=answer_payload.value,
            )
        )

    missing_required = [
        question.prompt
        for question in form.questions
        if question.required and question.id not in provided_question_ids
    ]
    if missing_required:
        raise ValueError(
            "Missing answers for required questions: " + ", ".join(missing_required)
        )

    response_group.answers = answers
    session.add(response_group)
    session.flush()
    session.refresh(response_group)
    return response_group


def list_responses_for_form(
    session: Session, form: Form, include_archived: bool = False
) -> List[ResponseGroup]:
    stmt = (
        select(ResponseGroup)
        .where(ResponseGroup.form_id == form.id)
        .order_by(ResponseGroup.submitted_at.desc())
    )
    if not include_archived:
        stmt = stmt.where(ResponseGroup.is_archived.is_(False))
    return session.scalars(stmt).all()


def get_response_group(
    session: Session, form: Form, response_group_id: int
) -> Optional[ResponseGroup]:
    stmt = select(ResponseGroup).where(
        ResponseGroup.id == response_group_id, ResponseGroup.form_id == form.id
    )
    return session.scalar(stmt)


def set_response_archived(
    session: Session, response_group: ResponseGroup, archived: bool
) -> ResponseGroup:
    response_group.is_archived = archived
    response_group.archived_at = datetime.utcnow() if archived else None
    session.flush()
    session.refresh(response_group)
    return response_group


def _validate_answer(question: Question, value: str) -> None:
    metadata = question.metadata or {}
    if question.type in {QuestionType.INTEGER, QuestionType.DECIMAL}:
        try:
            number = float(value)
        except ValueError as exc:
            raise ValueError(
                f"Answer for question '{question.prompt}' must be numeric"
            ) from exc

        min_value = metadata.get("min_value")
        max_value = metadata.get("max_value")
        if min_value is not None and number < float(min_value):
            raise ValueError(
                f"Answer for question '{question.prompt}' is below the minimum of {min_value}"
            )
        if max_value is not None and number > float(max_value):
            raise ValueError(
                f"Answer for question '{question.prompt}' exceeds the maximum of {max_value}"
            )

    if question.type in {QuestionType.SINGLE_CHOICE, QuestionType.MULTIPLE_CHOICE}:
        options = metadata.get("options") or []
        valid_values = {option["value"] for option in options}
        selected_values = [value]
        if question.type == QuestionType.MULTIPLE_CHOICE:
            selected_values = [item.strip() for item in value.split(",") if item.strip()]
        if not set(selected_values).issubset(valid_values):
            raise ValueError(
                f"Answer for question '{question.prompt}' includes invalid choices"
            )


def create_practice_overview_response(
    session: Session, payload: schemas.PracticeOverviewSubmission
) -> PracticeOverviewResponse:
    response = PracticeOverviewResponse(
        workstations=payload.workstations,
        onsite_server=payload.onsite_server,
        practice_management_software=payload.practice_management_software,
        imaging_software=payload.imaging_software,
        cloud_pms=payload.cloud_pms,
        notes=payload.notes,
        respondent_identifier=payload.respondent_identifier,
    )
    session.add(response)
    session.flush()
    session.refresh(response)
    return response


def list_practice_overview_responses(
    session: Session,
) -> List[PracticeOverviewResponse]:
    stmt = select(PracticeOverviewResponse).order_by(
        PracticeOverviewResponse.created_at.desc()
    )
    return session.scalars(stmt).all()
