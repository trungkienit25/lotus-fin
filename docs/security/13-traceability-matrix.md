# 13 — Ma Trận Truy Vết Yêu Cầu Bảo Mật

> **Tài liệu:** Lotus Fin Security Documentation Set · **Phiên bản:** 1.0 · **Ngày:** 2026-09-18
> **Phân loại:** `INTERNAL`
> **Mục đích:** Nối liền **Use Case nghiệp vụ (SRS) → Mối đe dọa → Kiểm soát bảo mật → Kịch bản kiểm thử**, để không một yêu cầu nào bị bỏ sót và không một kiểm soát nào tồn tại mà không kiểm chứng được.

---

## 1. Vì sao cần ma trận truy vết

Một bộ tài liệu bảo mật có thể rất đầy đủ mà vẫn thất bại theo hai cách, và ma trận này tồn tại để chặn cả hai:

1. **Kiểm soát mồ côi** — một kiểm soát được thiết kế công phu nhưng không ai biết nó bảo vệ điều gì. Khi cần tối ưu hiệu năng, nó sẽ bị gỡ bỏ vì "không thấy có tác dụng gì".
2. **Mối đe dọa mồ côi** — một mối đe dọa được liệt kê trong threat model nhưng không kiểm soát nào thực sự xử lý nó. Nó được ghi ra, được đọc qua, rồi bị quên.

Ma trận truy vết làm cho cả hai trường hợp trở nên **hiển thị được**: mỗi hàng phải có đủ bốn cột, và một ô trống là một câu hỏi bắt buộc phải trả lời.

---

## 2. Danh mục kiểm soát bảo mật

Tổng hợp toàn bộ kiểm soát đã đặc tả, gán mã định danh `CTL-nnn`.

### 2.1. Nhóm Định danh & Truy cập

| ID | Kiểm soát | Tài liệu | Đe dọa giảm thiểu |
| :--- | :--- | :--- | :--- |
| `CTL-001` | Băm mật khẩu Argon2id | `04 §2.1` | `THR-004` |
| `CTL-002` | Khóa tài khoản lũy tiến | `04 §2.1` | `THR-004` |
| `CTL-003` | Đối chiếu mật khẩu rò rỉ | `04 §2.1` | `THR-004` |
| `CTL-004` | Phản hồi đồng nhất & thời gian hằng định khi đăng nhập | `04 §2.1` | `THR-006` |
| `CTL-005` | MFA bắt buộc cho OWNER/ACCOUNTANT | `04 §2.2` | `THR-004`, `THR-043` |
| `CTL-006` | WebAuthn bắt buộc cho nhân sự nền tảng | `04 §2.2` | `THR-043` |
| `CTL-007` | Step-Up Authentication cho thao tác tài chính | `04 §2.3` | `THR-008`, `RR-01` |
| `CTL-008` | Cookie `__Host-` HttpOnly/Secure/SameSite=Strict | `04 §4.2` | `THR-007`, `THR-008` |
| `CTL-009` | Sinh lại session ID sau nâng cấp đặc quyền | `04 §4.3` | `THR-009` |
| `CTL-010` | Thu hồi phiên phía server | `04 §4.3` | `THR-007` |
| `CTL-011` | JWT ES256 TTL 5 phút, khai báo thuật toán tường minh | `04 §4.4` | `THR-014` |
| `CTL-012` | Tra cứu lại vai trò từ DB ở tầng UseCase | `04 §4.4` | `THR-015` |
| `CTL-013` | Ma trận RBAC theo quyền nhỏ nhất | `04 §3.2` | `THR-015`, `THR-016` |
| `CTL-014` | Phân quyền lớp 1 — middleware | `04 §5.1` | `THR-015` |
| `CTL-015` | Phân quyền lớp 2 — kiểm tra quyền sở hữu ở UseCase | `04 §5.2` | `THR-016` |
| `CTL-016` | ⭐ **Phân quyền lớp 3 — PostgreSQL RLS `FORCE`** | `04 §5.3` | `THR-016`, `THR-021` |
| `CTL-017` | Truy cập Just-in-Time cho quản trị | `04 §7.1` | `THR-044` |
| `CTL-018` | Break-glass nguyên tắc 4 mắt | `04 §7.2` | `THR-045` |
| `CTL-019` | Rà soát quyền truy cập định kỳ | `04 §8` | `THR-044` |
| `CTL-020` | Định danh nhân sự nền tảng tách biệt hoàn toàn | `04 §1` | `THR-043` |

