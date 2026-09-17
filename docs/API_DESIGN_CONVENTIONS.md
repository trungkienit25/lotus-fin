# 📐 Quy Chuẩn Thiết Kế RESTful API Endpoints — Lotus-Fin

> **Tài liệu hướng dẫn chung khi thiết kế API cho hệ thống Lotus-Fin**  
> **Áp dụng cho:** Toàn bộ Backend Services, Gateway và Microservices  

---

## 1. NGUYÊN TẮC ĐẶT TÊN ENDPOINT (URL CONVENTIONS)

### 1.1. Cấu trúc URL tiêu chuẩn
Mọi API endpoint phải tuân theo tiền tố định danh phiên bản:
```
/api/v{version}/{resource-collection}[/{resource-id}][/{sub-resource}]
```
*Ví dụ:*
- `/api/v1/transactions`
- `/api/v1/accounts/acc_12345/statements`
- `/api/v1/payment-gateways/vietqr/orders`

### 1.2. Quy tắc đặt tên danh từ số nhiều (Plural Nouns)
- **Bắt buộc dùng danh từ số nhiều** cho tài nguyên: `/users`, `/transactions`, `/orders`, `/wallets`.
- **Dùng kebab-case** (chữ thường, ngăn cách bằng dấu gạch ngang) cho đường dẫn có nhiều từ: `/payment-methods`, `/bank-accounts`, `/audit-logs`.
- **Không dùng động từ trong URL**:
  - ❌ *Sai:* `POST /api/v1/createTransaction`, `GET /api/v1/getUserInfo?id=1`
  - ✅ *Đúng:* `POST /api/v1/transactions`, `GET /api/v1/users/1`

### 1.3. Độ sâu phân cấp (Resource Nesting)
- Giới hạn lồng nhau tối đa **2 cấp**:
  - ✅ *Đúng:* `GET /api/v1/wallets/:id/transactions`
  - ❌ *Sai:* `GET /api/v1/users/:id/wallets/:id/cards/:id/transactions` (Nên đổi thành: `GET /api/v1/cards/:id/transactions`)

---

## 2. QUY CHUẨN HTTP METHODS

| HTTP Method | Ý nghĩa | Tính Chất | Trạng Thái Trả Về Tiêu Chuẩn |
| :--- | :--- | :--- | :--- |
| **`GET`** | Đọc dữ liệu tài nguyên | Safe, Idempotent | `200 OK` |
| **`POST`** | Tạo mới tài nguyên hoặc kích hoạt quy trình | Non-Idempotent | `201 Created` (nếu tạo mới), `200 OK` (nếu xử lý luồng) |
| **`PUT`** | Ghi đè toàn bộ tài nguyên | Idempotent | `200 OK` |
| **`PATCH`** | Cập nhật một phần thuộc tính tài nguyên | Idempotent | `200 OK` |
| **`DELETE`** | Xóa tài nguyên (Hard/Soft Delete) | Idempotent | `200 OK` hoặc `204 No Content` |

---

## 3. CẤU TRÚC JSON RESPONSE CHUẨN (RESPONSE ENVELOPE)

Tất cả các API trong hệ thống phải bọc response theo định dạng JSON đồng nhất:

### 3.1. Phản hồi thành công (Success Response)
```json
{
  "success": true,
  "data": {
    "id": "tx_987654321",
    "amount": 500000,
    "currency": "VND",
    "status": "COMPLETED",
    "createdAt": "2026-09-17T15:00:00.000Z"
  },
  "meta": {
    "requestId": "req_abc123xyz",
    "timestamp": 1789657529
  }
}
```

### 3.2. Phản hồi danh sách phân trang (Paginated List Response)
```json
{
  "success": true,
  "data": [
    { "id": "tx_01", "amount": 100000 },
    { "id": "tx_02", "amount": 250000 }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "totalItems": 150,
    "totalPages": 8,
    "hasNext": true,
    "hasPrev": false
  },
  "meta": {
    "requestId": "req_abc123xyz",
    "timestamp": 1789657529
  }
}
```

### 3.3. Phản hồi lỗi chuẩn (Error Response)
```json
{
  "success": false,
  "error": {
    "code": "INSUFFICIENT_WALLET_BALANCE",
    "message": "Số dư trong ví không đủ để thực hiện giao dịch.",
    "details": [
      {
        "field": "amount",
        "issue": "Yêu cầu 500000 VND, số dư khả dụng hiện tại là 120000 VND."
      }
    ]
  },
  "meta": {
    "requestId": "req_abc123xyz",
    "timestamp": 1789657529
  }
}
```

---

## 4. QUY CHUẨN HTTP STATUS CODES

### Thành công (2xx):
- `200 OK`: Truy vấn, cập nhật (`PATCH`/`PUT`) hoặc thực thi action thành công.
- `201 Created`: Tạo mới bản ghi tài nguyên thành công (`POST`).
- `204 No Content`: Xóa thành công và không cần trả về body (`DELETE`).

### Lỗi từ phía Client (4xx):
- `400 Bad Request`: Sai cú pháp request, thiếu param bắt buộc.
- `401 Unauthorized`: Chưa đăng nhập hoặc JWT Token hết hạn/không hợp lệ.
- `403 Forbidden`: Đã đăng nhập nhưng không có quyền truy cập tài nguyên này (RBAC Block).
- `404 Not Found`: Không tìm thấy tài nguyên theo ID yêu cầu.
- `409 Conflict`: Xung đột dữ liệu (ví dụ: trùng mã đơn hàng, tài khoản đã tồn tại).
- `422 Unprocessable Entity`: Dữ liệu gửi lên đúng định dạng JSON nhưng sai logic nghiệp vụ/validation.
- `429 Too Many Requests`: Vượt quá giới hạn Rate Limit.

### Lỗi từ phía Server (5xx):
- `500 Internal Server Error`: Lỗi hệ thống ngoài tầm kiểm soát.
- `502 Bad Gateway`: Lỗi kết nối tới dịch vụ bên thứ ba (Cổng ngân hàng / PayPal timeout).
- `503 Service Unavailable`: Hệ thống đang bảo trì.

---

## 5. CÁC NGUYÊN TẮC BẮT BUỘC DÀNH CHO FINTECH

1. **Khóa chống gửi trùng lặp (`Idempotency-Key` Header):**
   - Mọi endpoint làm thay đổi số dư hoặc trừ tiền (`POST /api/v1/payments`, `POST /api/v1/transfers`) bắt buộc phải nhận header `Idempotency-Key: <UUID>`.
2. **Xác thực chữ ký Webhook (`X-Signature` Header):**
   - Mọi Webhook nhận từ VietQR / PayPal / Ngân hàng phải kiểm tra HMAC SHA256 signature để chống giả mạo request.
3. **Mã lỗi nghiệp vụ có ý nghĩa (Semantic Error Codes):**
   - Không chỉ trả về status code 400 chung chung, `error.code` phải là chuỗi in hoa phân tách bằng gạch dưới (Ví dụ: `INVALID_OTP`, `TRANSACTION_EXPIRED`, `DAILY_LIMIT_EXCEEDED`).
4. **Audit Tracing:**
   - Mọi request gửi lên phải sinh và ghi kèm `requestId` trong log để truy vết khi xảy ra khiếu nại giao dịch.

