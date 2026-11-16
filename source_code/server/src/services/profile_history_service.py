from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError

from src.models.catalog import Skill
from src.models.profile import CandidateSkill, Education, WorkExperience
from src.services import candidate_service

MODELS = {"educations": Education, "experiences": WorkExperience, "skills": CandidateSkill}
FIELDS = {
    "educations": ("school_name", "major", "degree", "start_date", "end_date", "description"),
    "experiences": ("company_name", "position", "start_date", "end_date", "description"),
    "skills": ("skill_id", "level"),
}


def fields(db, kind, row):
    data = {key: getattr(row, key) for key in ("id", *FIELDS[kind])}
    if kind == "skills":
        skill = db.get(Skill, row.skill_id)
        data["name"] = skill.name if skill else ""
    return data


def profile_history(db, profile):
    if profile is None:
        return {kind: [] for kind in MODELS}
    return {kind: [fields(db, kind, row) for row in db.query(model).filter(
        model.candidate_profile_id == profile.id).order_by(model.id.desc())] for kind, model in MODELS.items()}


def save_entry(db, user, kind, data, entry_id=None):
    profile = candidate_service.get_or_create_profile(db, user)
    model = MODELS[kind]
    row = None
    if entry_id is not None:
        row = db.query(model).filter(model.id == entry_id, model.candidate_profile_id == profile.id).first()
        if row is None:
            raise HTTPException(404, "Không tìm thấy mục trong hồ sơ của bạn")
    if kind == "skills":
        skill = db.get(Skill, data.skill_id)
        if skill is None or (not skill.is_active and (row is None or row.skill_id != data.skill_id)):
            raise HTTPException(422, "Kỹ năng không tồn tại hoặc đã bị ẩn")
    if row is None:
        row = model(candidate_profile_id=profile.id)
        db.add(row)
    for key, value in data.model_dump().items():
        setattr(row, key, value)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Kỹ năng đã có trong hồ sơ")
    return fields(db, kind, row)


def delete_entry(db, user, kind, entry_id):
    profile = candidate_service.get_profile_or_404(db, user)
    model = MODELS[kind]
    row = db.query(model).filter(model.id == entry_id, model.candidate_profile_id == profile.id).first()
    if row is None:
        raise HTTPException(404, "Không tìm thấy mục trong hồ sơ của bạn")
    db.delete(row)
    db.commit()
