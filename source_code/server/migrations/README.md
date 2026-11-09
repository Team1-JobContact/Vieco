# Migration & seed

Chạy trong thư mục `server/` (đã `pip install -r requirements.txt`):

```bash
# 1. Tạo CSDL rỗng một lần (MySQL 8.0.16+ để CHECK constraint có hiệu lực)
mysql -u root -p -e "CREATE DATABASE job_contact_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"

# 2. Tạo 27 bảng
alembic upgrade head

# 3. Nạp danh mục cơ bản (chạy lại an toàn)
python -m src.seeds.run

# Hoàn tác toàn bộ
alembic downgrade base
```

Sửa model xong: `alembic revision --autogenerate -m "mo ta"`, kiểm tra file sinh ra rồi `alembic upgrade head`.
