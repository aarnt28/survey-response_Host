from __future__ import annotations

from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from . import crud, schemas
from .database import Base, engine, get_session

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Survey Response Orchestrator")

BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

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
def list_forms(
    include_archived: bool = False, session: Session = Depends(get_db_session)
):
    forms = crud.list_forms(session, include_archived=include_archived)
    return forms


@app.get("/forms/{slug}", response_model=schemas.FormRead)
def get_form(slug: str, session: Session = Depends(get_db_session)):
    form = crud.get_form_by_slug(session, slug)
    if not form:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Form not found")
    return form


@app.put("/forms/{slug}", response_model=schemas.FormRead)
def update_form(
    slug: str, payload: schemas.FormUpdate, session: Session = Depends(get_db_session)
):
    form = crud.get_form_by_slug(session, slug)
    if not form:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Form not found")

    try:
        form = crud.update_form(session, form, payload)
    except ValueError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return form


@app.post("/forms/{slug}/archive", response_model=schemas.FormRead)
def archive_form(
    slug: str, payload: schemas.ArchiveAction, session: Session = Depends(get_db_session)
):
    form = crud.get_form_by_slug(session, slug)
    if not form:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Form not found")

    form = crud.set_form_archived(session, form, payload.archived)
    return form


@app.get("/forms/{slug}/versions", response_model=list[schemas.FormVersionRead])
def list_form_versions(slug: str, session: Session = Depends(get_db_session)):
    form = crud.get_form_by_slug(session, slug)
    if not form:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Form not found")
    return crud.list_form_versions(session, form)


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
def list_responses(
    slug: str,
    include_archived: bool = False,
    session: Session = Depends(get_db_session),
):
    form = crud.get_form_by_slug(session, slug)
    if not form:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Form not found")
    return crud.list_responses_for_form(session, form, include_archived=include_archived)


@app.post(
    "/forms/{slug}/responses/{response_id}/archive",
    response_model=schemas.ResponseGroupRead,
)
def archive_response(
    slug: str,
    response_id: int,
    payload: schemas.ArchiveAction,
    session: Session = Depends(get_db_session),
):
    form = crud.get_form_by_slug(session, slug)
    if not form:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Form not found")

    response_group = crud.get_response_group(session, form, response_id)
    if not response_group:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Response not found")

    response_group = crud.set_response_archived(session, response_group, payload.archived)
    return response_group


@app.get("/", response_class=HTMLResponse)
def root_ui(request: Request):
    return templates.TemplateResponse("forms/index.html", {"request": request})


@app.get("/ui/forms", response_class=HTMLResponse)
def forms_ui(request: Request):
    return templates.TemplateResponse("forms/index.html", {"request": request})


@app.get("/ui/forms/{slug}", response_class=HTMLResponse)
def form_detail_ui(request: Request, slug: str):
    return templates.TemplateResponse("forms/detail.html", {"request": request, "slug": slug})
