from contextlib import contextmanager
import json
import hashlib
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Iterator, Optional

from sqlalchemy import JSON, Column, Date, DateTime, Float, Integer, String, Text, cast
from sqlalchemy.orm import Session

from backend.infrastructure import database as db
from backend.models.auth import UserRole
from backend.models.patient import ClinicalNote as ClinicalNoteModel
from backend.models.patient import LabReport as LabReportModel
from backend.models.patient import Prescription as PrescriptionModel


class PatientRecord(db.Base):
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(36), unique=True, index=True, nullable=False, default=lambda: str(uuid.uuid4()))
    role = Column(String(20), nullable=False, default=UserRole.patient.value)
    name = Column(String(255), nullable=False, default="")
    age = Column(Integer, nullable=False, default=0)
    email = Column(String(255), nullable=False, default="")
    password_hash = Column(String(128), nullable=False, default="")
    password_salt = Column(String(64), nullable=False, default="")
    risk_factors = Column(JSON, nullable=False, default=list)


class PrescriptionRecord(db.Base):
    __tablename__ = "prescriptions"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(String(36), unique=True, index=True, nullable=False)
    type = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    frequency = Column(String(50), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)
    calendar_path = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))


class ClinicalNoteRecord(db.Base):
    __tablename__ = "clinical_notes"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(String(36), unique=True, index=True, nullable=False)
    note = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))


class LabReportRecord(db.Base):
    __tablename__ = "lab_reports"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(String(36), index=True, nullable=False)
    name = Column(String(255), nullable=False)
    type = Column(String(255), nullable=False)
    report_date = Column(String(50), nullable=False)
    result_value = Column(Float, nullable=False)
    unit = Column(String(50), nullable=False)
    normal_range = Column(String(255), nullable=False)
    status = Column(String(50), nullable=False)


class AuthTokenRecord(db.Base):
    __tablename__ = "auth_tokens"

    id = Column(Integer, primary_key=True, index=True)
    token_hash = Column(String(64), unique=True, index=True, nullable=False)
    patient_id = Column(String(36), index=True, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)


class ConversationMessageRecord(db.Base):
    __tablename__ = "conversation_messages"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(String(36), index=True, nullable=False)
    role = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))


class ConversationSummaryRecord(db.Base):
    __tablename__ = "conversation_summaries"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(String(36), unique=True, index=True, nullable=False)
    summary = Column(Text, nullable=False, default="")
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))


def _hash_password(password: str, salt: str) -> str:
    return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), bytes.fromhex(salt), 120000).hex()


def _verify_password(password: str, salt: str, password_hash: str) -> bool:
    return secrets.compare_digest(_hash_password(password, salt), password_hash)


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _normalize_patient_id(patient_id: Any) -> str:
    return str(uuid.UUID(str(patient_id)))


def _patient_id_matches(column, patient_id: Any):
    return cast(column, String) == _normalize_patient_id(patient_id)


@contextmanager
def session_scope() -> Iterator[Session]:
    session = db.SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def _get_or_create_patient(session: Session, patient_id: str) -> PatientRecord:
    patient = session.query(PatientRecord).filter(_patient_id_matches(PatientRecord.user_id, patient_id)).one_or_none()
    if patient is None:
        patient = PatientRecord(user_id=patient_id, role=UserRole.patient.value, name="", age=0, email="", risk_factors=[])
        session.add(patient)
        session.flush()
    return patient


def _patient_to_dict(patient: Optional[PatientRecord]) -> Optional[dict]:
    if patient is None:
        return None
    return {
        "id": patient.user_id,
        "role": patient.role,
        "name": patient.name,
        "age": patient.age,
        "email": patient.email,
        "risk_factors": list(patient.risk_factors or []),
    }


def get_patient_record(patient_id: Any) -> Optional[dict]:
    with session_scope() as session:
        patient = session.query(PatientRecord).filter(_patient_id_matches(PatientRecord.user_id, patient_id)).one_or_none()
        return _patient_to_dict(patient)


def get_user_by_email(email: str) -> Optional[dict]:
    with session_scope() as session:
        patient = session.query(PatientRecord).filter_by(email=email.lower()).one_or_none()
        return _patient_to_dict(patient)


