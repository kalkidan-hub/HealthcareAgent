from contextlib import contextmanager
import json
import hashlib
import secrets
import uuid
from datetime import date, datetime, timedelta, timezone
from typing import Any, Iterator, Optional

from sqlalchemy import JSON, Column, Date, DateTime, Float, Integer, String, Text, cast
from sqlalchemy import UniqueConstraint
from sqlalchemy.orm import Session

from backend.infrastructure import database as db
from backend.models.auth import UserRole
from backend.models.patient import ClinicalNote as ClinicalNoteModel
from backend.models.patient import LabReport as LabReportModel
from backend.models.patient import Prescription as PrescriptionModel
from backend.models.patient import Vitals as VitalsModel


class PatientRecord(db.Base):
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(36), unique=True, index=True, nullable=False, default=lambda: str(uuid.uuid4()))
    role = Column(String(20), nullable=False, default=UserRole.patient.value)
    name = Column(String(255), nullable=False, default="")
    age = Column(Integer, nullable=False, default=0)
    email = Column(String(255), nullable=False, default="")
    sex = Column(String(50), nullable=True)
    contact_number = Column(String(50), nullable=True)
    emergency_number = Column(String(50), nullable=True)
    password_hash = Column(String(128), nullable=False, default="")
    password_salt = Column(String(64), nullable=False, default="")
    risk_factors = Column(JSON, nullable=False, default=list)


class PrescriptionRecord(db.Base):
    __tablename__ = "prescriptions"

    id = Column(Integer, primary_key=True, index=True)
    prescription_id = Column(String(36), unique=True, index=True, nullable=False, default=lambda: str(uuid.uuid4()))
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


class VitalsRecord(db.Base):
    __tablename__ = "vitals"
    __table_args__ = (UniqueConstraint("patient_id", "recorded_at", name="uq_vitals_patient_recorded_at"),)

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(String(36), index=True, nullable=False)
    recorded_at = Column(String(50), nullable=False)
    systolic_bp = Column(Integer, nullable=True)
    diastolic_bp = Column(Integer, nullable=True)
    heart_rate = Column(Integer, nullable=True)
    respiratory_rate = Column(Integer, nullable=True)
    temperature_c = Column(Float, nullable=True)
    spo2 = Column(Integer, nullable=True)
    weight_kg = Column(Float, nullable=True)
    height_cm = Column(Float, nullable=True)
    notes = Column(Text, nullable=True)


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
    try:
        return str(uuid.UUID(str(patient_id)))
    except (TypeError, ValueError):
        return str(patient_id)


def _resolve_patient_user_id(session: Session, patient_id: Any) -> str:
    normalized = _normalize_patient_id(patient_id)
    try:
        uuid.UUID(normalized)
        return normalized
    except (TypeError, ValueError):
        pass

    if isinstance(patient_id, int) or (isinstance(patient_id, str) and patient_id.isdigit()):
        legacy_id = int(patient_id)
        legacy_patient = session.query(PatientRecord).filter(PatientRecord.id == legacy_id).one_or_none()
        if legacy_patient is not None:
            return legacy_patient.user_id

    return normalized


def _patient_id_matches(column, patient_id: Any):
    return cast(column, String) == _normalize_patient_id(patient_id)


def _normalize_datetime_string(value: Any) -> str:
    if isinstance(value, datetime):
        parsed = value
    else:
        text_value = str(value).strip()
        if not text_value:
            return text_value
        try:
            parsed = datetime.fromisoformat(text_value)
        except ValueError:
            return text_value
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc).isoformat()


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
    resolved_patient_id = _resolve_patient_user_id(session, patient_id)
    patient = session.query(PatientRecord).filter(_patient_id_matches(PatientRecord.user_id, resolved_patient_id)).one_or_none()
    if patient is None:
        patient = PatientRecord(user_id=resolved_patient_id, role=UserRole.patient.value, name="", age=0, email="", risk_factors=[])
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
        "sex": patient.sex,
        "contact_number": patient.contact_number,
        "emergency_number": patient.emergency_number,
        "risk_factors": list(patient.risk_factors or []),
    }


