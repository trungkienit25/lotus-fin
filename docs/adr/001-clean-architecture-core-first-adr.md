# ADR 001: Tiêu Chuẩn Clean Architecture, Giới Hạn < 200 Dòng/File & Cấm Tuyệt Đối Script Ad-hoc

- **Trạng thái:** Chấp thuận (Accepted)
- **Áp dụng cho:** Hệ thống Lotus-Fin

---

## 1. Bối cảnh (Context)
Trong quá trình phát triển các hệ thống FinTech, codebase dễ phát sinh các script ad-hoc tạm bợ (vá dữ liệu, gán số thứ tự, xuất Excel, xử lý khiếu nại). Điều này gây ra:
- Phân mảnh logic nghiệp vụ nghiêm trọng.
- Thiếu kiểm thử tự động, dễ gây lỗi tái diễn khi xử lý tiền tệ/giao dịch.
- Codebase bị phình to và khó bảo trì cho cả kỹ sư lẫn AI Agent.

---

## 2. Quyết định (Decision)

### 2.1. Nguyên Tắc Bắt Buộc: Core-First Implementation (No Ad-hoc Scripts)
- **Cấm tuyệt đối**: Không được tạo bất kỳ script tạm bợ, file ad-hoc hay thư mục công cụ nào ngoài kiến trúc chuẩn.
- **Mọi nghiệp vụ phải được thiết kế trực tiếp vào Core**:
  1. `Domain Layer`: Định nghĩa entities, validation rules, value objects.
  2. `UseCase Layer`: Cài đặt logic nghiệp vụ, transaction và mutex locking.
  3. `Delivery / Transport Layer`: Expose REST API chuẩn hoặc CLI Worker chuẩn.

### 2.2. Giới Hạn Nghiêm Ngặt: File Code < 200 Dòng
- Toàn bộ file source code trong hệ thống không được vượt quá **200 dòng/file**.
- Khi một file tiệm cận 200 dòng, bắt buộc phải phân rã thành các module chuyên biệt:
  - Tách UseCase thành: Coordinator + Evaluator + Query Handlers.
  - Tách Handler thành: Controllers + Query Controllers + Parsers/DTOs.

### 2.3. Quy Chuẩn Kiểm Thử Bắt Buộc
Mọi UseCase trong Core đều phải có:
- **Unit Tests**: Table-driven tests bao phủ toàn bộ edge cases.
- **Delivery E2E Tests**: Kiểm thử tích hợp request/response.
- **Benchmark Tests**: Đo lường thông lượng (throughput) và cấp phát bộ nhớ.

---

## 3. Hệ quả (Consequences)
- **Ưu điểm**:
  - Codebase luôn gọn gàng, tinh khiết, tuân thủ Clean Architecture.
  - AI Agent đọc hiểu nhanh chóng, không bị quá tải context token, chỉnh sửa code chính xác tuyệt đối.
  - Loại bỏ hoàn toàn nợ kỹ thuật từ script rác.

