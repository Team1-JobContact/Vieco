from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from src.models.catalog import Industry, Province, Skill

MODELS = {"industries": Industry, "provinces": Province, "skills": Skill}

def get_categories(db):
    def options(model):
        rows = db.query(model).filter(model.is_active.is_(True)).order_by(model.name, model.id)
        return [dict(id=row.id, name=row.name) for row in rows]
    return {name: options(model) for name, model in MODELS.items()}

def create_category(db, data):
    if data.industry_id is not None and not db.query(Industry.id).filter(
            Industry.id == data.industry_id, Industry.is_active.is_(True)).first():
        raise HTTPException(422, "Ngành nghề không tồn tại")
    values = {"name": data.name}
    if data.type == "provinces":
        values["code"] = data.code
    if data.type == "skills":
        values["industry_id"] = data.industry_id
    if data.type == "industries":
        from src.services.company_service import slugify
        slug = slugify(data.name)
        candidate, suffix = slug, 2
        while db.query(Industry.id).filter(Industry.slug == candidate).first():
            candidate, suffix = f"{slug}-{suffix}", suffix+1
        values["slug"] = candidate
    row = MODELS[data.type](**values)
    db.add(row)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Danh mục hoặc mã đã tồn tại")
    return {"id": row.id, "type": data.type, **values}