def get_patient_record(patient_id: Any) -> Optional[dict]:
    with session_scope() as session:
        resolved_patient_id = _resolve_patient_user_id(session, patient_id)
        patient = session.query(PatientRecord).filter(_patient_id_matches(PatientRecord.user_id, resolved_patient_id)).one_or_none()
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
    sex: Optional[str] = None,
    contact_number: Optional[str] = None,
    emergency_number: Optional[str] = None,
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
                sex=sex,
                contact_number=contact_number,
                emergency_number=emergency_number,
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
            user.sex = sex if sex is not None else user.sex
            user.contact_number = contact_number if contact_number is not None else user.contact_number
            user.emergency_number = emergency_number if emergency_number is not None else user.emergency_number
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
                patient_id=_resolve_patient_user_id(session, user_id),
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
        resolved_patient_id = _resolve_patient_user_id(session, token_record.patient_id)
        user = session.query(PatientRecord).filter(_patient_id_matches(PatientRecord.user_id, resolved_patient_id)).one_or_none()
        return _patient_to_dict(user)


def upsert_patient_profile(
    patient_id: int,
    *,
    name: Optional[str] = None,
    age: Optional[int] = None,
    email: Optional[str] = None,
    sex: Optional[str] = None,
    contact_number: Optional[str] = None,
    emergency_number: Optional[str] = None,
    risk_factors: Optional[list[str]] = None,
) -> dict:
    with session_scope() as session:
        patient = _get_or_create_patient(session, patient_id)
        if name is not None:
            patient.name = name
        if age is not None:
            patient.age = age
        if email is not None:
            normalized_email = email.lower().strip()
            existing = session.query(PatientRecord).filter_by(email=normalized_email).one_or_none()
            if existing is not None and existing.user_id != patient.user_id:
                raise ValueError("A user with this email already exists")
            patient.email = normalized_email
        if sex is not None:
            patient.sex = sex
        if contact_number is not None:
            patient.contact_number = contact_number
        if emergency_number is not None:
            patient.emergency_number = emergency_number
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
        patient = _get_or_create_patient(session, patient_id)
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
        resolved_patient_id = _resolve_patient_user_id(session, patient_id)
        records = (
            session.query(PrescriptionRecord)
            .filter(_patient_id_matches(PrescriptionRecord.patient_id, resolved_patient_id))
            .order_by(PrescriptionRecord.created_at.desc(), PrescriptionRecord.id.desc())
            .all()
        )
        return [
            {
                "id": record.prescription_id,
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
        resolved_patient_id = _resolve_patient_user_id(session, patient_id)
        records = (
            session.query(ClinicalNoteRecord)
            .filter(_patient_id_matches(ClinicalNoteRecord.patient_id, resolved_patient_id))
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
        resolved_patient_id = _resolve_patient_user_id(session, patient_id)
        records = (
            session.query(LabReportRecord)
            .filter(_patient_id_matches(LabReportRecord.patient_id, resolved_patient_id))
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


def _coerce_timeline_timestamp(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value
    if isinstance(value, date):
        return datetime.combine(value, datetime.min.time(), tzinfo=timezone.utc)
    if isinstance(value, str):
        text_value = value.strip()
        if not text_value:
            return datetime.min.replace(tzinfo=timezone.utc)
        try:
            parsed = datetime.fromisoformat(text_value)
        except ValueError:
            try:
                parsed_date = date.fromisoformat(text_value)
                return datetime.combine(parsed_date, datetime.min.time(), tzinfo=timezone.utc)
            except ValueError:
                return datetime.min.replace(tzinfo=timezone.utc)
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=timezone.utc)
        return parsed
    return datetime.min.replace(tzinfo=timezone.utc)


def get_patient_history(patient_id: Any) -> list[dict]:
    with session_scope() as session:
        resolved_patient_id = _resolve_patient_user_id(session, patient_id)

        timeline: list[dict] = []

        prescriptions = (
            session.query(PrescriptionRecord)
            .filter(_patient_id_matches(PrescriptionRecord.patient_id, resolved_patient_id))
            .all()
        )
        for record in prescriptions:
            timeline.append(
                {
                    "event_type": "prescription",
                    "occurred_at": record.created_at,
                    "payload": {
                        "id": record.prescription_id,
                        "patient_id": record.patient_id,
                        "type": record.type,
                        "description": record.description,
                        "frequency": record.frequency,
                        "start_date": record.start_date,
                        "end_date": record.end_date,
                        "calendar_path": record.calendar_path,
                        "created_at": record.created_at,
                    },
                }
            )

        clinical_notes = (
            session.query(ClinicalNoteRecord)
            .filter(_patient_id_matches(ClinicalNoteRecord.patient_id, resolved_patient_id))
            .all()
        )
        for record in clinical_notes:
            timeline.append(
                {
                    "event_type": "clinical_note",
                    "occurred_at": record.created_at,
                    "payload": {
                        "id": record.id,
                        "patient_id": record.patient_id,
                        "note": record.note,
                        "created_at": record.created_at,
                    },
                }
            )

        lab_reports = (
            session.query(LabReportRecord)
            .filter(_patient_id_matches(LabReportRecord.patient_id, resolved_patient_id))
            .all()
        )
        for record in lab_reports:
            occurred_at = _coerce_timeline_timestamp(record.report_date)
            timeline.append(
                {
                    "event_type": "lab_report",
                    "occurred_at": occurred_at,
                    "payload": {
                        "id": record.id,
                        "patient_id": record.patient_id,
                        "name": record.name,
                        "type": record.type,
                        "report_date": record.report_date,
                        "result_value": record.result_value,
                        "unit": record.unit,
                        "normal_range": record.normal_range,
                        "status": record.status,
                    },
                }
            )

        timeline.sort(key=lambda item: (item["occurred_at"], item["event_type"]))
        return timeline


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
        resolved_patient_id = _resolve_patient_user_id(session, patient_id)
        records = (
            session.query(ConversationMessageRecord)
            .filter(_patient_id_matches(ConversationMessageRecord.patient_id, resolved_patient_id))
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
        resolved_patient_id = _resolve_patient_user_id(session, patient_id)
        records = (
            session.query(ConversationMessageRecord)
            .filter(_patient_id_matches(ConversationMessageRecord.patient_id, resolved_patient_id))
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
                patient_id=_resolve_patient_user_id(session, patient_id),
                role=role,
                content=message,
            )
        )


def get_conversation_summary(patient_id: Any) -> str:
    with session_scope() as session:
        resolved_patient_id = _resolve_patient_user_id(session, patient_id)
        record = session.query(ConversationSummaryRecord).filter(_patient_id_matches(ConversationSummaryRecord.patient_id, resolved_patient_id)).one_or_none()
        if record is None:
            return ""
        return record.summary or ""


def set_conversation_summary(patient_id: Any, summary: str) -> str:
    cleaned_summary = (summary or "").strip()

    with session_scope() as session:
        resolved_patient_id = _resolve_patient_user_id(session, patient_id)
        record = session.query(ConversationSummaryRecord).filter(_patient_id_matches(ConversationSummaryRecord.patient_id, resolved_patient_id)).one_or_none()
        if record is None:
            record = ConversationSummaryRecord(patient_id=resolved_patient_id, summary=cleaned_summary)
            session.add(record)
        else:
            record.summary = cleaned_summary
            record.updated_at = datetime.now(timezone.utc)
        return cleaned_summary


def get_recent_conversation_messages(patient_id: Any, *, limit: int = 8) -> list[dict]:
    with session_scope() as session:
        resolved_patient_id = _resolve_patient_user_id(session, patient_id)
        records = (
            session.query(ConversationMessageRecord)
            .filter(_patient_id_matches(ConversationMessageRecord.patient_id, resolved_patient_id))
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
        resolved_patient_id = _resolve_patient_user_id(session, patient_id)
        return (
            session.query(ConversationMessageRecord)
            .filter(_patient_id_matches(ConversationMessageRecord.patient_id, resolved_patient_id))
            .count()
        )


def prune_conversation_messages(patient_id: Any, *, keep_last: int = 8) -> None:
    with session_scope() as session:
        normalized_patient_id = _resolve_patient_user_id(session, patient_id)
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
    with session_scope() as session:
        patient_id = _resolve_patient_user_id(session, prescription.patient_id)
        _get_or_create_patient(session, patient_id)
        record = session.query(PrescriptionRecord).filter(_patient_id_matches(PrescriptionRecord.patient_id, patient_id)).one_or_none()
        if record is None:
            record = PrescriptionRecord(patient_id=patient_id)
            session.add(record)
        record.type = prescription.type
        record.description = prescription.description
        record.frequency = prescription.frequency
        record.start_date = prescription.start_date
        record.end_date = prescription.end_date
        record.calendar_path = prescription.calendar_path
        session.flush()
        return {
            "id": record.prescription_id,
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
    with session_scope() as session:
        patient_id = _resolve_patient_user_id(session, prescription.patient_id)
        record = session.query(PrescriptionRecord).filter(_patient_id_matches(PrescriptionRecord.patient_id, patient_id)).one_or_none()
        if record is None:
            return None
        _get_or_create_patient(session, patient_id)
        record.type = prescription.type
        record.description = prescription.description
        record.frequency = prescription.frequency
        record.start_date = prescription.start_date
        record.end_date = prescription.end_date
        record.calendar_path = prescription.calendar_path
        return {
            "id": record.prescription_id,
            "patient_id": record.patient_id,
            "type": record.type,
            "description": record.description,
            "frequency": record.frequency,
            "start_date": record.start_date,
            "end_date": record.end_date,
            "calendar_path": record.calendar_path,
            "created_at": record.created_at,
        }


def delete_prescription(patient_id: int) -> bool:
    with session_scope() as session:
        resolved_patient_id = _resolve_patient_user_id(session, patient_id)
        record = session.query(PrescriptionRecord).filter(_patient_id_matches(PrescriptionRecord.patient_id, resolved_patient_id)).one_or_none()
        if record is None:
            return False
        session.delete(record)
        return True


def get_prescription(patient_id: int) -> dict:
    with session_scope() as session:
        resolved_patient_id = _resolve_patient_user_id(session, patient_id)
        record = session.query(PrescriptionRecord).filter(_patient_id_matches(PrescriptionRecord.patient_id, resolved_patient_id)).one_or_none()
        if record is None:
            return {}
        return {
            "id": record.prescription_id,
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
    with session_scope() as session:
        patient_id = _resolve_patient_user_id(session, clinical_note.patient_id)
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
    with session_scope() as session:
        patient_id = _resolve_patient_user_id(session, clinical_note.patient_id)
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
        resolved_patient_id = _resolve_patient_user_id(session, patient_id)
        record = session.query(ClinicalNoteRecord).filter(_patient_id_matches(ClinicalNoteRecord.patient_id, resolved_patient_id)).one_or_none()
        if record is None:
            return False
        session.delete(record)
        return True


def get_clinical_note(patient_id: int) -> dict:
    with session_scope() as session:
        resolved_patient_id = _resolve_patient_user_id(session, patient_id)
        record = session.query(ClinicalNoteRecord).filter(_patient_id_matches(ClinicalNoteRecord.patient_id, resolved_patient_id)).one_or_none()
        if record is None:
            return {}
        return {
            "id": record.id,
            "patient_id": record.patient_id,
            "note": record.note,
            "created_at": record.created_at,
        }


def upsert_lab_report(lab_report: LabReportModel) -> dict:
    with session_scope() as session:
        patient_id = _resolve_patient_user_id(session, lab_report.patient_id)
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
    with session_scope() as session:
        patient_id = _resolve_patient_user_id(session, lab_report.patient_id)
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
        resolved_patient_id = _resolve_patient_user_id(session, patient_id)
        record = (
            session.query(LabReportRecord)
            .filter(_patient_id_matches(LabReportRecord.patient_id, resolved_patient_id), LabReportRecord.report_date == report_date)
            .one_or_none()
        )
        if record is None:
            return False
        session.delete(record)
        return True


def get_lab_report(patient_id: int, report_date: str) -> dict:
    with session_scope() as session:
        resolved_patient_id = _resolve_patient_user_id(session, patient_id)
        record = (
            session.query(LabReportRecord)
            .filter(_patient_id_matches(LabReportRecord.patient_id, resolved_patient_id), LabReportRecord.report_date == report_date)
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


def upsert_vitals(vitals: VitalsModel) -> dict:
    with session_scope() as session:
        patient_id = _resolve_patient_user_id(session, vitals.patient_id)
        _get_or_create_patient(session, patient_id)
        recorded_at = _normalize_datetime_string(vitals.recorded_at)
        record = (
            session.query(VitalsRecord)
            .filter(_patient_id_matches(VitalsRecord.patient_id, patient_id), VitalsRecord.recorded_at == recorded_at)
            .one_or_none()
        )
        if record is None:
            record = VitalsRecord(patient_id=patient_id, recorded_at=recorded_at)
            session.add(record)
        if vitals.id is not None:
            record.id = vitals.id
        record.systolic_bp = vitals.systolic_bp
        record.diastolic_bp = vitals.diastolic_bp
        record.heart_rate = vitals.heart_rate
        record.respiratory_rate = vitals.respiratory_rate
        record.temperature_c = vitals.temperature_c
        record.spo2 = vitals.spo2
        record.weight_kg = vitals.weight_kg
        record.height_cm = vitals.height_cm
        record.notes = vitals.notes
        session.flush()
        return {
            "id": record.id,
            "patient_id": record.patient_id,
            "recorded_at": record.recorded_at,
            "systolic_bp": record.systolic_bp,
            "diastolic_bp": record.diastolic_bp,
            "heart_rate": record.heart_rate,
            "respiratory_rate": record.respiratory_rate,
            "temperature_c": record.temperature_c,
            "spo2": record.spo2,
            "weight_kg": record.weight_kg,
            "height_cm": record.height_cm,
            "notes": record.notes,
        }


def update_vitals(vitals: VitalsModel) -> Optional[dict]:
    with session_scope() as session:
        patient_id = _resolve_patient_user_id(session, vitals.patient_id)
        recorded_at = _normalize_datetime_string(vitals.recorded_at)
        record = (
            session.query(VitalsRecord)
            .filter(_patient_id_matches(VitalsRecord.patient_id, patient_id), VitalsRecord.recorded_at == recorded_at)
            .one_or_none()
        )
        if record is None:
            return None
        _get_or_create_patient(session, patient_id)
        if vitals.id is not None:
            record.id = vitals.id
        record.systolic_bp = vitals.systolic_bp
        record.diastolic_bp = vitals.diastolic_bp
        record.heart_rate = vitals.heart_rate
        record.respiratory_rate = vitals.respiratory_rate
        record.temperature_c = vitals.temperature_c
        record.spo2 = vitals.spo2
        record.weight_kg = vitals.weight_kg
        record.height_cm = vitals.height_cm
        record.notes = vitals.notes
        return vitals.model_dump()


def delete_vitals(patient_id: int, recorded_at: str) -> bool:
    with session_scope() as session:
        resolved_patient_id = _resolve_patient_user_id(session, patient_id)
        normalized_recorded_at = _normalize_datetime_string(recorded_at)
        record = (
            session.query(VitalsRecord)
            .filter(_patient_id_matches(VitalsRecord.patient_id, resolved_patient_id), VitalsRecord.recorded_at == normalized_recorded_at)
            .one_or_none()
        )
        if record is None:
            return False
        session.delete(record)
        return True


def get_vitals(patient_id: int, recorded_at: str) -> dict:
    with session_scope() as session:
        resolved_patient_id = _resolve_patient_user_id(session, patient_id)
        normalized_recorded_at = _normalize_datetime_string(recorded_at)
        record = (
            session.query(VitalsRecord)
            .filter(_patient_id_matches(VitalsRecord.patient_id, resolved_patient_id), VitalsRecord.recorded_at == normalized_recorded_at)
            .one_or_none()
        )
        if record is None:
            return {}
        return {
            "id": record.id,
            "patient_id": record.patient_id,
            "recorded_at": record.recorded_at,
            "systolic_bp": record.systolic_bp,
            "diastolic_bp": record.diastolic_bp,
            "heart_rate": record.heart_rate,
            "respiratory_rate": record.respiratory_rate,
            "temperature_c": record.temperature_c,
            "spo2": record.spo2,
            "weight_kg": record.weight_kg,
            "height_cm": record.height_cm,
            "notes": record.notes,
        }


def get_vitals_history(patient_id: int) -> list[dict]:
    with session_scope() as session:
        resolved_patient_id = _resolve_patient_user_id(session, patient_id)
        records = (
            session.query(VitalsRecord)
            .filter(_patient_id_matches(VitalsRecord.patient_id, resolved_patient_id))
            .order_by(VitalsRecord.recorded_at.desc(), VitalsRecord.id.desc())
            .all()
        )
        return [
            {
                "id": record.id,
                "patient_id": record.patient_id,
                "recorded_at": record.recorded_at,
                "systolic_bp": record.systolic_bp,
                "diastolic_bp": record.diastolic_bp,
                "heart_rate": record.heart_rate,
                "respiratory_rate": record.respiratory_rate,
                "temperature_c": record.temperature_c,
                "spo2": record.spo2,
                "weight_kg": record.weight_kg,
                "height_cm": record.height_cm,
                "notes": record.notes,
            }
            for record in records
        ]