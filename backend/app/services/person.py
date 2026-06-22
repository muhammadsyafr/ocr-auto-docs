"""Aggregate one job (one ZIP = one person) into a single person record.

A ZIP for a person contains multiple documents (KTP, ijazah, employment letter).
Each target field is taken from whichever document extracted it with the highest
confidence. The photo is the KTP image (fallback: first image document).
"""
from app.models import Document, Job

TARGET_FIELDS = [
    "nik",
    "full_name",
    "place_of_birth",
    "date_of_birth",
    "company_name",
    "company_address",
]

IMAGE_EXT = (".jpg", ".jpeg", ".png", ".tiff", ".tif", ".bmp")


def _basename_stem(path: str) -> str:
    import os
    return os.path.splitext(os.path.basename(path))[0].lower()


def _is_photo_file(path: str) -> bool:
    """A file literally named PHOTO.<ext> is the person's face photo, not the KTP."""
    return _basename_stem(path) == "photo"


def build_person(job: Job) -> tuple[dict[str, str | None], Document | None]:
    """Return (merged fields, photo document) for a job.

    Photo column = the KTP scan. Selection is deterministic (docs sorted by name)
    and never the dedicated PHOTO.<ext> file, which often misclassifies as ktp.
    """
    best: dict[str, tuple[str | None, float]] = {f: (None, -1.0) for f in TARGET_FIELDS}
    ktp_by_name: Document | None = None
    ktp_by_type: Document | None = None
    first_image: Document | None = None

    # Stable order so the same zip/folder always yields the same photo.
    docs = sorted(
        (d for d in job.documents if d.status == "completed"),
        key=lambda d: (d.filename or "").lower(),
    )
    for d in docs:
        is_photo = _is_photo_file(d.source_path)
        stem = _basename_stem(d.source_path)
        if not is_photo:
            if "ktp" in stem and ktp_by_name is None:
                ktp_by_name = d
            if d.document_type == "ktp" and ktp_by_type is None:
                ktp_by_type = d
            if first_image is None and d.source_path.lower().endswith(IMAGE_EXT):
                first_image = d
        for r in d.results:
            if r.field_name in best and r.field_value:
                conf = r.confidence or 0.0
                if conf > best[r.field_name][1]:
                    best[r.field_name] = (r.field_value, conf)

    fields = {f: best[f][0] for f in TARGET_FIELDS}
    # Prefer the file named KTP, then a doc classified ktp, then any non-photo image.
    photo_doc = ktp_by_name or ktp_by_type or first_image
    return fields, photo_doc