### 2.2. Nhóm Bảo vệ dữ liệu

| ID | Kiểm soát | Tài liệu | Đe dọa giảm thiểu |
| :--- | :--- | :--- | :--- |
| `CTL-021` | Bộ thuật toán mật mã chuẩn + danh sách cấm | `05 §2` | `THR-003` |
| `CTL-022` | Envelope encryption với DEK theo tenant | `05 §3.1` | `THR-022` |
| `CTL-023` | Luân chuyển khóa không gián đoạn | `05 §3.3` | `THR-022` |
| `CTL-024` | TLS 1.3 + mTLS mọi đoạn đường | `05 §4` | `THR-003`, `THR-038` |
| `CTL-025` | `sslmode=verify-full` tới PostgreSQL | `05 §4` | `THR-003` |
| `CTL-026` | Mã hóa cấp trường cho dữ liệu `L4` | `05 §5.2` | `THR-022` |
| `CTL-027` | Blind index cho trường cần tìm kiếm | `05 §5.3` | `THR-022` |
| `CTL-028` | ⭐ **Token hóa số tài khoản ngân hàng** | `05 §6` | `THR-022`, `THR-027` |
| `CTL-029` | ⭐ **Masking cưỡng chế bằng hệ thống kiểu trước `TB-5`** | `05 §7.2` | `THR-027`, `THR-040` |
| `CTL-030` | DLP quét luồng ra | `05 §8`, `07 §5.2` | `THR-027`, `THR-040` |
| `CTL-031` | Crypto-shredding khi xóa dữ liệu | `05 §9` | Nghĩa vụ xóa dữ liệu |
| `CTL-032` | Chính sách phân loại & lưu trữ dữ liệu | `02 §2`, `§6` | Rò rỉ qua kênh phụ |

### 2.3. Nhóm An toàn ứng dụng

| ID | Kiểm soát | Tài liệu | Đe dọa giảm thiểu |
| :--- | :--- | :--- | :--- |
| `CTL-033` | Validate hai tầng cú pháp + ngữ nghĩa | `06 §2.1` | `THR-005`, `THR-019` |
| `CTL-034` | DTO allowlist, từ chối trường lạ | `06 §2.3` | `THR-019` |
| `CTL-035` | ⭐ **sqlc — triệt tiêu SQL injection ở cấp kiến trúc** | `06 §3.1` | `THR-020` |
| `CTL-036` | Chống CSV formula injection | `06 §3.2` | Tấn công vượt ranh giới hệ thống |
| `CTL-037` | Tắt XXE khi parse XML/XLSX | `06 §3.2` | `THR-031` |
| `CTL-038` | CSP nonce + `strict-dynamic`, không `unsafe-inline` | `06 §4.2` | `THR-007` |
| `CTL-039` | Cấm `dangerouslySetInnerHTML` bằng lint | `06 §4.1` | `THR-007` |
| `CTL-040` | Xử lý nội dung AI như dữ liệu không tin cậy | `06 §4.3` | `THR-007`, `THR-028` |
| `CTL-041` | Chống CSRF 4 lớp | `06 §5` | `THR-008` |
| `CTL-042` | Pipeline kiểm tra tệp tải lên 14 bước | `06 §6.2` | `THR-030`, `THR-031` |
| `CTL-043` | ⭐ **Parser sandbox gVisor không mạng** | `06 §6.3`, `08 §2.3` | `THR-030` |
| `CTL-044` | Giới hạn giải nén & tài nguyên | `06 §6.2` | `THR-031` |
| `CTL-045` | Bộ security header đầy đủ | `06 §7` | `THR-011`, `THR-013` |
| `CTL-046` | Fail closed trong mọi kiểm soát bảo mật | `06 §8` | Nhiều mối đe dọa |
| `CTL-047` | `Cache-Control: private, no-store` cho dữ liệu tenant | `06 §7` | `THR-011` |
| `CTL-048` | DTO riêng cho tầng hiển thị, không lộ entity domain | `06 §8` | `THR-010` |

