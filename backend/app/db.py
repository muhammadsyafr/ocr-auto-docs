"""SQLAlchemy engine + session."""
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.config import get_settings

settings = get_settings()

engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


def get_db():
    """FastAPI dependency yielding a DB session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create tables + lightweight idempotent migrations (MVP, no Alembic)."""
    from app import models  # noqa: F401  (register models)
    Base.metadata.create_all(bind=engine)
    _migrate()
    _ensure_default_session()


def _migrate():
    """Add columns introduced after the tables already existed."""
    from sqlalchemy import text
    stmts = [
        "ALTER TABLE jobs ADD COLUMN IF NOT EXISTS session_id VARCHAR",
        "ALTER TABLE people ADD COLUMN IF NOT EXISTS session_id VARCHAR",
        "ALTER TABLE people ADD COLUMN IF NOT EXISTS jenis_pelatihan TEXT",
        "ALTER TABLE people ADD COLUMN IF NOT EXISTS ket TEXT",
        "ALTER TABLE settings ADD COLUMN IF NOT EXISTS active_session_id VARCHAR",
    ]
    with engine.begin() as conn:
        for s in stmts:
            conn.execute(text(s))


def _ensure_default_session():
    """Guarantee at least one session exists and is active; tag orphan rows."""
    from app.models import Job, Person, Session, Setting
    db = SessionLocal()
    try:
        setting = db.get(Setting, 1)
        if setting is None:
            setting = Setting(id=1)
            db.add(setting)
            db.commit()

        active = setting.active_session_id
        if not active or db.get(Session, active) is None:
            sess = db.query(Session).order_by(Session.created_at.asc()).first()
            if sess is None:
                sess = Session(name="Default")
                db.add(sess)
                db.commit()
                db.refresh(sess)
            setting.active_session_id = sess.id
            db.commit()
            active = sess.id

        # Adopt any pre-session rows into the active session.
        db.query(Job).filter(Job.session_id.is_(None)).update({"session_id": active})
        db.query(Person).filter(Person.session_id.is_(None)).update({"session_id": active})
        db.commit()
    finally:
        db.close()
