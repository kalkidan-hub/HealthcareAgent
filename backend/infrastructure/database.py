import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy import inspect, text
from sqlalchemy.orm import declarative_base, sessionmaker
import uuid


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
        AuthTokenRecord,
        ConversationMessageRecord,
        ConversationSummaryRecord,
        PatientRecord,
        PrescriptionRecord,
        ClinicalNoteRecord,
        LabReportRecord,
    )  # noqa: F401

    # Reference imported classes to avoid linting 'unused import' warnings.
    _MODEL_CLASSES = (
        AuthTokenRecord,
        ConversationMessageRecord,
        ConversationSummaryRecord,
        PatientRecord,
        PrescriptionRecord,
        ClinicalNoteRecord,
        LabReportRecord,
    )

    Base.metadata.create_all(bind=engine)

    _migrate_uuid_user_ids()


def _migrate_uuid_user_ids() -> None:
    with engine.begin() as connection:
        inspector = inspect(connection)

        if "patients" not in inspector.get_table_names():
            return

        patient_columns = {column["name"] for column in inspector.get_columns("patients")}
        if "user_id" not in patient_columns:
            connection.execute(text("ALTER TABLE patients ADD COLUMN user_id VARCHAR(36)"))
            rows = connection.execute(text("SELECT id FROM patients WHERE user_id IS NULL OR user_id = ''")).fetchall()
            for row in rows:
                connection.execute(
                    text("UPDATE patients SET user_id = :user_id WHERE id = :id"),
                    {"user_id": str(uuid.uuid4()), "id": row.id},
                )
            connection.execute(text("ALTER TABLE patients ALTER COLUMN user_id SET NOT NULL"))
            connection.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ix_patients_user_id ON patients (user_id)"))

        if "role" not in patient_columns:
            connection.execute(text("ALTER TABLE patients ADD COLUMN role VARCHAR(20)"))
            connection.execute(text("UPDATE patients SET role = 'patient' WHERE role IS NULL OR role = ''"))
            connection.execute(text("ALTER TABLE patients ALTER COLUMN role SET NOT NULL"))

        if "password_hash" not in patient_columns:
            connection.execute(text("ALTER TABLE patients ADD COLUMN password_hash VARCHAR(128)"))
            connection.execute(text("UPDATE patients SET password_hash = '' WHERE password_hash IS NULL"))
            connection.execute(text("ALTER TABLE patients ALTER COLUMN password_hash SET NOT NULL"))

        if "password_salt" not in patient_columns:
            connection.execute(text("ALTER TABLE patients ADD COLUMN password_salt VARCHAR(64)"))
            connection.execute(text("UPDATE patients SET password_salt = '' WHERE password_salt IS NULL"))
            connection.execute(text("ALTER TABLE patients ALTER COLUMN password_salt SET NOT NULL"))

        table_updates = {
            "prescriptions": ["patient_id"],
            "clinical_notes": ["patient_id"],
            "lab_reports": ["patient_id"],
            "auth_tokens": ["patient_id"],
            "conversation_messages": ["patient_id"],
            "conversation_summaries": ["patient_id"],
        }

        for table_name, columns in table_updates.items():
            if table_name not in inspector.get_table_names():
                continue
            table_columns = {column["name"] for column in inspector.get_columns(table_name)}
            if "patient_uuid" not in table_columns and "patient_id" in table_columns:
                connection.execute(text(f"ALTER TABLE {table_name} ADD COLUMN patient_uuid VARCHAR(36)"))
                connection.execute(
                    text(
                        f"""
                        UPDATE {table_name} AS child
                        SET patient_uuid = parent.user_id
                        FROM patients AS parent
                        WHERE child.patient_id::text = parent.id::text
                        """
                    )
                )
                connection.execute(text(f"ALTER TABLE {table_name} DROP COLUMN patient_id"))
                connection.execute(text(f"ALTER TABLE {table_name} RENAME COLUMN patient_uuid TO patient_id"))