### 2.4. Nhóm API & Tích hợp

| ID | Kiểm soát | Tài liệu | Đe dọa giảm thiểu |
| :--- | :--- | :--- | :--- |
| `CTL-049` | Thứ tự middleware chain có chủ đích | `07 §2.1` | Nhiều mối đe dọa |
| `CTL-050` | Rate limit đa chiều | `07 §3.1` | `THR-002`, `THR-004` |
| `CTL-051` | ⭐ **Rate limit theo chi phí tính toán** | `07 §3.2` | `THR-002`, `THR-042` |
| `CTL-052` | Ngân sách token LLM + circuit breaker | `07 §3.2` | `THR-042` |
| `CTL-053` | Idempotency với ràng buộc UNIQUE ở DB | `07 §4.2` | `THR-037` |
| `CTL-054` | Không nhận URL người dùng cho lời gọi ra ngoài | `07 §5.1` | `THR-039` |
| `CTL-055` | Egress Proxy allowlist theo domain và workload | `07 §5.2` | `THR-029`, `THR-039`, `THR-040` |
| `CTL-056` | Chặn metadata endpoint `169.254.169.254` | `07 §5.2`, `08 §5` | `THR-039` |
| `CTL-057` | mTLS + ghim chứng chỉ với Bank API | `07 §6.1` | `THR-038` |
| `CTL-058` | Xác thực webhook HMAC so sánh thời gian hằng định | `07 §6.2` | `THR-035` |
| `CTL-059` | Chống replay webhook bằng timestamp + nonce | `07 §6.2` | `THR-036` |
| `CTL-060` | Validate schema phản hồi từ bên thứ ba | `07 §6.3` | API10 |
| `CTL-061` | Đăng ký API bắt buộc, quét endpoint bóng tối | `07 §2.3` | API9 |

### 2.5. Nhóm Ranh giới AI (`TB-5`)

| ID | Kiểm soát | Tài liệu | Đe dọa giảm thiểu |
| :--- | :--- | :--- | :--- |
| `CTL-062` | ⭐⭐ **LLM không bao giờ sinh ra con số tài chính** | `07 §7.5` | `THR-028` |
| `CTL-063` | ⭐ **Đối chiếu chéo mọi con số AI sinh ra với giá trị engine** | `07 §7.5` | `THR-028` |
| `CTL-064` | Validate schema nghiêm ngặt phản hồi AI | `07 §7.6` | `THR-028` |
| `CTL-065` | Từ chối URL và HTML trong đầu ra AI | `07 §7.6` | `THR-007`, trích xuất dữ liệu |
| `CTL-066` | AI không có credential cơ sở dữ liệu | `01 §3.4`, `08 §1.2` | `THR-029`, `THR-032` |
| `CTL-067` | AI không có đường ra Internet trực tiếp | `08 §1.2` | `THR-029`, `THR-040` |
| `CTL-068` | AI không được gọi Bank API | `07 §5.2` | `THR-029` |
| `CTL-069` | Cảnh báo `CRITICAL` khi `tenant_id` không khớp | `07 §7.6`, `09 §4.2` | `THR-032` |
| `CTL-070` | Suy giảm chức năng có kiểm soát khi AI ngừng hoạt động | `02 §3.3`, `11 §4.3` | `THR-033` |

### 2.6. Nhóm Hạ tầng & Mạng

| ID | Kiểm soát | Tài liệu | Đe dọa giảm thiểu |
| :--- | :--- | :--- | :--- |
| `CTL-071` | Phân vùng mạng 6 vùng + NetworkPolicy `default-deny` | `08 §1` | `THR-017`, `THR-029` |
| `CTL-072` | Ảnh distroless, non-root, rootfs chỉ đọc, drop capability | `08 §2.1` | `THR-029` |
| `CTL-073` | Pod Security Standard `restricted` | `08 §2.2` | `THR-029` |
| `CTL-074` | CDN chống DDoS + WAF OWASP CRS | `08 §3` | `THR-001`, `THR-005` |
| `CTL-075` | TLS 1.3, HSTS preload, giám sát CT log | `08 §3.3` | `THR-003` |
| `CTL-076` | Credential DB động TTL 24 giờ từ Vault | `08 §4` | `THR-023` |
| `CTL-077` | Bí mật chỉ tồn tại trong bộ nhớ, không ghi xuống đĩa | `08 §4` | Lộ credential |
| `CTL-078` | Tài khoản DB quyền tối thiểu, không `BYPASSRLS` | `08 §4`, `04 §5.3` | `THR-023`, `THR-021` |
| `CTL-079` | ⭐ **Sao lưu bất biến WORM Object Lock** | `08 §6` | `THR-022`, Ransomware |
| `CTL-080` | Khóa mã hóa sao lưu tách biệt khỏi production | `08 §6` | `THR-022` |
| `CTL-081` | IaC, cấm thay đổi thủ công, phát hiện trôi cấu hình | `08 §8` | `THR-046` |

