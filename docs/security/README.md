# 🔐 Lotus Fin — Bộ Tài Liệu An Toàn Thông Tin (Security Documentation Set)

> **Hệ thống:** Lotus Fin — AI-Powered Financial Copilot for SMEs
> **Đường đua:** FinTechathon 2026 — Topic E (SME Finance Copilot) · *Trọng số Security & Compliance: 30%*
> **Phiên bản:** 1.0 · **Ngày ban hành:** 2026-09-18
> **Phân loại tài liệu:** `INTERNAL`

---

## 1. Mục đích

Bộ tài liệu này đặc tả **toàn bộ kiến trúc an toàn thông tin của nền tảng Lotus Fin ở tầng ứng dụng và hạ tầng** (Backend Go + Frontend Next.js + dữ liệu + vận hành), từ mô hình mối đe dọa cho tới các kiểm soát cụ thể và bản đồ tuân thủ chuẩn quốc tế.

Tài liệu được viết để phục vụ đồng thời ba nhóm người đọc:

| Người đọc | Đọc phần nào trước |
| :--- | :--- |
| **Kỹ sư triển khai (BE/FE/DevOps)** | `01` → `04` → `06` → `07` → `10` |
| **Ban giám khảo / Kiểm toán viên** | `README` → `03` (Threat Model) → `12` (Compliance Mapping) → `13` (Traceability) |
| **Quản trị rủi ro / Vận hành** | `02` → `09` → `11` → `12` |

---

## 2. ⚠️ Ranh giới trách nhiệm (Scope Ownership)

Lotus Fin chia bề mặt bảo mật thành **hai vùng trách nhiệm tách biệt**. Việc phân tách này là chủ ý về mặt kiến trúc, không chỉ về mặt tổ chức: nó tạo ra một **trust boundary có thể kiểm chứng (TB-5)** giữa lõi giao dịch và lõi AI.

### 2.1. TRONG phạm vi bộ tài liệu này (Platform Security)

✅ Kiến trúc hệ thống BE + FE, phân vùng tin cậy, mô hình mối đe dọa STRIDE
✅ Xác thực, phân quyền RBAC, quản lý phiên, cô lập đa người thuê (multi-tenant isolation)
✅ Mật mã, quản lý khóa, che mờ & token hóa dữ liệu nhạy cảm, vòng đời dữ liệu
✅ An toàn ứng dụng web (OWASP ASVS L2 / Top 10) — cụ thể cho Go và Next.js
✅ An toàn API, webhook, tích hợp Bank API, kiểm soát luồng ra (egress control)
✅ An toàn hạ tầng, mạng, container, bí mật (secrets), sao lưu
✅ Nhật ký kiểm toán, giám sát, phát hiện xâm nhập
✅ Secure SDLC, an toàn chuỗi cung ứng phần mềm
✅ Ứng phó sự cố, liên tục kinh doanh
✅ Bản đồ tuân thủ **ISO/IEC 27001:2022 Annex A** và **PCI DSS v4.0.1**
✅ **Hợp đồng bảo mật tại ranh giới TB-5** — tức các điều kiện mà lõi nền tảng *áp đặt lên* dịch vụ AI và *giả định về* dịch vụ AI

### 2.2. NGOÀI phạm vi — do nhóm chuyên trách AI đảm nhiệm (AI Pipeline Security)

❌ Phòng vệ Prompt Injection (trực tiếp & gián tiếp) trong tầng LLM
❌ Guardrail đầu vào/đầu ra của mô hình, kiểm duyệt nội dung sinh ra
❌ An toàn pipeline RAG: đầu độc chỉ mục vector, rò rỉ ngữ cảnh chéo giữa các tenant trong vector store
❌ Kiểm soát chuỗi công cụ của Agent (tool-use / function-calling authorization)
❌ Chống trích xuất mô hình, đảo ngược embedding, suy luận thành viên (membership inference)
❌ OWASP Top 10 for LLM Applications, NIST AI RMF, ISO/IEC 42001

