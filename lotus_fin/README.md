# Lotus Fin

**Lotus Fin** là một Custom App được xây dựng theo chuẩn **Frappe Framework**, chạy trên nền tảng ERPNext nhằm cung cấp giải pháp **Quản trị Tài chính, Mua bán, Kho, Tài sản tinh gọn cho doanh nghiệp vừa và nhỏ (SME)**, đồng thời tích hợp **AI Key Report Pipeline** để nạp dữ liệu cho các mô hình AI dự báo và phân tích.

---

## 🎯 Phạm vi các Phân hệ (Scope)

- ✅ **Accounting (Kế toán - Tài chính)**: Sổ cái (`General Ledger`), Báo cáo Lỗ/Lãi (`Profit and Loss`), Báo cáo Lưu chuyển tiền tệ (`Cash Flow`), Quản lý Thu/Chi (`Payment Entry`), Hóa đơn mua/bán, Đối soát ngân hàng.
- ✅ **Selling (Bán hàng)**: Khách hàng (`Customer`), Báo giá (`Quotation`), Đơn hàng (`Sales Order`), Điểm bán lẻ (`Point of Sale`), Danh mục sản phẩm & Bảng giá (`Item & Pricing`).
- ✅ **Buying (Mua hàng)**: Nhà cung cấp (`Supplier`), Đơn mua hàng (`Purchase Order`), Hóa đơn mua hàng (`Purchase Invoice`), Theo dõi công nợ nhà cung cấp.
- ✅ **Assets (Tài sản)**: Quản lý tài sản cố định, tự động trích khấu hao (`Asset Depreciation`), lịch bảo trì.
- ✅ **Subcontracting (Gia công)**: Theo dõi nghiệp vụ gia công trong và ngoài (`Inward / Outward Subcontracting`).
- ✅ **Settings & Organization**: Thiết lập công ty, đa tiền tệ (VND/USD), năm tài chính, phân quyền người dùng.
- 🚫 **Ẩn các module không cần thiết**: `Manufacturing`, `Quality`, `Healthcare`, `Agriculture`, `Education`... giúp hệ thống siêu nhẹ và tập trung.

---

## 🤖 AI Key Report Data Pipeline

Module `lotus_fin.api.key_reports` cung cấp các API để trích xuất dữ liệu sạch từ các báo cáo cốt lõi của ERPNext:

- `General Ledger` -> Dữ liệu dòng tiền, phát sinh Nợ/Có.
- `Accounts Receivable / Payable` -> Dữ liệu tuổi nợ, lịch sử thanh toán, rủi ro tín dụng.
- `Profit and Loss Statement` -> Doanh thu, chi phí, lợi nhuận thực tế.
- `Sales & Purchase Analytics` -> Xu hướng mua bán theo mùa vụ và đối tác.

---

## 🚀 Cài đặt vào Frappe Bench

```bash
# 1. Đặt thư mục lotus_fin vào apps/
cd /home/frappe/frappe-bench/apps

# 2. Cài đặt app vào môi trường Python
../env/bin/pip install -e lotus_fin

# 3. Cài đặt app vào site hiện tại
bench --site [ten_site] install-app lotus_fin

# 4. Chạy migrate để cập nhật cấu hình
bench --site [ten_site] migrate
```