### 2.7. Nhóm Nhật ký & Giám sát

| ID | Kiểm soát | Tài liệu | Đe dọa giảm thiểu |
| :--- | :--- | :--- | :--- |
| `CTL-082` | Tách bạch 3 loại nhật ký | `09 §1` | Rò rỉ qua log |
| `CTL-083` | ⭐ **Chống rò rỉ qua log bằng 4 lớp kỹ thuật** | `09 §2.2` | Rò rỉ qua log |
| `CTL-084` | Danh mục sự kiện kiểm toán đầy đủ | `09 §3.1` | `THR-018` |
| `CTL-085` | ⭐ **Nhật ký kiểm toán chuỗi băm + niêm phong WORM** | `09 §3.3` | `THR-026` |
| `CTL-086` | Bảng audit chỉ cho phép INSERT | `09 §3.3` | `THR-026` |
| `CTL-087` | 20 use case phát hiện trong SIEM | `09 §4.2` | Nhiều mối đe dọa |
| `CTL-088` | Đồng bộ thời gian NTP, UTC | `09 §5` | Điều tra sự cố |
| `CTL-089` | Chống mệt mỏi cảnh báo | `09 §4.4` | Thất bại của giám sát |

### 2.8. Nhóm SDLC & Chuỗi cung ứng

| ID | Kiểm soát | Tài liệu | Đe dọa giảm thiểu |
| :--- | :--- | :--- | :--- |
| `CTL-090` | Threat modeling bắt buộc ở giai đoạn thiết kế | `10 §2` | Lỗi thiết kế |
| `CTL-091` | Chuẩn lập trình an toàn cưỡng chế bằng lint | `10 §3` | Nhiều mối đe dọa |
| `CTL-092` | 14 cổng kiểm soát CI/CD | `10 §4.2` | Nhiều mối đe dọa |
| `CTL-093` | ⭐ **Cổng test cô lập tenant (RLS) trên DB thật** | `10 §4.3` | `THR-021` |
| `CTL-094` | Test regression masking | `10 §4.2` #9 | `THR-027` |
| `CTL-095` | Test rò rỉ log | `10 §4.2` #10 | Rò rỉ qua log |
| `CTL-096` | SBOM CycloneDX + ký ảnh Cosign | `10 §5.2` | `THR-012` |
| `CTL-097` | Bảo vệ nhánh, 2 reviewer cho code nhạy cảm | `10 §5.3` | `THR-012` |
| `CTL-098` | ⭐ **Mô phỏng AI bị xâm phạm hằng quý** | `10 §6.1` | `THR-029` — *kiểm chứng giả định phòng thủ* |
| `CTL-099` | Kiểm thử xâm nhập độc lập hằng năm | `10 §6` | Nhiều mối đe dọa |
| `CTL-100` | Đào tạo bảo mật theo vai trò | `10 §7` | Yếu tố con người |

---

## 3. 🔗 Ma trận truy vết theo Use Case

### UC001 — Upload & Normalize Financial Data

