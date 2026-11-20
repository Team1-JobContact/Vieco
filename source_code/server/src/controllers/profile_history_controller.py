from typing import Literal

from fastapi import Depends, HTTPException, Response
from sqlalchemy.orm import Session

from src.config.database import get_db
from src.middlewares.auth import require_roles
from src.models.user import User
from src.schemas.profile_history import EducationInput, ExperienceInput, SkillInput
from src.services import candidate_service, profile_history_service

candidate = require_roles("CANDIDATE")
EntryType = Literal["educations", "experiences", "skills"]
EntryData = EducationInput | ExperienceInput | SkillInput
SCHEMAS = {"educations": EducationInput, "experiences": ExperienceInput, "skills": SkillInput}


def history(user: User = Depends(candidate), db: Session = Depends(get_db)):
    return profile_history_service.profile_history(db, candidate_service.find_profile(db, user))


def create_entry(kind: EntryType, data: EntryData, user: User = Depends(candidate), db: Session = Depends(get_db)):
    if not isinstance(data, SCHEMAS[kind]):
        raise HTTPException(422, "Thông tin không khớp loại mục hồ sơ")
    return profile_history_service.save_entry(db, user, kind, data)


def update_entry(kind: EntryType, entry_id: int, data: EntryData, user: User = Depends(candidate), db: Session = Depends(get_db)):
    if not isinstance(data, SCHEMAS[kind]):
        raise HTTPException(422, "Thông tin không khớp loại mục hồ sơ")
    return profile_history_service.save_entry(db, user, kind, data, entry_id)


def delete_entry(kind: EntryType, entry_id: int, user: User = Depends(candidate), db: Session = Depends(get_db)):
    profile_history_service.delete_entry(db, user, kind, entry_id)
    return Response(status_code=204)
