from __future__ import annotations

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from . import crud, schemas
from .database import Base, engine, get_session

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Survey Response Orchestrator")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_db_session() -> Session:
    with get_session() as session:
        yield session


@app.post(
    "/forms",
    response_model=schemas.FormRead,
    status_code=status.HTTP_201_CREATED,
)
def create_form(payload: schemas.FormCreate, session: Session = Depends(get_db_session)):
    try:
        form = crud.create_form(session, payload)
    except crud.FormAlreadyExistsError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return form


@app.get("/forms", response_model=list[schemas.FormRead])
def list_forms(session: Session = Depends(get_db_session)):
    forms = crud.list_forms(session)
    return forms


@app.get("/forms/{slug}", response_model=schemas.FormRead)
def get_form(slug: str, session: Session = Depends(get_db_session)):
    form = crud.get_form_by_slug(session, slug)
    if not form:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Form not found")
    return form


@app.post(
    "/forms/{slug}/responses",
    response_model=schemas.ResponseGroupRead,
    status_code=status.HTTP_201_CREATED,
)
def submit_response(
    slug: str, payload: schemas.ResponseGroupCreate, session: Session = Depends(get_db_session)
):
    form = crud.get_form_by_slug(session, slug)
    if not form:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Form not found")

    try:
        response_group = crud.create_response_group(session, form, payload)
    except ValueError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return response_group


@app.get(
    "/forms/{slug}/responses",
    response_model=list[schemas.ResponseGroupRead],
)
def list_responses(slug: str, session: Session = Depends(get_db_session)):
    form = crud.get_form_by_slug(session, slug)
    if not form:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Form not found")
    return crud.list_responses_for_form(session, form)
