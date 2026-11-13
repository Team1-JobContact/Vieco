"""Read-only active catalog options used by the employer forms (PB-015)."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.config.database import get_db
from src.models.catalog import Industry, Province

router = APIRouter(prefix="/api/v1/categories", tags=["Catalog"])


@router.get("")
def get_categories(db: Session = Depends(get_db)):
    def options(model):
        rows = db.query(model.id, model.name).filter(model.is_active.is_(True))
        return [dict(id=row.id, name=row.name) for row in rows.order_by(model.name, model.id)]

    return {"industries": options(Industry), "provinces": options(Province)}