| Yêu cầu bảo mật | Đe dọa | Kiểm soát | Kịch bản kiểm thử |
| :--- | :--- | :--- | :--- |
| Chỉ vai trò được phép mới tải lên được | `THR-016` | `CTL-013`, `CTL-014`, `CTL-015` | `VIEWER` gọi `POST /documents` → nhận `403` |
| Tệp độc hại không được xử lý | `THR-030`, `THR-031` | `CTL-042`, `CTL-043`, `CTL-044` | Tải lên PDF có payload khai thác → bị chặn hoặc bị cô lập trong sandbox |
| Đổi tên tệp thực thi không qua mặt được | `THR-030` | `CTL-042` #3 | Đổi tên `payload.exe` → `baocao.pdf` → bị từ chối ở bước kiểm tra magic byte |
| Zip bomb không làm cạn tài nguyên | `THR-031` | `CTL-044` | Tải lên XLSX tỉ lệ nén 1000:1 → bị chặn, sandbox không vượt giới hạn |
| Path traversal không ghi đè được tệp | `THR-030` | `CTL-042` #6 | Tên tệp `../../etc/passwd` → lưu với khóa UUID, tên gốc chỉ là metadata |
| PII được che mờ trước khi sang AI | `THR-027` | `CTL-029`, `CTL-028` | Kiểm tra payload gửi sang `lotus-ai` không chứa CCCD, email, số tài khoản |
| Không truy cập được tài liệu tenant khác | `THR-016`, `THR-021` | `CTL-015`, `CTL-016` | Tenant A gọi `GET /documents/{id_của_B}` → `404` *(không phải `403` — tránh rò rỉ sự tồn tại)* |
| Mọi lần upload/download đều được audit | `THR-018` | `CTL-084` | Kiểm tra bản ghi `document.uploaded` có đủ trường |

### UC002 — Forecast Cash Flow & Trigger Shortfall Alert

| Yêu cầu bảo mật | Đe dọa | Kiểm soát | Kịch bản kiểm thử |
| :--- | :--- | :--- | :--- |
| Dự báo chỉ dùng dữ liệu của chính tenant | `THR-021` | `CTL-016` | Đặt `app.current_tenant` = A → kết quả không chứa dữ liệu của B |
| Worker chạy job vẫn bị RLS ràng buộc | `THR-021` | `CTL-016` | Job của tenant A không đọc được dữ liệu tenant B |
| Endpoint tính toán lại không bị lạm dụng | `THR-002` | `CTL-051` | Gọi 200 lần `POST /forecasts/recalculations` → bị chặn theo ngân sách chi phí |
| Email cảnh báo không rò rỉ số liệu | Rò rỉ qua kênh phụ | `CTL-032` | Kiểm tra nội dung email chỉ chứa liên kết đăng nhập |
| Số liệu dự báo do engine tính, không phải AI | `THR-028` | `CTL-062` | Xác minh đường code: forecast không đi qua `lotus-ai` |

### UC003 — Analyze Business Financial Health

| Yêu cầu bảo mật | Đe dọa | Kiểm soát | Kịch bản kiểm thử |
| :--- | :--- | :--- | :--- |
| ⭐ **DSCR do Deterministic Engine tính** | `THR-028` | `CTL-062` | Giá trị DSCR hiển thị = giá trị engine, không lấy từ văn bản AI |
| ⭐ **Số trong văn bản AI khớp giá trị engine** | `THR-028` | `CTL-063` | Chèn số sai vào phản hồi AI giả lập → hệ thống từ chối + cảnh báo `SEC-AI-MISMATCH` |
| Văn bản AI không chứa HTML/URL | `THR-007` | `CTL-065`, `CTL-040` | Phản hồi AI chứa `<script>` hoặc URL → bị từ chối |
| Báo cáo xuất PDF không rò rỉ qua CSV | `06 §3.2` | `CTL-036` | Tên đối tác là `=HYPERLINK(...)` → được thoát ký tự khi xuất |
| Báo cáo chỉ truy cập được bởi tenant sở hữu | `THR-021` | `CTL-016` | Tenant B truy cập báo cáo của A → không có kết quả |

### UC004 — Match Financing Options

