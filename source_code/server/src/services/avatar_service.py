from src.models.user import User
from src.services import company_media_service


def set_avatar(db, user, file=None):
    """Avatars share the existing validated public-image storage and media route."""
    account = db.query(User).filter(User.id == user.id).populate_existing().with_for_update().one()
    url = company_media_service._store(file, company_media_service.logo_max_mb(db)) if file is not None else None
    old = account.avatar_url
    account.avatar_url = url
    try:
        db.commit()
    except BaseException:
        db.rollback()
        company_media_service._remove(url)
        raise
    company_media_service._remove(old)
    return {"avatar_url": url}
