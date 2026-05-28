import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker


load_dotenv()


def _normalize_database_url(database_url: str | None) -> str:
    if not database_url:
        raise RuntimeError(
            "DATABASE_URL is not set. Add it to .env or export it before starting the app."
        )
    # Accept both the postgres:// and postgresql+psycopg2:// styles
    if database_url.startswith("postgres://"):
        return "postgresql+psycopg2://" + database_url.removeprefix("postgres://")
    return database_url


DATABASE_URL = _normalize_database_url(
    os.getenv("DATABASE_URL")
)

# Engine options; keep sqlite connect args only if a sqlite URL is explicitly used
engine_options = {"pool_pre_ping": True}
if DATABASE_URL.startswith("sqlite"):
    engine_options["connect_args"] = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, **engine_options)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_database_url() -> str:
    return DATABASE_URL


def init_db() -> None:
    """Create database tables.

    This intentionally does not swallow OperationalError: the application
    requires the configured database to be reachable at startup so mis-
    configuration is visible immediately.
    """
    # Import model classes so SQLAlchemy knows about mapped classes.
    from backend.infrastructure.db_repo import (
        PatientRecord,
        PrescriptionRecord,
        ClinicalNoteRecord,
        LabReportRecord,
    )  # noqa: F401

    # Reference imported classes to avoid linting 'unused import' warnings.
    _MODEL_CLASSES = (PatientRecord, PrescriptionRecord, ClinicalNoteRecord, LabReportRecord)

    Base.metadata.create_all(bind=engine)