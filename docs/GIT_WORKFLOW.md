# 🔀 Git Workflow & Governance — Lotus-Fin

> **Nhánh chính:** `main` (Production) · `staging` (Pre-production) · `develop` (Integration Testing)  
> **Áp dụng cho:** Hệ sinh thái FinTech Lotus-Fin  

---

## 1. SƠ ĐỒ TỔNG QUAN LUỒNG NHÁNH

```
  main (Production — Code ổn định nhất)
    │
    ├──────────────────── staging (Pre-production / UAT Test lần cuối)
    │                       ▲
    │                       │ merge khi test done
    │                       │
    └──────────────────── develop (Integration Testing)
                            ▲
                            │ merge để test tích hợp
                            │
                    ┌───────┴───────┐
                    │               │
                feature/         fix/
              vietqr-webhook    paypal-calc
```

**Luồng code đi theo 1 chiều duy nhất:**
```
feature branch → develop (test tích hợp) → feature branch → staging (UAT) → main (Production)
```

---

## 2. MÔ TẢ CÁC NHÁNH & NGUYÊN TẮC BẢO VỆ

| Nhánh | Mục đích | Checkout từ | Merge vào | Deploy tới |
| :--- | :--- | :--- | :--- | :--- |
| **`main`** | Production — Code ổn định nhất | — | Chỉ từ `staging` | Production Server |
| **`staging`** | Pre-production — Kiểm thử UAT | `main` | Từ feature/fix (đã test pass) | Staging Environment |
| **`develop`** | Testing — Tích hợp tính năng mới | `main` | Từ feature branches | Dev / Local Server |
| **`feature/*`** | Phát triển tính năng mới | `staging` | `develop` $\rightarrow$ test done $\rightarrow$ `staging` | Local |
| **`fix/*`** | Sửa lỗi | `staging` | `develop` $\rightarrow$ test done $\rightarrow$ `staging` | Local |
| **`hotfix/*`** | Sửa lỗi khẩn cấp production | `main` | Trực tiếp vào `staging` $\rightarrow$ `main` | Hotfix Deploy |

### ⚠️ Quy tắc bảo vệ nhánh:
1. **CẤM PUSH TRỰC TIẾP** vào `main`, `staging`, `develop`.
2. **PULL CODE MỚI NHẤT DUY NHẤT TỪ `staging`**.

---

## 3. QUY CHUẨN ĐẶT TÊN NHÁNH & COMMIT

### Đặt tên nhánh:
```
feature/<tên-dev>/<tên-task>    # Ví dụ: feature/kien/vietqr-webhook-handler
fix/<tên-dev>/<tên-bug>         # Ví dụ: fix/kien/paypal-ipn-signature
refactor/<tên-dev>/<mô-tả>      # Ví dụ: refactor/kien/clean-arch-payment-usecase
```

### Commit Message chuẩn Conventional Commits:
```
feat(payment): add dynamic VietQR generation with CRC checksum
fix(paypal): resolve IPN webhook signature verification mismatch
refactor(ledger): split balance mutation into modular usecases (<200 lines)
test(harness): add E2E payment settlement test suite
```