| Yêu cầu bảo mật | Đe dọa | Kiểm soát | Kịch bản kiểm thử |
| :--- | :--- | :--- | :--- |
| Chỉ `OWNER` nộp được hồ sơ vay | `THR-015` | `CTL-013`, `CTL-015` | `ACCOUNTANT` gọi `POST /financing-applications` → `403` |
| Nộp hồ sơ yêu cầu step-up MFA | `THR-008`, `RR-01` | `CTL-007` | Gọi không có MFA gần đây → yêu cầu xác thực lại |
| Không tạo hồ sơ trùng lặp | `THR-037` | `CTL-053` | Gửi 2 lần cùng `Idempotency-Key` → chỉ 1 hồ sơ, 2 phản hồi giống hệt |
| Webhook giả mạo bị từ chối | `THR-035` | `CTL-058` | Gửi webhook sai chữ ký → `401` + cảnh báo |
| Webhook phát lại bị từ chối | `THR-036` | `CTL-059` | Phát lại webhook hợp lệ cũ → bị từ chối bởi kiểm tra nonce |
| Đo thời gian không suy ra được chữ ký | `THR-035` | `CTL-058` | Đo thời gian phản hồi với chữ ký sai ở nhiều vị trí → không có tương quan |
| Tấn công SSRF không gọi được nội bộ | `THR-039` | `CTL-054`, `CTL-056` | Không tồn tại tham số URL nào trong API |
| Phản hồi bất thường từ ngân hàng bị chặn | API10 | `CTL-060` | Lãi suất âm trong phản hồi → bị từ chối |
| Nộp hồ sơ được audit mức `HIGH` | `THR-018` | `CTL-084` | Bản ghi `financing.application.submitted` có IP, user-agent, MFA |

### UC005 — Interactive Financial Copilot Chat

| Yêu cầu bảo mật | Đe dọa | Kiểm soát | Kịch bản kiểm thử |
| :--- | :--- | :--- | :--- |
| Dữ liệu gửi sang AI đã che mờ | `THR-027`, `THR-040` | `CTL-029` | Kiểm tra prompt không chứa tên doanh nghiệp, số tài khoản, PII |
| ⭐ **AI không truy cập được dữ liệu tenant khác** | `THR-032` | `CTL-066`, `CTL-069` | Phản hồi AI mang `tenant_id` sai → từ chối + cảnh báo `CRITICAL` |
| AI bị xâm phạm không đọc được DB | `THR-029` | `CTL-066`, `CTL-071` | **Bài tập mô phỏng** `10 §6.1` |
| AI bị xâm phạm không trích xuất được dữ liệu | `THR-029`, `THR-040` | `CTL-067`, `CTL-055` | Từ trong container AI, thử kết nối ra Internet → thất bại |
| Chi phí LLM có trần | `THR-042` | `CTL-052` | Vượt 100% ngân sách → circuit breaker ngắt |
| Truy vấn bị guardrail chặn được ghi log `SEC-403` | SRS UC005 | `CTL-084` | Bản ghi `copilot.blocked` được tạo *(guardrail thuộc nhóm AI)* |
| Lịch sử hội thoại chỉ tenant sở hữu xem được | `THR-021` | `CTL-016` | Tenant B truy cập hội thoại của A → không có kết quả |
| Nội dung AI render an toàn trên giao diện | `THR-007` | `CTL-040`, `CTL-039` | Phản hồi AI chứa payload XSS → render dưới dạng văn bản thuần |

### UC006 — Simulate Financing Repayment Scenarios

| Yêu cầu bảo mật | Đe dọa | Kiểm soát | Kịch bản kiểm thử |
| :--- | :--- | :--- | :--- |
| ⭐ **Lịch trả nợ do engine tính** | `THR-028` | `CTL-062` | Bảng trả nợ không đi qua `lotus-ai` |
| Tham số phi lý bị từ chối | `THR-019` | `CTL-033` | Lãi suất `-50%`, kỳ hạn `99999` → `422` |
| Không gán được trường ngoài phép | `THR-019` | `CTL-034` | Gửi kèm `"tenant_id": "<id khác>"` → từ chối vì trường lạ |
| Tính toán tiền tệ chính xác tuyệt đối | Toàn vẹn dữ liệu | `01 §4` | Kiểm thử với số lớn và nhiều chữ số thập phân → không sai số tích lũy |
| Kịch bản chỉ tenant sở hữu xem được | `THR-021` | `CTL-016` | RLS chặn truy cập chéo |

---

## 4. Ma trận độ bao phủ mối đe dọa

Xác minh rằng **mọi** mối đe dọa trong `03` đều có ít nhất một kiểm soát.

