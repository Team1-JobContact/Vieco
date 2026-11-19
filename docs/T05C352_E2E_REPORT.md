# T05C352 — Báo cáo kiểm thử luồng tuyển dụng end-to-end

- Task: Kiểm thử end-to-end: đăng ký → hồ sơ → duyệt công ty → đăng tin → duyệt tin → ứng tuyển → xử lý đơn.
- Ngày chạy: 19/11/2026 (Asia/Saigon).
- Mã nguồn được kiểm tra: `01524ff2b862e3e4a40af67e0ac7fc2c3346589c`.
- Bài test: `source_code/server/tests/test_workflows.py::test_end_to_end_register_profile_company_job_apply_process`.
- Môi trường: Windows, Python 3.15.2, pytest 9.2.0, FastAPI TestClient, SQLite trong bộ nhớ và thư mục uploads tạm.
- Kết quả: **1 passed, 2 warnings in 1.83s**, exit code 0.

## Các bước được xác minh

| Bước | Kiểm tra và kết quả đạt |
| --- | --- |
| Đăng ký/đăng nhập | Tạo tài khoản nhà tuyển dụng và ứng viên; đăng nhập lấy token. Admin được chuẩn bị bằng fixture. |
| Hồ sơ/CV | Ứng viên tạo hồ sơ và tải CV PDF. |
| Công ty | Công ty mới ở PENDING; chưa được đăng tin hoặc xuất hiện công khai. Từ chối cần lý do, gửi lại PENDING rồi Admin duyệt APPROVED. |
| Đăng tin | Nhà tuyển dụng tạo tin DRAFT; bản nháp chưa truy cập công khai được. |
| Duyệt tin | Gửi duyệt PENDING; nhà tuyển dụng không có quyền duyệt; Admin duyệt APPROVED, tìm kiếm công khai trả đúng tin và số tin công ty. |
| Ứng tuyển | Nộp CV và thư giới thiệu thành công; nộp trùng trả 409; số lượt ứng tuyển là 1; nhà tuyển dụng tải được đúng nội dung CV. |
| Xử lý đơn | Chuyển VIEWED → INTERVIEW → ACCEPTED; không đổi trạng thái cuối sang REJECTED; không rút đơn sau khi được nhận. |
| Theo dõi | Ứng viên đọc được ACCEPTED, lịch sử NEW → VIEWED → INTERVIEW → ACCEPTED và 3 thông báo chưa đọc. |
| Đóng tin | Tin CLOSED không còn hiển thị công khai; đơn đã nộp vẫn được lưu. Có audit log và thông báo. |

## Cách chạy lại

Từ gốc repository, dùng PowerShell:

```powershell
cd source_code/server
$env:DEBUG='False'
..\..\.venv\Scripts\python.exe -m pytest tests/test_workflows.py::test_end_to_end_register_profile_company_job_apply_process -v -p no:cacheprovider
```

Kết quả lần chạy ghi nhận:

```text
collected 1 item

tests/test_workflows.py::test_end_to_end_register_profile_company_job_apply_process PASSED [100%]

1 passed, 2 warnings in 1.83s
```

## Phạm vi và giới hạn

Đây là kiểm thử xuyên suốt các module qua API trong tiến trình TestClient; không mở trình duyệt và không kết nối database của nhóm. Hai cảnh báo deprecation liên quan Starlette/httpx và tên hằng HTTP 422, không làm test thất bại. Lần chạy này không xác minh SMTP thật, MySQL/Aiven, Docker hoặc hosting.

Báo cáo kiểm tra MySQL/trình duyệt trước đó được lưu riêng tại [HOSTING_REVIEW_20261118.md](HOSTING_REVIEW_20261118.md), với giới hạn của đợt kiểm tra đó. File này là minh chứng cho lần chạy lại ngày 19/11/2026; không chứa dữ liệu tài khoản thật, token hoặc cấu hình môi trường riêng.
