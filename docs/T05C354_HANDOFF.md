# Bàn giao T05C354 — Hoàn thiện và demo

- Phụ trách: Nguyễn Thiên Bảo — N25DTCN078, thành viên C.
- Hạn: 24/11/2026. Rà soát: 23/11/2026.
- Phối hợp: A, B, D. Phụ thuộc: PB-025, PB-026.
- Mã nguồn đầu vào: origin/main, commit b40aba4406fa0b33a6b9f1ca81a00fec5842a935. Tích hợp tài liệu vào main mới nhất; giữ nguyên hosting, CV builder và AI.
- Trạng thái: hoàn thành rà soát tự động và tài liệu; chờ nghiệm thu môi trường demo và kết quả phụ thuộc. Chưa đề nghị đánh dấu toàn bộ task Done.

## Kết quả kiểm tra thực tế

| Phạm vi | Kết quả ngày 23/11 | Giới hạn |
| --- | --- | --- |
| Local ae3b406, backend (lần trước) | 72 passed, 2 warnings | FastAPI TestClient, SQLite cô lập |
| Main b40aba4, backend | Chưa xác minh thành công trong môi trường bàn giao, xem log | Xem log đính kèm |
| Local ae3b406, frontend (lần trước) | 22 passed | Node.js/jsdom |
| Main b40aba4, frontend | 37 passed | Node.js/jsdom, xem log |
| Blocker/critical | Chưa ghi nhận lỗi nghiệp vụ mới được xác nhận | Không kết luận main không có lỗi nếu chưa nghiệm thu đầy đủ |
| MySQL/migration thật | Chưa xác minh trong lượt này | Không chạy migration/seed vào DB đang cấu hình |
| SMTP, browser, file storage khi triển khai | Chưa nghiệm thu | Cần môi trường test của nhóm |

Lệnh tái hiện tại source_code/server:

```powershell
..\..\.venv\Scripts\python.exe -m pytest tests -q -p no:cacheprovider
```

Lệnh tại source_code/client (dependency đã có trong lượt kiểm tra này):

```powershell
npm test
```

Hai cảnh báo backend liên quan Starlette TestClient/httpx và tên hằng HTTP 422 deprecated. Frontend có cảnh báo cấu hình môi trường npm http-proxy. Các cảnh báo không làm test thất bại; chưa nâng dependency trong task này.

## Thay đổi và lý do

1. README: bỏ trạng thái nhánh cũ khỏi hướng dẫn hiện tại; ghi lệnh Windows bằng Python của .venv, cấu hình DB, migration/seed và Admin; giải thích localhost, database nhóm và giới hạn lưu file.
2. Checklist: thay nội dung lịch sử “chưa có source code” bằng checklist nghiệm thu hiện tại, có phân biệt test tự động và thủ công.
3. Hướng dẫn demo: bổ sung điều kiện chuẩn bị, kịch bản rút gọn, tiêu chí chấp nhận và cách lưu bằng chứng.
4. Báo cáo này: tổng kết phạm vi, kết quả thực tế, mục còn mở và nội dung PR.

Không thay đổi logic nghiệp vụ vì chưa tìm được lỗi tái hiện trong phạm vi đã chạy. Không thay đổi .env, mật khẩu hoặc dữ liệu nhóm.

## Tổng kết phạm vi backlog

Đây là đối chiếu mã nguồn/test, không phải cập nhật trạng thái chính thức trên board.

| Nhóm chức năng | Bằng chứng trong repository | Kết luận |
| --- | --- | --- |
| Tài khoản, phân quyền, hồ sơ/CV | test_auth.py, test_candidate.py | Có kiểm thử tự động, đã pass |
| Công ty, duyệt, tin tuyển dụng | test_company.py, test_job.py, test_employer_integration.py | Có kiểm thử tự động, đã pass |
| Tìm kiếm, ứng tuyển, lịch sử, lưu việc | test_workflows.py | Có kiểm thử tự động, đã pass |
| Thông báo, quyền tải CV, ảnh công ty | test_workflows.py | Có kiểm thử tự động, đã pass |
| UI trang chủ/tìm kiếm/form tuyển dụng/đặt lại mật khẩu | client/tests/*.test.cjs | Phạm vi jsdom đã pass |
| API liên hệ, theo dõi/đánh giá công ty, lịch hẹn | Giới hạn trong HUONG_DAN_DEMO.md | Chờ nhóm quyết định phạm vi/hoãn; chưa xác nhận backlog chính thức |
| E2E đã có | T05C352_E2E_REPORT.md, ngày 19/11 | Đã đọc; chưa xác nhận mapping PB-025/PB-026 |
| PB-025, PB-026 | Chưa có trạng thái chính thức trên board | Chờ nhóm xác nhận, không tự đánh dấu Done |

## Việc cần nhóm xác nhận trước khi đóng

| Việc | Người phối hợp đề xuất | Bằng chứng cần có |
| --- | --- | --- |
| Kết quả PB-025/PB-026 và danh sách lỗi còn mở | A/B/D theo phân công thực tế | Link task/báo cáo/test |
| MySQL, migration và SMTP test | Người phụ trách backend/DB cùng Bảo | Môi trường, kết quả, ngày kiểm tra |
| Demo ba vai trò, desktop và mobile | Bảo cùng cả nhóm | Ảnh/video và checklist |
| Chốt phần ngoài MVP | Trưởng nhóm và cả nhóm | Quyết định, task tiếp theo, người nhận |
| Review và nộp | Reviewer của nhóm | Link PR có mã T05C354 |

## Nội dung PR đề xuất

Tiêu đề: T05C354: cập nhật hướng dẫn chạy, demo và báo cáo nghiệm thu

README và checklist còn mô tả trạng thái lịch sử, gây khó khăn khi chạy dự án và đánh giá khả năng demo. Cập nhật hướng dẫn Windows/database, bổ sung kịch bản demo và tổng kết kiểm thử hiện tại.

Validation trên main b40aba4: backend Chưa xác minh thành công trong môi trường bàn giao, xem log; frontend 37 passed. Số liệu 72/22 thuộc bản local trước đó. MySQL, SMTP, browser thật và kết quả PB-025/PB-026 còn chờ nhóm xác nhận.

## Mẫu ghi lỗi phát hiện khi demo

| ID | Mức độ | Bước tái hiện | Mong đợi/thực tế | Người xử lý | Commit sửa | Kiểm tra lại |
| --- | --- | --- | --- | --- | --- | --- |
| Chưa ghi nhận lỗi tái hiện mới | — | — | — | — | — | — |

Không ghi token, mật khẩu, .env hoặc CV thật vào minh chứng.

## Log trên main mới nhất

- [Backend log](evidence/T05C354-backend-test.txt)
- [Frontend log](evidence/T05C354-frontend-test.txt)

Test đặt SECRET_KEY riêng cho kiểm thử và DATABASE_URL=sqlite://, không dùng DB nhóm. Frontend tái sử dụng jsdom qua NODE_PATH. Dependency thiếu được thử tải vào thư mục tạm; nếu test chưa chạy thành công thì vẫn ghi chưa xác minh, không coi là pass. Không nghiệm thu AI/hosting thật trong lượt này.
