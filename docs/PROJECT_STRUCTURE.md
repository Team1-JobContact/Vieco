# Cấu trúc dự án Vieco

## Nguyên tắc

Giữ source_code/client và source_code/server để bảo toàn URL trang, cách chạy và đường dẫn test tích hợp. Backend tiếp tục phân lớp routes → services → models, dùng schemas để kiểm tra/biểu diễn dữ liệu. Frontend gom JavaScript theo chức năng. Không thêm framework, dependency, API hoặc thay schema trong đợt tổ chức này.

## Trước khi tổ chức

```text
Vieco/
├── package-lock.json                  # Lockfile rỗng tại gốc, không có package.json
├── docs/
└── source_code/
    ├── New Text Document.txt
    ├── client/
    │   ├── index.html
    │   ├── pages/
    │   ├── assets/js/                 # auth-api, auth-ui, employer-api, employer-ui, main
    │   └── tests/
    └── server/
        ├── run.py
        ├── server.js                  # File khung
        ├── prisma/.gitkeep
        ├── migrations/
        ├── uploads/
        ├── tests/
        └── src/
            ├── app.py
            ├── app.js                 # File khung
            ├── controllers/.gitkeep
            ├── middlewares/auth.py
            ├── config/
            ├── models/
            ├── routes/
            ├── schemas/
            ├── services/
            ├── seeds/
            └── utils/
```

## Sau khi tổ chức

Cây dưới lược bỏ dependency/cache và các placeholder còn giữ nguyên.

```text
Vieco/
├── README.md
├── .github/
├── archive/
│   ├── README.md
│   ├── package-lock.json
│   └── source_code/                   # Các file khung và file rỗng theo bảng dưới
├── docs/
│   ├── SETUP.md
│   ├── PROJECT_STRUCTURE.md
│   ├── HUONG_DAN_CHAY_DU_AN.md
│   ├── PB-015.md
│   ├── TEST_CHECKLIST.md
│   ├── CONTRIBUTING.md
│   ├── WEEK1_REVIEW.md
│   ├── design/
│   ├── erd/
│   ├── meeting-notes/
│   └── srs/
└── source_code/
    ├── README.md
    ├── client/
    │   ├── index.html
    │   ├── package.json
    │   ├── package-lock.json
    │   ├── pages/                     # login.html, register.html, employer.html
    │   ├── assets/
    │   │   ├── css/
    │   │   ├── images/
    │   │   └── js/
    │   │       ├── auth/              # auth-api.js, auth-ui.js
    │   │       ├── employer/          # employer-api.js, employer-ui.js
    │   │       └── home/              # home-ui.js
    │   └── tests/
    └── server/
        ├── run.py
        ├── requirements.txt
        ├── alembic.ini
        ├── .env.example
        ├── migrations/
        ├── uploads/
        ├── tests/
        └── src/
            ├── app.py
            ├── config/
            ├── dependencies/          # __init__.py, auth.py
            ├── models/
            ├── routes/
            ├── schemas/
            ├── services/
            ├── seeds/
            └── utils/
```

## Trách nhiệm

| Thư mục | Trách nhiệm |
| --- | --- |
| client/pages | Trang HTML; giữ tên trang và điều hướng hiện có |
| client/assets/js/auth | HTTP auth, validation, phiên đăng nhập và UI auth; giữ nội dung file hiện có |
| client/assets/js/employer | API client và UI biểu mẫu công ty/tin tuyển dụng |
| client/assets/js/home | Tương tác trang chủ |
| client/assets/css, images | Giao diện và tài nguyên; không thay CSS/cascade |
| client/tests | Test Node/jsdom và trình sinh request cho test tích hợp |
| server/src/config | Settings, engine/session và SQLAlchemy Base |
| server/src/dependencies | FastAPI dependency xác thực, lấy user và phân quyền |
| server/src/routes | Khai báo HTTP endpoint và dependency |
| server/src/schemas | Request/response và validation Pydantic |
| server/src/services | Nghiệp vụ auth, hồ sơ/CV, công ty và tin tuyển dụng |
| server/src/models | Model SQLAlchemy; __init__.py đăng ký model cho metadata |
| server/src/utils | Tiện ích bảo mật hiện có |
| server/src/seeds | Dữ liệu/lệnh seed, chỉ chạy chủ động |
| server/migrations | Lịch sử Alembic, giữ nguyên revision và nội dung |
| server/uploads | Dữ liệu CV cục bộ; không đưa lên Git, không di chuyển dữ liệu |
| server/tests | Test API bằng SQLite và test tích hợp gọi Node |
| docs | Hướng dẫn, thiết kế, yêu cầu và báo cáo |
| archive | File khung/artefact giữ nguyên nội dung, không thuộc runtime |

## Bảng di chuyển

Đường dẫn tính từ gốc repository. Không xóa nội dung; SHA-256 đã được đối chiếu cho file di chuyển.