def create_user_account(
    *,
    name: str,
    email: str,
    password: str,
    role: UserRole,
    age: Optional[int] = None,
    risk_factors: Optional[list[str]] = None,
) -> dict:
    with session_scope() as session:
        normalized_email = email.lower().strip()
        existing = session.query(PatientRecord).filter_by(email=normalized_email).one_or_none()
        if existing is not None and existing.password_hash:
            raise ValueError("A user with this email already exists")

        if existing is None:
            user = PatientRecord(
                user_id=str(uuid.uuid4()),
                role=role.value,
                name=name,
                age=age or 0,
                email=normalized_email,
                password_salt=secrets.token_hex(16),
                password_hash="",
                risk_factors=list(risk_factors or []),
            )
            session.add(user)
        else:
            user = existing
            user.role = role.value
            user.name = name
            user.age = age or user.age
            user.email = normalized_email
            user.risk_factors = list(risk_factors or user.risk_factors or [])
            user.password_salt = secrets.token_hex(16)

        user.password_hash = _hash_password(password, user.password_salt)
        session.flush()
        return _patient_to_dict(user) or {}


def authenticate_user(email: str, password: str) -> Optional[dict]:
    with session_scope() as session:
        user = session.query(PatientRecord).filter_by(email=email.lower()).one_or_none()
        if user is None or not user.password_hash or not user.password_salt:
            return None
        if not _verify_password(password, user.password_salt, user.password_hash):
            return None
        return _patient_to_dict(user)


def create_access_token(user_id: Any, expires_minutes: int = 24 * 60) -> str:
    token = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=expires_minutes)
    with session_scope() as session:
        session.add(
            AuthTokenRecord(
                token_hash=_hash_token(token),
                patient_id=_normalize_patient_id(user_id),
                expires_at=expires_at,
            )
        )
    return token


def get_user_by_access_token(token: str) -> Optional[dict]:
    token_hash = _hash_token(token)
    now = datetime.now(timezone.utc)
    with session_scope() as session:
        token_record = session.query(AuthTokenRecord).filter_by(token_hash=token_hash).one_or_none()
        if token_record is None:
            return None
        if token_record.expires_at <= now:
            session.delete(token_record)
            return None
        user = session.query(PatientRecord).filter(_patient_id_matches(PatientRecord.user_id, token_record.patient_id)).one_or_none()
        return _patient_to_dict(user)


def upsert_patient_profile(
    patient_id: int,
    *,
    name: Optional[str] = None,
    age: Optional[int] = None,
    email: Optional[str] = None,
    risk_factors: Optional[list[str]] = None,
) -> dict:
    with session_scope() as session:
        patient = _get_or_create_patient(session, _normalize_patient_id(patient_id))
        if name is not None:
            patient.name = name
        if age is not None:
            patient.age = age
        if email is not None:
            patient.email = email
        if risk_factors is not None:
            patient.risk_factors = list(risk_factors)
        return _patient_to_dict(patient) or {}


