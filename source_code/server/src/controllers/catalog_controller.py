from fastapi import Depends
from sqlalchemy.orm import Session
from src.config.database import get_db
from src.services import catalog_service

def get_categories(db: Session = Depends(get_db)):
    return catalog_service.get_categories(db)