| Đường dẫn cũ | Đường dẫn mới | Lý do | Ảnh hưởng |
| --- | --- | --- | --- |
| source_code/client/assets/js/auth-api.js | source_code/client/assets/js/auth/auth-api.js | Gom auth | Trung bình |
| source_code/client/assets/js/auth-ui.js | source_code/client/assets/js/auth/auth-ui.js | Gom auth | Trung bình |
| source_code/client/assets/js/employer-api.js | source_code/client/assets/js/employer/employer-api.js | Gom employer | Trung bình |
| source_code/client/assets/js/employer-ui.js | source_code/client/assets/js/employer/employer-ui.js | Gom employer | Trung bình |
| source_code/client/assets/js/main.js | source_code/client/assets/js/home/home-ui.js | Tên thể hiện trang chủ | Trung bình |
| source_code/server/src/middlewares/auth.py | source_code/server/src/dependencies/auth.py | Đúng trách nhiệm FastAPI dependency | Trung bình |
| source_code/server/server.js | archive/source_code/server/server.js | File khung JavaScript | Thấp |
| source_code/server/src/app.js | archive/source_code/server/src/app.js | File khung Express | Thấp |
| source_code/server/prisma/.gitkeep | archive/source_code/server/prisma/.gitkeep | Placeholder Prisma | Thấp |
| source_code/server/src/controllers/.gitkeep | archive/source_code/server/src/controllers/.gitkeep | Placeholder controllers | Thấp |
| source_code/New Text Document.txt | archive/source_code/New Text Document.txt | File rỗng | Thấp |
| package-lock.json | archive/package-lock.json | Lockfile rỗng không có manifest ở gốc | Thấp |

## File chỉnh sửa và tham chiếu cập nhật

- Thêm server/src/dependencies/__init__.py. Cập nhật import src.middlewares.auth thành src.dependencies.auth trong routes/auth.py, candidate.py, company.py, job.py và tests/test_auth.py.
- Cập nhật script src trong client/index.html và pages/login.html, register.html, employer.html; giữ thứ tự auth API trước script phụ thuộc.
- Cập nhật require/đường dẫn đọc JS trong client/tests/employer-api.test.cjs, employer-ui.test.cjs, job-contract.cjs. Test Python vẫn gọi client/tests/job-contract.cjs tại vị trí cũ.
- Cập nhật README.md, source_code/README.md, docs/SETUP.md, docs/HUONG_DAN_CHAY_DU_AN.md và đường dẫn trong docs/PB-015.md. Thêm archive/README.md và tài liệu này; đánh dấu checklist tuần 1 là lịch sử.
- Giữ run.py, src.app:app, API /api/v1, URL HTML, query/hash, tên global JS, khóa storage, model/schema/service, migration, dependency manifest/lockfile client và cấu hình môi trường.
- Không thay quy tắc ignore: archive chỉ chứa file đã liệt kê; file bí mật/uploads không được đưa vào archive. Không di chuyển môi trường ảo, node_modules hay cache. Các .gitkeep còn lại được giữ nguyên.

## Kiểm chứng đã thực hiện

| Bước | Kết quả |
| --- | --- |
| Di chuyển artefact | Hash 6 file trùng trước/sau |
| Chuyển auth dependency | Hash auth.py trùng; 44 test backend pass cả trước/sau |
| Gom JS | Hash 5 file trùng; 19 test frontend pass cả trước/sau |
| Test tích hợp sau gom JS | 1 test pass, thực thi request do JS sinh với FastAPI/SQLite |
| Tham chiếu script HTML | 9 tham chiếu tồn tại; không còn đường dẫn JS cũ trong mã nguồn/tài liệu vận hành |
| Cú pháp JS | Cả 5 file pass node --check |
| Diff | git diff --check không báo lỗi khoảng trắng ở các bước mã nguồn |

Hai cảnh báo backend có sẵn: TestClient dùng httpx bị deprecated và hằng HTTP_422_UNPROCESSABLE_ENTITY bị deprecated. Không cài thư viện hoặc sửa cảnh báo trong phạm vi refactoring.

Frontend không có bước build. Chưa xác minh MySQL/migration thực tế, kết nối dữ liệu thật hoặc giao diện trực quan trên browser. Kết quả SQLite/jsdom không thay thế các kiểm tra này. Endpoint health trả thông báo cố định nên không chứng minh MySQL kết nối thành công.

## Hoàn tác và công việc còn lại

Hoàn tác theo từng nhóm: đưa file về đường dẫn cũ và đổi đồng thời các tham chiếu liên quan; đối chiếu Git diff, không ghi đè thay đổi mới hoặc dùng reset phá hủy dữ liệu. Chưa commit/push các bước này.

Rà soát cuối đã hoàn tất: đối chiếu cả 12 file di chuyển với Git blob ban đầu; diff mã nguồn chỉ đổi import/đường dẫn; kiểm tra 20 liên kết Markdown nội bộ trong 6 tài liệu và mã hóa tiếng Việt đều đạt. Không phát hiện file .env, dependency/cache hoặc dữ liệu uploads trong danh sách file mới không bị ignore. git diff --check đạt. Các đường dẫn cũ còn trong tài liệu này để ghi lịch sử di chuyển, không phải tham chiếu runtime. Kiểm tra browser/MySQL bằng môi trường phát triển vẫn là phần chưa xác minh. Báo cáo WEEK1_REVIEW và checklist tuần 1 được giữ như lịch sử, không coi là trạng thái vận hành hiện tại.