> **📌 Điểm bàn giao:** Mục **`07 — API & Integration Security §7`** định nghĩa chính xác hợp đồng kỹ thuật tại ranh giới giữa hai vùng: dữ liệu nào được phép đi qua, đã được che mờ tới mức nào, xác thực ra sao, và nền tảng *giả định gì* về hành vi của dịch vụ AI. Nhóm AI cần lấy mục đó làm đầu vào cho tài liệu AI Security của mình.

---

## 3. Khung chuẩn áp dụng (Applied Frameworks)

| Lớp | Chuẩn | Vai trò trong bộ tài liệu |
| :--- | :--- | :--- |
| **Mô hình mối đe dọa** | Microsoft STRIDE + Data Flow Diagram | Xương sống phân tích — tài liệu `03` |
| **Kiểm soát kỹ thuật** | OWASP ASVS 4.0.3 **Level 2** | Checklist verify từng kiểm soát — tài liệu `06` |
| **Lỗ hổng phổ biến** | OWASP Top 10:2021 | Đối chiếu bề mặt tấn công web |
| **Hệ thống quản lý ATTT** | **ISO/IEC 27001:2022 Annex A** (93 controls) | Bản đồ tuân thủ — tài liệu `12` |
| **Chuẩn ngành thanh toán** | **PCI DSS v4.0.1** (12 requirements) | Bản đồ tuân thủ + tuyên bố phạm vi — tài liệu `12` |
| **Định danh lỗ hổng** | CWE / CVSS v3.1 | Xếp hạng rủi ro và SLA vá lỗi |

**Vì sao chọn ASVS L2 chứ không phải L1 hay L3:** ASVS Level 1 chỉ phù hợp cho ứng dụng không xử lý dữ liệu nhạy cảm. Level 3 dành cho hệ thống chịu rủi ro sinh mạng hoặc quốc phòng, chi phí kiểm chứng vượt xa nhu cầu. **Level 2 là mức chuẩn cho ứng dụng xử lý dữ liệu tài chính doanh nghiệp** — đúng hồ sơ rủi ro của Lotus Fin (báo cáo tài chính, số tài khoản ngân hàng, thông tin người đại diện pháp luật).

---

## 4. Mục lục bộ tài liệu

| # | Tài liệu | Nội dung cốt lõi |
| :--- | :--- | :--- |
| `01` | [Kiến trúc hệ thống & Phân vùng tin cậy](01-system-architecture.md) | Stack BE/FE, sơ đồ thành phần, 8 trust boundary, mô hình dữ liệu, bề mặt API |
| `02` | [Kiểm kê tài sản & Phân loại dữ liệu](02-data-classification-assets.md) | Asset inventory, 4 mức phân loại dữ liệu, vòng đời & lưu trữ |
| `03` | [Mô hình mối đe dọa STRIDE](03-threat-model-stride.md) | DFD, danh mục mối đe dọa, xếp hạng rủi ro, giảm thiểu, rủi ro tồn dư |
| `04` | [Định danh & Kiểm soát truy cập](04-identity-access-control.md) | AuthN, MFA, phiên, RBAC matrix, cô lập tenant bằng PostgreSQL RLS |
| `05` | [Bảo vệ dữ liệu & Mật mã](05-data-protection-cryptography.md) | Mã hóa, quản lý khóa envelope, masking, tokenization, xóa dữ liệu |
| `06` | [An toàn ứng dụng — OWASP ASVS L2](06-application-security-owasp.md) | Checklist ASVS cho Go/Next.js, an toàn tải tệp, sandbox parser |
| `07` | [An toàn API & Tích hợp](07-api-integration-security.md) | API security, idempotency, webhook HMAC, Bank API mTLS, **hợp đồng TB-5** |
| `08` | [An toàn hạ tầng & Mạng](08-infrastructure-network-security.md) | Phân vùng mạng, hardening container/K8s, WAF, egress proxy, secrets |
| `09` | [Nhật ký, Kiểm toán & Giám sát](09-logging-audit-monitoring.md) | Audit event catalog, chuỗi băm chống giả mạo, use case phát hiện |
| `10` | [Secure SDLC & Chuỗi cung ứng](10-secure-sdlc-supply-chain.md) | Cổng kiểm soát CI/CD, SAST/SCA/DAST, SBOM, ký ảnh container |
| `11` | [Ứng phó sự cố & Liên tục kinh doanh](11-incident-response-bcdr.md) | Phân loại sự cố, playbook, RTO/RPO, thông báo vi phạm dữ liệu |
| `12` | [Bản đồ tuân thủ ISO 27001 & PCI DSS](12-compliance-iso27001-pcidss.md) | Mapping Annex A + 12 requirement PCI DSS + tuyên bố phạm vi |
| `13` | [Ma trận truy vết yêu cầu bảo mật](13-traceability-matrix.md) | UC001–UC006 → Mối đe dọa → Kiểm soát → Kịch bản kiểm thử |

