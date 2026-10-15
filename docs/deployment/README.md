# HƯỚNG DẪN TRIỂN KHAI HỆ THỐNG LOTUS FIN LÊN LINUX CLOUD SERVER (END-TO-END)

> **Dự án:** Lotus Fin — SME Financial Management Core with AI Key Report Pipeline  
> **Nền tảng mục tiêu:** Linux Cloud Server / VPS (Ubuntu 22.04 LTS / Debian 12)  
> **Cấu hình phần cứng tối thiểu:** 2 vCPU — 4 GB RAM (Khuyên dùng 8 GB RAM) — 40 GB SSD  
> **Kiến trúc:** Single VM (Host Nginx Reverse Proxy + React SPA + Cụm 9 Container Docker Frappe/ERPNext)  

---

## 📌 MỤC LỤC CHI TIẾT THEO TỪNG BƯỚC TRIỂN KHAI

Bộ tài liệu này đã được module hóa thành **7 bước độc lập, chi tiết và có thể kiểm chứng** từ đầu đến cuối:

| Bước | Tài liệu hướng dẫn chi tiết | Nội dung chính | Trạng thái |
| :---: | :--- | :--- | :---: |
| **Bước 1** | [**`STEP_1_SERVER_SURVEY.md`**](./STEP_1_SERVER_SURVEY.md) | Khảo sát chi tiết hiện trạng CPU, RAM, SSD, cổng dịch vụ, tường lửa và kết nối mạng. | ✅ *Đã hoàn thành* |
| **Bước 2** | [**`STEP_2_OS_HARDENING_AND_DOCKER.md`**](./STEP_2_OS_HARDENING_AND_DOCKER.md) | Kích hoạt 2GB Swap, cài đặt Docker CE & Compose v2, bật xoay vòng log chống tràn ổ đĩa. | ⏳ *Đang tiến hành* |
| **Bước 3** | [**`STEP_3_BACKEND_DEPLOYMENT.md`**](./STEP_3_BACKEND_DEPLOYMENT.md) | Khởi chạy cụm 9 container Frappe/ERPNext, sync app `lotus_fin`, migrate DB và nạp demo data. | 📋 *Sẵn sàng* |
| **Bước 4** | [**`STEP_4_NGINX_AND_SSL_CONFIG.md`**](./STEP_4_NGINX_AND_SSL_CONFIG.md) | Cấu hình Host Nginx làm Reverse Proxy, hỗ trợ WebSocket Copilot, timeout 180s và SSL Let's Encrypt. | 📋 *Sẵn sàng* |
| **Bước 5** | [**`STEP_5_FRONTEND_DEPLOYMENT.md`**](./STEP_5_FRONTEND_DEPLOYMENT.md) | Biên dịch React Frontend (Vite) tại local (1.47s), đóng gói và triển khai lên `/var/www/lotus-fin-fe`. | 📋 *Sẵn sàng* |
| **Bước 6** | [**`STEP_6_TESTING_AND_VERIFICATION.md`**](./STEP_6_TESTING_AND_VERIFICATION.md) | Bộ ma trận 6 kịch bản thử nghiệm: Ping, Desk, AI Copilot API, Suite tests, What-If 9 KPIs, Resource audit. | 📋 *Sẵn sàng* |
| **Bước 7** | [**`STEP_7_CICD_AUTOMATION.md`**](./STEP_7_CICD_AUTOMATION.md) | Thiết lập pipeline GitHub Actions tự động hóa toàn bộ quy trình Deploy trong 30 giây mỗi lần push git. | 📋 *Sẵn sàng* |

---

## 🏗️ SƠ ĐỒ KIẾN TRÚC TỔNG THỂ HỆ THỐNG

```
                                [ Người dùng / Trình duyệt ]
                                             │
                                   HTTP :80 / HTTPS :443
                                             ▼
                        ┌─────────────────────────────────────────┐
                        │       Linux Cloud Server / VPS          │
                        │       (IP: <YOUR_SERVER_IP>)            │
                        │                                         │
                        │   ┌─────────────────────────────────┐   │
                        │   │  Nginx Host (Reverse Proxy)     │   │
                        │   └──────┬────────────────────┬─────┘   │
                        │          │                    │         │
                        │  Tĩnh: / │      API / Desk:   │         │
                        │          ▼      /api, /assets ▼         │
                        │   ┌─────────────┐     ┌───────────────┐ │
                        │   │ React Dist  │     │ Cụm 9 Docker  │ │
                        │   │ (/var/www/  │     │ Containers    │ │
                        │   │ lotus-fin-  │     │ (:8080)       │ │
                        │   │ fe)         │     │ Frappe+MariaDB│ │
                        │   └─────────────┘     └───────────────┘ │
                        └─────────────────────────────────────────┘
```

---

## ⚡ BẢNG TRA CỨU NHANH CÁC LỆNH VẬN HÀNH THƯỜNG DÙNG

Tại thư mục `~/lotus-fin` trên máy chủ:

```bash
# Khởi động cụm container
./run.sh up

# Đồng bộ mã nguồn mới nhất vào container và migrate cơ sở dữ liệu
./run.sh sync

# Nạp dữ liệu mẫu kế toán cho demo
./run.sh demo

# Chạy mô phỏng kịch bản tài chính What-If 9 KPIs
./run.sh simulate

# Chạy bộ test suite tự động
./run.sh test lotus_fin.tests.test_financial_health

# Xem trạng thái tiêu hao tài nguyên thực tế
docker stats --no-stream

# Dọn dẹp cache rác bảo toàn dung lượng ổ cứng
docker system prune -f
```

---

*Hồ sơ tài liệu chuẩn được lưu trữ trong thư mục `docs/deployment/` của kho mã nguồn Lotus Fin.*
