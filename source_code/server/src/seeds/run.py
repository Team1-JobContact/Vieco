"""Seed danh mục cơ bản. Chạy từ thư mục server/:  python -m src.seeds.run

- Idempotent: chạy nhiều lần không tạo trùng; bản ghi đã có KHÔNG bị ghi đè
  (Admin có thể đã đổi cấu hình, ẩn danh mục...).
- Tài khoản Admin chỉ được tạo khi đặt ADMIN_EMAIL và ADMIN_PASSWORD trong môi trường/.env.
"""
import os

from sqlalchemy import select

from src.config.database import SessionLocal
from src.models import Industry, Province, Role, Skill, StaticPage, SystemSetting, User
from src.seeds import data


def _missing(session, column, values):
    existing = set(session.scalars(select(column)))
    return [v for v in values if v not in existing]


def seed_roles(s):
    desc = dict(data.ROLES)
    new = _missing(s, Role.name, list(desc))
    s.add_all(Role(name=n, description=desc[n]) for n in new)
    return len(new)


def seed_industries(s):
    new = set(_missing(s, Industry.slug, [i[1] for i in data.INDUSTRIES]))
    s.add_all(Industry(name=n, slug=sl) for n, sl in data.INDUSTRIES if sl in new)
    return len(new)


def seed_provinces(s):
    new = set(_missing(s, Province.code, [p[1] for p in data.PROVINCES]))
    s.add_all(Province(name=n, code=c) for n, c in data.PROVINCES if c in new)
    return len(new)


def seed_skills(s):
    industry_ids = {slug: i for slug, i in s.execute(select(Industry.slug, Industry.id))}
    new = set(_missing(s, Skill.name, [k[0] for k in data.SKILLS]))
    s.add_all(Skill(name=n, industry_id=industry_ids.get(sl)) for n, sl in data.SKILLS if n in new)
    return len(new)


def seed_settings(s):
    new = set(_missing(s, SystemSetting.setting_key, [x[0] for x in data.SYSTEM_SETTINGS]))
    s.add_all(SystemSetting(setting_key=k, setting_value=v, description=d)
              for k, v, d in data.SYSTEM_SETTINGS if k in new)
    return len(new)


def seed_pages(s):
    new = set(_missing(s, StaticPage.slug, [p[0] for p in data.STATIC_PAGES]))
    s.add_all(StaticPage(slug=sl, title=t, content=c) for sl, t, c in data.STATIC_PAGES if sl in new)
    return len(new)


def seed_admin(s):
    email, password = os.getenv("ADMIN_EMAIL"), os.getenv("ADMIN_PASSWORD")
    if not email or not password:
        return "bỏ qua (chưa đặt ADMIN_EMAIL/ADMIN_PASSWORD)"
    if s.scalar(select(User.id).where(User.email == email)):
        return "đã tồn tại"
    from passlib.context import CryptContext  # import muộn: chỉ cần khi tạo Admin

    role_id = s.scalar(select(Role.id).where(Role.name == "ADMIN"))
    s.add(User(
        email=email,
        password_hash=CryptContext(schemes=["bcrypt"]).hash(password),
        role_id=role_id,
        full_name=os.getenv("ADMIN_FULL_NAME", "Quản trị viên"),
        is_email_verified=True,
    ))
    return "đã tạo"


def main():
    steps = [("roles", seed_roles), ("industries", seed_industries), ("provinces", seed_provinces),
             ("skills", seed_skills), ("system_settings", seed_settings),
             ("static_pages", seed_pages), ("admin", seed_admin)]
    result = {}
    with SessionLocal() as s:
        for label, fn in steps:
            result[label] = fn(s)
            s.flush()  # cần để bước sau (skills, admin) thấy dữ liệu bước trước
        s.commit()
    for k, v in result.items():
        print(f"{k:16} +{v}" if isinstance(v, int) else f"{k:16} {v}")


if __name__ == "__main__":
    main()
