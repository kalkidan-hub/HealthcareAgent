from contextlib import contextmanager
import json
from typing import Any, Iterator, Optional

from sqlalchemy import JSON, Column, Date, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Session

from backend.infrastructure import database as db
from backend.models.patient import ClinicalNote as ClinicalNoteModel
from backend.models.patient import LabReport as LabReportModel
from backend.models.patient import Prescription as PrescriptionModel


class PatientRecord(db.Base):
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, default="")
    age = Column(Integer, nullable=False, default=0)
    email = Column(String(255), nullable=False, default="")
    risk_factors = Column(JSON, nullable=False, default=list)


class PrescriptionRecord(db.Base):
    __tablename__ = "prescriptions"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), unique=True, index=True, nullable=False)
    type = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    frequency = Column(String(50), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)
    calendar_path = Column(String(255), nullable=False)


class ClinicalNoteRecord(db.Base):
    __tablename__ = "clinical_notes"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), unique=True, index=True, nullable=False)
    note = Column(Text, nullable=False)


class LabReportRecord(db.Base):
    __tablename__ = "lab_reports"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), index=True, nullable=False)
    name = Column(String(255), nullable=False)
    type = Column(String(255), nullable=False)
    report_date = Column(String(50), nullable=False)
    result_value = Column(Float, nullable=False)
    unit = Column(String(50), nullable=False)
    normal_range = Column(String(255), nullable=False)
    status = Column(String(50), nullable=False)


def _normalize_patient_id(patient_id: Any) -> int:
    return int(patient_id)


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


def _get_or_create_patient(session: Session, patient_id: int) -> PatientRecord:
    patient = session.get(PatientRecord, patient_id)
    if patient is None:
        patient = PatientRecord(id=patient_id, name="", age=0, email="", risk_factors=[])
        session.add(patient)
        session.flush()
    return patient


def _patient_to_dict(patient: Optional[PatientRecord]) -> Optional[dict]:
    if patient is None:
        return None
    return {
        "id": patient.id,
        "name": patient.name,
        "age": patient.age,
        "email": patient.email,
        "risk_factors": list(patient.risk_factors or []),
    }


def get_patient_record(patient_id: int) -> Optional[dict]:
    with session_scope() as session:
        patient = session.get(PatientRecord, _normalize_patient_id(patient_id))
        print(patient)
        return _patient_to_dict(patient)


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


def upsert_prescription(prescription: PrescriptionModel) -> dict:
    with session_scope() as session:
        _get_or_create_patient(session, prescription.patient_id)
        record = session.query(PrescriptionRecord).filter_by(patient_id=prescription.patient_id).one_or_none()
        if record is None:
            record = PrescriptionRecord(patient_id=prescription.patient_id)
            session.add(record)
        record.id = prescription.id
        record.type = prescription.type
        record.description = prescription.description
        record.frequency = prescription.frequency
        record.start_date = prescription.start_date
        record.end_date = prescription.end_date
        record.calendar_path = prescription.calendar_path
        return prescription.model_dump()


def update_prescription(prescription: PrescriptionModel) -> Optional[dict]:
    with session_scope() as session:
        record = session.query(PrescriptionRecord).filter_by(patient_id=prescription.patient_id).one_or_none()
        if record is None:
            return None
        _get_or_create_patient(session, prescription.patient_id)
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
        record = session.query(PrescriptionRecord).filter_by(patient_id=_normalize_patient_id(patient_id)).one_or_none()
        if record is None:
            return False
        session.delete(record)
        return True


def get_prescription(patient_id: int) -> dict:
    with session_scope() as session:
        record = session.query(PrescriptionRecord).filter_by(patient_id=_normalize_patient_id(patient_id)).one_or_none()
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
        }


def upsert_clinical_note(clinical_note: ClinicalNoteModel) -> dict:
    with session_scope() as session:
        _get_or_create_patient(session, clinical_note.patient_id)
        record = session.query(ClinicalNoteRecord).filter_by(patient_id=clinical_note.patient_id).one_or_none()
        if record is None:
            record = ClinicalNoteRecord(patient_id=clinical_note.patient_id)
            session.add(record)
        record.id = clinical_note.id
        record.note = clinical_note.note
        return clinical_note.model_dump()


def update_clinical_note(clinical_note: ClinicalNoteModel) -> Optional[dict]:
    with session_scope() as session:
        record = session.query(ClinicalNoteRecord).filter_by(patient_id=clinical_note.patient_id).one_or_none()
        if record is None:
            return None
        _get_or_create_patient(session, clinical_note.patient_id)
        record.id = clinical_note.id
        record.note = clinical_note.note
        return clinical_note.model_dump()


def delete_clinical_note(patient_id: int) -> bool:
    with session_scope() as session:
        record = session.query(ClinicalNoteRecord).filter_by(patient_id=_normalize_patient_id(patient_id)).one_or_none()
        if record is None:
            return False
        session.delete(record)
        return True


def get_clinical_note(patient_id: int) -> dict:
    with session_scope() as session:
        record = session.query(ClinicalNoteRecord).filter_by(patient_id=_normalize_patient_id(patient_id)).one_or_none()
        if record is None:
            return {}
        return {
            "id": record.id,
            "patient_id": record.patient_id,
            "note": record.note,
        }


def upsert_lab_report(lab_report: LabReportModel) -> dict:
    with session_scope() as session:
        _get_or_create_patient(session, lab_report.patient_id)
        record = (
            session.query(LabReportRecord)
            .filter_by(patient_id=lab_report.patient_id, report_date=lab_report.report_date)
            .one_or_none()
        )
        if record is None:
            record = LabReportRecord(patient_id=lab_report.patient_id, report_date=lab_report.report_date)
            session.add(record)
        record.id = lab_report.id
        record.name = lab_report.name
        record.type = lab_report.type
        record.result_value = lab_report.result_value
        record.unit = lab_report.unit
        record.normal_range = lab_report.normal_range
        record.status = lab_report.status
        return lab_report.model_dump()


def update_lab_report(lab_report: LabReportModel) -> Optional[dict]:
    with session_scope() as session:
        record = (
            session.query(LabReportRecord)
            .filter_by(patient_id=lab_report.patient_id, report_date=lab_report.report_date)
            .one_or_none()
        )
        if record is None:
            return None
        _get_or_create_patient(session, lab_report.patient_id)
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
            .filter_by(patient_id=_normalize_patient_id(patient_id), report_date=report_date)
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
            .filter_by(patient_id=_normalize_patient_id(patient_id), report_date=report_date)
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