def _normalize_risk_factors(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return []
        try:
            parsed = json.loads(stripped)
        except json.JSONDecodeError:
            return [line.strip(" -*\t") for line in stripped.splitlines() if line.strip()]
        if isinstance(parsed, list):
            return [str(item).strip() for item in parsed if str(item).strip()]
        if isinstance(parsed, str):
            return [parsed.strip()] if parsed.strip() else []
        return [str(parsed)]
    return [str(value).strip()]


def update_patient_risk_factors(patient_id: int, risk_factors: Any):
    normalized = _normalize_risk_factors(risk_factors)
    with session_scope() as session:
        patient = _get_or_create_patient(session, _normalize_patient_id(patient_id))
        patient.risk_factors = normalized
        return normalized


def get_patient_name(user_id: int) -> str:
    patient = get_patient_record(user_id)
    if patient:
        return patient.get("name", "")
    return ""


def get_patient_risk_factors(patient_id: int) -> list:
    patient = get_patient_record(patient_id)
    if patient:
        return list(patient.get("risk_factors", []))
    return []


def get_email(patient_id: int) -> str:
    patient = get_patient_record(patient_id)
    if patient:
        return patient.get("email", "")
    return ""


def get_prescription_history(patient_id: Any) -> list[dict]:
    with session_scope() as session:
        records = (
            session.query(PrescriptionRecord)
            .filter(_patient_id_matches(PrescriptionRecord.patient_id, patient_id))
            .order_by(PrescriptionRecord.id.desc())
            .all()
        )
        return [
            {
                "id": record.id,
                "patient_id": record.patient_id,
                "type": record.type,
                "description": record.description,
                "frequency": record.frequency,
                "start_date": record.start_date,
                "end_date": record.end_date,
                "calendar_path": record.calendar_path,
                "created_at": record.created_at,
            }
            for record in records
        ]


def get_clinical_note_history(patient_id: Any) -> list[dict]:
    with session_scope() as session:
        records = (
            session.query(ClinicalNoteRecord)
            .filter(_patient_id_matches(ClinicalNoteRecord.patient_id, patient_id))
            .order_by(ClinicalNoteRecord.id.desc())
            .all()
        )
        return [
            {
                "id": record.id,
                "patient_id": record.patient_id,
                "note": record.note,
                "created_at": record.created_at,
            }
            for record in records
        ]


def get_lab_report_history(patient_id: Any) -> list[dict]:
    with session_scope() as session:
        records = (
            session.query(LabReportRecord)
            .filter(_patient_id_matches(LabReportRecord.patient_id, patient_id))
            .order_by(LabReportRecord.report_date.desc(), LabReportRecord.id.desc())
            .all()
        )
        return [
            {
                "id": record.id,
                "patient_id": record.patient_id,
                "name": record.name,
                "type": record.type,
                "report_date": record.report_date,
                "result_value": record.result_value,
                "unit": record.unit,
                "normal_range": record.normal_range,
                "status": record.status,
            }
            for record in records
        ]


def get_patient_chat_context(patient_id: Any) -> dict:
    patient = get_patient_record(patient_id) or {}
    return {
        "patient": patient,
        "prescriptions": get_prescription_history(patient_id),
        "clinical_notes": get_clinical_note_history(patient_id),
        "lab_reports": get_lab_report_history(patient_id),
    }


def get_recent_conversation_messages(patient_id: Any, *, limit: int = 12) -> list[dict]:
    with session_scope() as session:
        records = (
            session.query(ConversationMessageRecord)
            .filter(_patient_id_matches(ConversationMessageRecord.patient_id, patient_id))
            .order_by(ConversationMessageRecord.created_at.desc(), ConversationMessageRecord.id.desc())
            .limit(limit)
            .all()
        )
        return [
            {
                "role": record.role,
                "content": record.content,
                "created_at": record.created_at,
            }
            for record in reversed(records)
        ]


def get_all_conversation_messages(patient_id: Any) -> list[dict]:
    with session_scope() as session:
        records = (
            session.query(ConversationMessageRecord)
            .filter(_patient_id_matches(ConversationMessageRecord.patient_id, patient_id))
            .order_by(ConversationMessageRecord.created_at.asc(), ConversationMessageRecord.id.asc())
            .all()
        )
        return [
            {
                "role": record.role,
                "content": record.content,
                "created_at": record.created_at,
            }
            for record in records
        ]


def append_conversation_message(patient_id: Any, role: str, content: str) -> None:
    message = (content or "").strip()
    if not message:
        return

    with session_scope() as session:
        session.add(
            ConversationMessageRecord(
                patient_id=_normalize_patient_id(patient_id),
                role=role,
                content=message,
            )
        )


def get_conversation_summary(patient_id: Any) -> str:
    with session_scope() as session:
        record = session.query(ConversationSummaryRecord).filter(_patient_id_matches(ConversationSummaryRecord.patient_id, patient_id)).one_or_none()
        if record is None:
            return ""
        return record.summary or ""


def set_conversation_summary(patient_id: Any, summary: str) -> str:
    normalized_patient_id = _normalize_patient_id(patient_id)
    cleaned_summary = (summary or "").strip()

    with session_scope() as session:
        record = session.query(ConversationSummaryRecord).filter(_patient_id_matches(ConversationSummaryRecord.patient_id, normalized_patient_id)).one_or_none()
        if record is None:
            record = ConversationSummaryRecord(patient_id=normalized_patient_id, summary=cleaned_summary)
            session.add(record)
        else:
            record.summary = cleaned_summary
            record.updated_at = datetime.now(timezone.utc)
        return cleaned_summary


def get_recent_conversation_messages(patient_id: Any, *, limit: int = 8) -> list[dict]:
    with session_scope() as session:
        records = (
            session.query(ConversationMessageRecord)
            .filter_by(patient_id=_normalize_patient_id(patient_id))
            .order_by(ConversationMessageRecord.created_at.desc(), ConversationMessageRecord.id.desc())
            .limit(limit)
            .all()
        )
        return [
            {
                "role": record.role,
                "content": record.content,
                "created_at": record.created_at,
            }
            for record in reversed(records)
        ]


def get_message_count(patient_id: Any) -> int:
    with session_scope() as session:
        return (
            session.query(ConversationMessageRecord)
            .filter(_patient_id_matches(ConversationMessageRecord.patient_id, patient_id))
            .count()
        )


def prune_conversation_messages(patient_id: Any, *, keep_last: int = 8) -> None:
    normalized_patient_id = _normalize_patient_id(patient_id)
    with session_scope() as session:
        records = (
            session.query(ConversationMessageRecord)
            .filter(_patient_id_matches(ConversationMessageRecord.patient_id, normalized_patient_id))
            .order_by(ConversationMessageRecord.created_at.desc(), ConversationMessageRecord.id.desc())
            .all()
        )
        for record in records[keep_last:]:
            session.delete(record)


def summarize_conversation_anchor(patient_id: Any) -> str:
    patient_context = get_patient_chat_context(patient_id)
    summary = get_conversation_summary(patient_id)
    recent_messages = get_recent_conversation_messages(patient_id, limit=8)

    return (
        f"Protected anchor summary:\n{summary}\n\n"
        f"Patient context:\n{json.dumps(patient_context, default=str, indent=2)}\n\n"
        f"Recent conversation:\n{json.dumps(recent_messages, default=str, indent=2)}"
    ).strip()


def upsert_prescription(prescription: PrescriptionModel) -> dict:
    patient_id = _normalize_patient_id(prescription.patient_id)
    with session_scope() as session:
        _get_or_create_patient(session, patient_id)
        record = session.query(PrescriptionRecord).filter(_patient_id_matches(PrescriptionRecord.patient_id, patient_id)).one_or_none()
        if record is None:
            record = PrescriptionRecord(patient_id=patient_id)
            session.add(record)
        if prescription.id is not None:
            record.id = prescription.id
        record.type = prescription.type
        record.description = prescription.description
        record.frequency = prescription.frequency
        record.start_date = prescription.start_date
        record.end_date = prescription.end_date
        record.calendar_path = prescription.calendar_path
        session.flush()
        return {
            "id": record.id,
            "patient_id": record.patient_id,
            "type": record.type,
            "description": record.description,
            "frequency": record.frequency,
            "start_date": record.start_date,
            "end_date": record.end_date,
            "calendar_path": record.calendar_path,
            "created_at": record.created_at,
        }


def update_prescription(prescription: PrescriptionModel) -> Optional[dict]:
    patient_id = _normalize_patient_id(prescription.patient_id)
    with session_scope() as session:
        record = session.query(PrescriptionRecord).filter(_patient_id_matches(PrescriptionRecord.patient_id, patient_id)).one_or_none()
        if record is None:
            return None
        _get_or_create_patient(session, patient_id)
        if prescription.id is not None:
            record.id = prescription.id
        record.type = prescription.type
        record.description = prescription.description
        record.frequency = prescription.frequency
        record.start_date = prescription.start_date
        record.end_date = prescription.end_date
        record.calendar_path = prescription.calendar_path
        return prescription.model_dump()


def delete_prescription(patient_id: int) -> bool:
    with session_scope() as session:
        record = session.query(PrescriptionRecord).filter(_patient_id_matches(PrescriptionRecord.patient_id, patient_id)).one_or_none()
        if record is None:
            return False
        session.delete(record)
        return True


def get_prescription(patient_id: int) -> dict:
    with session_scope() as session:
        record = session.query(PrescriptionRecord).filter(_patient_id_matches(PrescriptionRecord.patient_id, patient_id)).one_or_none()
        if record is None:
            return {}
        return {
            "id": record.id,
            "patient_id": record.patient_id,
            "type": record.type,
            "description": record.description,
            "frequency": record.frequency,
            "start_date": record.start_date,
            "end_date": record.end_date,
            "calendar_path": record.calendar_path,
            "created_at": record.created_at,
        }


def upsert_clinical_note(clinical_note: ClinicalNoteModel) -> dict:
    patient_id = _normalize_patient_id(clinical_note.patient_id)
    with session_scope() as session:
        _get_or_create_patient(session, patient_id)
        record = session.query(ClinicalNoteRecord).filter(_patient_id_matches(ClinicalNoteRecord.patient_id, patient_id)).one_or_none()
        if record is None:
            record = ClinicalNoteRecord(patient_id=patient_id)
            session.add(record)
        if clinical_note.id is not None:
            record.id = clinical_note.id
        record.note = clinical_note.note
        session.flush()
        return {
            "id": record.id,
            "patient_id": record.patient_id,
            "note": record.note,
            "created_at": record.created_at,
        }


def update_clinical_note(clinical_note: ClinicalNoteModel) -> Optional[dict]:
    patient_id = _normalize_patient_id(clinical_note.patient_id)
    with session_scope() as session:
        record = session.query(ClinicalNoteRecord).filter(_patient_id_matches(ClinicalNoteRecord.patient_id, patient_id)).one_or_none()
        if record is None:
            return None
        _get_or_create_patient(session, patient_id)
        if clinical_note.id is not None:
            record.id = clinical_note.id
        record.note = clinical_note.note
        return clinical_note.model_dump()


def delete_clinical_note(patient_id: int) -> bool:
    with session_scope() as session:
        record = session.query(ClinicalNoteRecord).filter(_patient_id_matches(ClinicalNoteRecord.patient_id, patient_id)).one_or_none()
        if record is None:
            return False
        session.delete(record)
        return True


def get_clinical_note(patient_id: int) -> dict:
    with session_scope() as session:
        record = session.query(ClinicalNoteRecord).filter(_patient_id_matches(ClinicalNoteRecord.patient_id, patient_id)).one_or_none()
        if record is None:
            return {}
        return {
            "id": record.id,
            "patient_id": record.patient_id,
            "note": record.note,
            "created_at": record.created_at,
        }


def upsert_lab_report(lab_report: LabReportModel) -> dict:
    patient_id = _normalize_patient_id(lab_report.patient_id)
    with session_scope() as session:
        _get_or_create_patient(session, patient_id)
        # ensure report_date is filled; accept datetime or string from the model
        report_dt = getattr(lab_report, "report_date", None)
        if hasattr(report_dt, "isoformat"):
            report_date_str = report_dt.astimezone(timezone.utc).isoformat()
        elif report_dt:
            report_date_str = str(report_dt)
        else:
            report_date_str = datetime.now(timezone.utc).isoformat()

        record = (
            session.query(LabReportRecord)
            .filter(_patient_id_matches(LabReportRecord.patient_id, patient_id), LabReportRecord.report_date == report_date_str)
            .one_or_none()
        )
        if record is None:
            record = LabReportRecord(patient_id=patient_id, report_date=report_date_str)
            session.add(record)
        if lab_report.id is not None:
            record.id = lab_report.id
        record.name = lab_report.name
        record.type = lab_report.type
        record.result_value = lab_report.result_value
        record.unit = lab_report.unit
        record.normal_range = lab_report.normal_range
        record.status = lab_report.status
        session.flush()
        return {
            "id": record.id,
            "patient_id": record.patient_id,
            "name": record.name,
            "type": record.type,
            "report_date": record.report_date,
            "result_value": record.result_value,
            "unit": record.unit,
            "normal_range": record.normal_range,
            "status": record.status,
        }


def update_lab_report(lab_report: LabReportModel) -> Optional[dict]:
    patient_id = _normalize_patient_id(lab_report.patient_id)
    with session_scope() as session:
        record = (
            session.query(LabReportRecord)
            .filter(_patient_id_matches(LabReportRecord.patient_id, patient_id), LabReportRecord.report_date == lab_report.report_date)
            .one_or_none()
        )
        if record is None:
            return None
        _get_or_create_patient(session, patient_id)
        if lab_report.id is not None:
            record.id = lab_report.id
        record.name = lab_report.name
        record.type = lab_report.type
        record.result_value = lab_report.result_value
        record.unit = lab_report.unit
        record.normal_range = lab_report.normal_range
        record.status = lab_report.status
        return lab_report.model_dump()


def delete_lab_report(patient_id: int, report_date: str) -> bool:
    with session_scope() as session:
        record = (
            session.query(LabReportRecord)
            .filter(_patient_id_matches(LabReportRecord.patient_id, patient_id), LabReportRecord.report_date == report_date)
            .one_or_none()
        )
        if record is None:
            return False
        session.delete(record)
        return True


def get_lab_report(patient_id: int, report_date: str) -> dict:
    with session_scope() as session:
        record = (
            session.query(LabReportRecord)
            .filter(_patient_id_matches(LabReportRecord.patient_id, patient_id), LabReportRecord.report_date == report_date)
            .one_or_none()
        )
        if record is None:
            return {}
        return {
            "id": record.id,
            "patient_id": record.patient_id,
            "name": record.name,
            "type": record.type,
            "report_date": record.report_date,
            "result_value": record.result_value,
            "unit": record.unit,
            "normal_range": record.normal_range,
            "status": record.status,
        }