| Nhóm mối đe dọa | Số lượng | Có kiểm soát | Độ bao phủ |
| :--- | :---: | :---: | :---: |
| `TB-1` — Biên *(THR-001→006)* | 6 | 6 | ✅ 100% |
| `TB-2` — BFF *(THR-007→013)* | 7 | 7 | ✅ 100% |
| `TB-3` — Core API *(THR-014→019)* | 6 | 6 | ✅ 100% |
| `TB-4` — Dữ liệu *(THR-020→026)* | 7 | 7 | ✅ 100% |
| `TB-5` — AI *(THR-027→034)* | 8 | 8 | ✅ 100% |
| `TB-6` — Bank API *(THR-035→039)* | 5 | 5 | ✅ 100% |
| `TB-7` — LLM *(THR-040→042)* | 3 | 3 | ✅ 100% |
| `TB-8` — Quản trị *(THR-043→046)* | 4 | 4 | ✅ 100% |
| **Tổng** | **46** | **46** | ✅ **100%** |

---

## 5. ⭐ Mười kiểm soát quan trọng nhất

Nếu chỉ có nguồn lực để triển khai đúng mười thứ, đây là mười thứ đó — xếp theo giá trị phòng thủ trên mỗi đơn vị công sức.

| Hạng | Kiểm soát | Vì sao quan trọng nhất |
| :---: | :--- | :--- |
| **1** | `CTL-016` — **PostgreSQL RLS `FORCE`** | Lưới an toàn duy nhất **không phụ thuộc vào việc lập trình viên nhớ viết đúng**. Chặn rò rỉ chéo tenant — rủi ro tồn tại nhất của nền tảng SaaS đa người thuê. |
| **2** | `CTL-062` — **LLM không sinh con số tài chính** | Vô hiệu hóa **toàn bộ một lớp tấn công** thao túng AI để bẻ cong quyết định tín dụng. Đạt được bằng kiến trúc, không phải bằng bộ lọc. |
| **3** | `CTL-035` — **sqlc** | Triệt tiêu SQL injection ở cấp kiến trúc thay vì phụ thuộc kỷ luật. Viết code có lỗ hổng đòi hỏi phải cố ý đi vòng qua tầng data access. |
| **4** | `CTL-029` — **Masking cưỡng chế bằng hệ thống kiểu** | Biến việc quên che mờ dữ liệu từ "lỗi runtime âm thầm" thành "lỗi biên dịch". |
| **5** | `CTL-043` — **Parser sandbox không mạng** | Biến một khai thác RCE thành công thành vô giá trị. Hiện thân rõ nhất của *Assume Breach*. |
| **6** | `CTL-085` — **Audit chuỗi băm + WORM** | Không có nhật ký đáng tin cậy thì không điều tra được, không chứng minh được, không học được từ sự cố. |
| **7** | `CTL-008` — **Cookie phiên qua BFF** | Hạ bán kính thiệt hại của XSS từ "chiếm tài khoản vĩnh viễn" xuống "lạm dụng trong phiên". |
| **8** | `CTL-079` — **Sao lưu bất biến** | Kiểm soát chống ransomware quan trọng nhất. Vô hiệu hóa bước đầu tiên của mọi chiến dịch ransomware hiện đại. |
| **9** | `CTL-093` — **Cổng CI test cô lập tenant** | Biến kiểm soát quan trọng nhất *(`CTL-016`)* thành thứ **không thể vô tình phá vỡ** trong tương lai. |
| **10** | `CTL-051` — **Rate limit theo chi phí** | Chặn lớp DoS mà rate limit thông thường hoàn toàn bỏ lọt trong hệ thống có endpoint AI đắt đỏ. |

> **Điểm chung của cả mười kiểm soát:** chúng đều chuyển bảo mật từ chỗ *phụ thuộc vào việc con người luôn làm đúng* sang chỗ *hệ thống không cho phép làm sai*. Đó là tiêu chí phân biệt một kiểm soát bền vững với một kiểm soát chỉ đúng vào ngày nó được viết ra.

---

## 6. Điều hướng

| ← Trước | Về đầu |
| :--- | :--- |
| [12 — Bản đồ tuân thủ ISO 27001 & PCI DSS](12-compliance-iso27001-pcidss.md) | [README — Tổng quan bộ tài liệu](README.md) |
