# Checklist nghiệm thu — T05C354

Ngày 23/11/2026. Phụ trách: Nguyễn Thiên Bảo (N25DTCN078).
Kết quả tự động: xem [báo cáo](T05C354_HANDOFF.md). Chỉ đánh dấu khi có bằng chứng.

## Kiểm tra trên môi trường demo

- [ ] MySQL đúng database test; migration tại head; đọc/ghi được.
- [ ] Đăng ký/đăng nhập; không thể tự đăng ký Admin.
- [ ] Công ty: tạo → từ chối có lý do → sửa → gửi lại → duyệt.
- [ ] Tin: nháp → gửi duyệt → duyệt → công khai → đóng.
- [ ] Tìm kiếm, lọc, lưu/bỏ lưu và xem lại trong hồ sơ.
- [ ] Ứng tuyển bằng CV hợp lệ; chặn ứng tuyển trùng và file sai.
- [ ] Nhà tuyển dụng xem CV, đổi trạng thái; ứng viên xem lịch sử.
- [ ] Người khác công ty không tải CV hoặc xem đơn không thuộc quyền.
- [ ] Thông báo và số chưa đọc cập nhật khi đọc.
- [ ] SMTP test: nhận email xác thực/quên mật khẩu.
- [ ] Tắt backend: UI báo lỗi, không báo lưu thành công.
- [ ] Giao diện desktop và 375px không che nút thao tác.
- [ ] File upload còn truy cập đúng quyền sau khi khởi động lại backend.

Các mục trên đang chờ nghiệm thu thủ công, không phải kết luận có lỗi.

## Điều kiện đóng task

- [ ] Nhận kết quả PB-025/PB-026 và danh sách lỗi của nhóm.
- [ ] Blocker/critical đã sửa và kiểm tra lại, hoặc có quyết định phạm vi của nhóm.
- [ ] Hoàn thành demo trên MySQL và trình duyệt thật.
- [ ] Phần hoãn có người nhận và quyết định rõ ràng.
- [ ] PR có mã T05C354, được review; đính kèm minh chứng lên thẻ task.

Blocker: không thể cài/chạy hoặc thực hiện luồng demo chính.
Critical: mất dữ liệu, vượt quyền hoặc sai nghiệp vụ nghiêm trọng.
Mỗi lỗi cần bước tái hiện, mong đợi/thực tế, môi trường, commit sửa và kết quả kiểm tra lại.
