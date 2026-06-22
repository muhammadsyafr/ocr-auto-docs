"""Master document endpoints: push a job's person, list/remove people, download Excel."""
import os

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.deps import active_session_id
from app.db import get_db
from app.models import Job, Person
from app.models.schemas import PersonOut, PersonUpdate
from app.services import excel
from app.services.person import build_person

router = APIRouter(prefix="/api/doc", tags=["doc"])


def _zip_name(job: Job) -> str:
    base = os.path.basename(job.source_path.rstrip("/"))
    return base or job.id[:8]


def _upper(v: str | None) -> str | None:
    return v.upper() if v else v


def _all_people(db: Session):
    sid = active_session_id(db)
    return (
        db.query(Person)
        .filter(Person.session_id == sid)
        .order_by(Person.created_at.asc())
        .all()
    )


@router.post("/push/{job_id}", response_model=PersonOut)
def push_to_doc(job_id: str, db: Session = Depends(get_db)):
    """Aggregate a job (1 ZIP = 1 person) into the People doc (upsert by job_id)."""
    job = db.get(Job, job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    if job.status != "completed":
        raise HTTPException(400, f"Job not completed (status={job.status})")

    fields, photo_doc = build_person(job)
    if not any(fields.values()):
        raise HTTPException(400, "No extracted data to push for this job")

    photo_path = None
    if photo_doc:
        photo_path = excel.make_thumbnail(photo_doc.source_path, job_id)

    person = db.get(Person, job_id)
    if not person:
        person = Person(job_id=job_id)
        db.add(person)
    person.session_id = job.session_id
    person.zip_name = _zip_name(job)
    person.nik = fields.get("nik")
    person.full_name = _upper(fields.get("full_name"))
    person.place_of_birth = _upper(fields.get("place_of_birth"))
    person.date_of_birth = fields.get("date_of_birth")
    person.company_name = fields.get("company_name")
    person.company_address = fields.get("company_address")
    if photo_path:
        person.photo_path = photo_path
    db.commit()
    db.refresh(person)
    return person


@router.get("/people", response_model=list[PersonOut])
def list_people(db: Session = Depends(get_db)):
    return _all_people(db)


@router.patch("/people/{job_id}", response_model=PersonOut)
def update_person(job_id: str, patch: PersonUpdate, db: Session = Depends(get_db)):
    """Manually edit a person's extracted values (fix OCR mistakes)."""
    person = db.get(Person, job_id)
    if not person:
        raise HTTPException(404, "Person not in doc")
    for field, value in patch.model_dump(exclude_unset=True).items():
        # Treat empty string as clearing the field.
        setattr(person, field, value if (value is None or value != "") else None)
    db.commit()
    db.refresh(person)
    return person


@router.get("/people/{job_id}/photo")
def person_photo(job_id: str, db: Session = Depends(get_db)):
    person = db.get(Person, job_id)
    if not person or not person.photo_path or not os.path.exists(person.photo_path):
        raise HTTPException(404, "No photo")
    return FileResponse(person.photo_path, media_type="image/png")


@router.delete("/people/{job_id}")
def remove_person(job_id: str, db: Session = Depends(get_db)):
    """Remove a specific person from the doc (and their photo thumbnail)."""
    person = db.get(Person, job_id)
    if not person:
        raise HTTPException(404, "Person not in doc")
    if person.photo_path and os.path.exists(person.photo_path):
        try:
            os.remove(person.photo_path)
        except OSError:
            pass
    db.delete(person)
    db.commit()
    return {"removed": job_id}


@router.get("/info")
def doc_info(db: Session = Depends(get_db)):
    return {"rows": len(_all_people(db))}


@router.get("/download")
def doc_download(db: Session = Depends(get_db)):
    """Regenerate master.xlsx from the People table and download it."""
    people = _all_people(db)
    if not people:
        raise HTTPException(404, "No people in doc yet — push a completed job first")
    path = excel.generate_workbook(people)
    return FileResponse(
        path,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename="people.xlsx",
    )