---

## 5. Nguyên tắc thiết kế xuyên suốt (Guiding Principles)

1. **Secure by Default** — Cấu hình mặc định luôn là cấu hình an toàn nhất. Mọi nới lỏng phải là hành động chủ động, được ghi log và có người chịu trách nhiệm.
2. **Defense in Depth** — Không kiểm soát nào được phép là điểm phòng thủ duy nhất. Phân quyền được thực thi *đồng thời* ở middleware, tầng UseCase và tầng cơ sở dữ liệu (RLS).
3. **Least Privilege** — Mọi chủ thể (người dùng, dịch vụ, tiến trình, kết nối DB) chỉ nhận đúng quyền tối thiểu để hoàn thành nhiệm vụ.
4. **Zero Trust giữa các dịch vụ** — Lưu lượng nội bộ *không* được mặc nhiên tin cậy. Mọi lời gọi giữa các service đều xác thực bằng mTLS và mang danh tính workload.
5. **Assume Breach** — Thiết kế với giả định một thành phần *sẽ* bị xâm phạm. Trọng tâm chuyển sang giới hạn bán kính thiệt hại (blast radius) và khả năng phát hiện.
6. **Deterministic over Probabilistic cho quyết định tài chính** — Mọi con số ảnh hưởng tới quyết định tín dụng (DSCR, Cash Runway, lịch trả nợ) **bắt buộc** do Deterministic Engine tính toán. LLM chỉ được phép *diễn giải* kết quả, **không bao giờ** được phép *tạo ra* chúng. Đây vừa là nguyên tắc chính xác nghiệp vụ, vừa là **kiểm soát bảo mật cốt lõi** — nó vô hiệu hóa toàn bộ lớp tấn công thao túng LLM nhằm bẻ cong hạn mức tín dụng.
7. **Auditability** — Mọi hành động làm thay đổi trạng thái tài chính hoặc truy cập dữ liệu nhạy cảm đều để lại dấu vết bất biến, có thể tái dựng lại dòng thời gian sự việc.

---

## 6. Trạng thái tài liệu & Quy trình cập nhật

| Trường | Giá trị |
| :--- | :--- |
| Chủ sở hữu tài liệu | Security Lead — nhóm Lotus Fin |
| Chu kỳ rà soát | Mỗi Sprint, hoặc ngay khi có thay đổi kiến trúc |
| Điều kiện kích hoạt rà soát bắt buộc | Thêm trust boundary mới · Thêm tích hợp bên thứ ba · Thay đổi mô hình phân quyền · Sau mỗi sự cố bảo mật mức S1/S2 |
| Liên kết ADR | [ADR-001 — Clean Architecture & giới hạn 200 dòng/file](../adr/001-clean-architecture-core-first-adr.md) |
| Liên kết SRS | [SRS Mini — Lotus Fin v1.0](../report/report-1509-kiennt.md) *(đưa lên trong MR riêng)* |
| Liên kết quy chuẩn API | [API Design Conventions](../API_DESIGN_CONVENTIONS.md) |

---

## 7. Ký hiệu dùng trong bộ tài liệu

| Ký hiệu | Ý nghĩa |
| :--- | :--- |
| `TB-n` | Trust Boundary số n (định nghĩa tại `01 §5`) |
| `THR-nnn` | Định danh mối đe dọa (định nghĩa tại `03`) |
| `CTL-nnn` | Định danh kiểm soát bảo mật (tổng hợp tại `13`) |
| `UC00n` | Use Case theo SRS |
| 🔴 `CRITICAL` · 🟠 `HIGH` · 🟡 `MEDIUM` · 🟢 `LOW` | Mức rủi ro theo thang CVSS v3.1 |
