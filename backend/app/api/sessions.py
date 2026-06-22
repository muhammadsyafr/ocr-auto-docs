"""Session (workspace) endpoints: list/create/select/delete.

Each session scopes its own jobs, results and people. Switching sessions gives
a clean slate; data is isolated per session.
"""
import os

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session as DbSession

from app.api.deps import active_session_id
from app.db import get_db
from app.models import Job, Person, Session, Setting

router = APIRouter(prefix="/api/sessions", tags=["sessions"])


class SessionIn(BaseModel):
    name: str


class SessionOut(BaseModel):
    id: str
    name: str
    active: bool
    jobs: int
    people: int

    class Config:
        from_attributes = True


def _to_out(db: DbSession, s: Session, active: str | None) -> SessionOut:
    return SessionOut(
        id=s.id,
        name=s.name,
        active=s.id == active,
        jobs=db.query(Job).filter(Job.session_id == s.id).count(),
        people=db.query(Person).filter(Person.session_id == s.id).count(),
    )


@router.get("", response_model=list[SessionOut])
def list_sessions(db: DbSession = Depends(get_db)):
    active = active_session_id(db)
    rows = db.query(Session).order_by(Session.created_at.asc()).all()
    return [_to_out(db, s, active) for s in rows]


@router.post("", response_model=SessionOut)
def create_session(body: SessionIn, db: DbSession = Depends(get_db)):
    name = body.name.strip() or "Untitled"
    s = Session(name=name)
    db.add(s)
    db.commit()
    db.refresh(s)
    # Newly created session becomes active.
    setting = db.get(Setting, 1)
    setting.active_session_id = s.id
    db.commit()
    return _to_out(db, s, s.id)


@router.put("/{session_id}/activate", response_model=SessionOut)
def activate_session(session_id: str, db: DbSession = Depends(get_db)):
    s = db.get(Session, session_id)
    if not s:
        raise HTTPException(404, "Session not found")
    setting = db.get(Setting, 1)
    setting.active_session_id = s.id
    db.commit()
    return _to_out(db, s, s.id)


@router.delete("/{session_id}")
def delete_session(session_id: str, db: DbSession = Depends(get_db)):
    s = db.get(Session, session_id)
    if not s:
        raise HTTPException(404, "Session not found")

    # Remove this session's people (+ their photos) and jobs (+ docs/results).
    people = db.query(Person).filter(Person.session_id == session_id).all()
    for p in people:
        if p.photo_path and os.path.exists(p.photo_path):
            try:
                os.remove(p.photo_path)
            except OSError:
                pass
        db.delete(p)
    for job in db.query(Job).filter(Job.session_id == session_id).all():
        db.delete(job)  # cascades documents + extraction_results
    db.delete(s)
    db.commit()

    # If we deleted the active session, fall back to another (create one if none).
    setting = db.get(Setting, 1)
    if setting.active_session_id == session_id:
        other = db.query(Session).order_by(Session.created_at.asc()).first()
        if other is None:
            other = Session(name="Default")
            db.add(other)
            db.commit()
            db.refresh(other)
        setting.active_session_id = other.id
        db.commit()
    return {"deleted": session_id, "active": setting.active_session_id}
