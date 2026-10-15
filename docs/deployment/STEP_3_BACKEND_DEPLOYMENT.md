# BƯỚC 3: TRIỂN KHAI CỤM FRAPPE / ERPNEXT BACKEND DOCKER

> **Giai đoạn:** Bước 3 / 7 trong quy trình triển khai Lotus Fin  
> **Mục tiêu:** Kéo mã nguồn, khởi chạy 9 container dịch vụ của Frappe v16 & ERPNext, cài đặt app `lotus_fin`, migrate cơ sở dữ liệu MariaDB 11.8 và nạp dữ liệu mẫu kế toán doanh nghiệp.  
> **Điều kiện tiên quyết:** Đã hoàn thành [Bước 2: Chuẩn bị môi trường OS & Docker](./STEP_2_OS_HARDENING_AND_DOCKER.md).  

---

## 1. TỔNG QUAN CỤM 9 CONTAINER DỊCH VỤ

Hệ thống backend sử dụng kiến trúc chuẩn của Frappe Framework v16 đóng gói trong Docker Compose (`frappe_docker/pwd.yml`):

```
                                  [ Cổng 8080 ]
                                        │
                                        ▼
                         ┌─────────────────────────────┐
                         │  frappe_docker-frontend-1   │
                         │  (Nginx nội bộ của Frappe)  │
                         └──────────────┬──────────────┘
                                        │
                 ┌──────────────────────┼──────────────────────┐
                 ▼                      ▼                      ▼
        ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
        │     backend     │    │    websocket    │    │       db        │
        │(Gunicorn PyApp) │    │  (SocketIO Real)│    │ (MariaDB 11.8)  │
        └────────┬────────┘    └─────────────────┘    └─────────────────┘
                 │
                 ├──────────────────────────────┐
                 ▼                              ▼
        ┌─────────────────┐            ┌─────────────────┐
        │   queue-short   │            │   queue-long    │
        │ (Worker nhanh)  │            │ (Worker dài hạn)│
        └────────┬────────┘            └────────┬────────┘
                 │                              │
                 ▼                              ▼
        ┌─────────────────┐            ┌─────────────────┐
        │   redis-queue   │            │   redis-cache   │
        │(Hàng đợi Redis) │            │ (Cache hệ thống)│
        └─────────────────┘            └─────────────────┘
                 ▲
                 │
        ┌─────────────────┐
        │    scheduler    │
        │ (Cronjob Frappe)│
        └─────────────────┘
```

---

## 2. QUY TRÌNH TRIỂN KHAI CHI TIẾT

Đăng nhập vào máy chủ qua SSH: `ssh root@<YOUR_SERVER_IP>`.

### 2.1. Kéo mã nguồn dự án Lotus Fin
```bash
cd ~
git clone https://github.com/trungkienit25/lotus-fin.git ~/lotus-fin
cd ~/lotus-fin

# Cấp quyền thực thi cho script điều khiển
chmod +x run.sh
```

---

### 2.2. Khởi động 9 Container dịch vụ
Chạy lệnh khởi động:
```bash
./run.sh up
```

*Cơ chế hoạt động bên dưới của lệnh này:*
1. Tự động kiểm tra và clone thư mục cấu hình `frappe_docker`.
2. Tải các Docker Images chính thức:
   * `frappe/erpnext:v16.36.1` (~2.89 GB)
   * `mariadb:11.8` (~329 MB)
   * `redis:6.2-alpine` (~28 MB)
3. Chạy container `create-site` để tạo site tên là `frontend` với tài khoản mặc định `Administrator / admin`.
4. Khởi động toàn bộ 9 container dịch vụ.

⏳ *Thời gian chạy lần đầu:* Khoảng **2 – 3 phút** (tùy thuộc tốc độ mạng kéo image).

---

### 2.3. Kiểm tra trạng thái các Container
Chạy lệnh kiểm tra danh sách container đang chạy:
```bash
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
```

👉 **Bảng đối chiếu trạng thái đạt chuẩn (9/9 Containers):**

| Tên Container | Trạng thái yêu cầu | Cổng kết nối | Chức năng |
| :--- | :---: | :---: | :--- |
| `frappe_docker-frontend-1` | `Up ...` | `0.0.0.0:8080->8080/tcp` | Cổng tiếp nhận chính của Frappe |
| `frappe_docker-backend-1` | `Up ...` | Internal | Máy chủ ứng dụng Python Gunicorn |
| `frappe_docker-db-1` | `Up ... (healthy)` | `3306/tcp` | Cơ sở dữ liệu MariaDB |
| `frappe_docker-websocket-1`| `Up ...` | Internal | Xử lý sự kiện thời gian thực Socket.io |
| `frappe_docker-queue-short-1`| `Up ...` | Internal | Xử lý tác vụ nền ngắn hạn (Email, Event) |
| `frappe_docker-queue-long-1` | `Up ...` | Internal | Xử lý tác vụ nền nặng (Báo cáo, Snapshot) |
| `frappe_docker-scheduler-1` | `Up ...` | Internal | Điều phối cron job tự động |
| `frappe_docker-redis-queue-1`| `Up ...` | `6379/tcp` | Hàng đợi Celery / RQ |
| `frappe_docker-redis-cache-1`| `Up ...` | `6379/tcp` | Bộ nhớ đệm Redis Cache |

---

### 2.4. Đồng bộ ứng dụng Lotus Fin & Migrate Database
Sau khi 9 container đã chạy ổn định, chạy lệnh đồng bộ mã nguồn Lotus Fin:
```bash
./run.sh sync
```

*Lệnh này sẽ tự động thực hiện tuần tự:*
1. Copy mã nguồn `lotus_fin` mới nhất vào `/home/frappe/frappe-bench/apps/lotus_fin` bên trong container.
2. Cài đặt app `lotus_fin` vào môi trường Python của container (`pip install -e`).
3. Chạy migration lược đồ cơ sở dữ liệu (`bench --site frontend migrate`) để tạo các DocTypes, Custom Fields và Fixtures của Lotus Fin.
4. Xóa cache và khởi động lại container `frappe_docker-backend-1` để nạp code mới.

👉 *Kỳ vọng hoàn thành:* Dòng thông báo `[OK] Synced source code, built assets, migrated DB, and reloaded successfully!`.

---

### 2.5. Nạp bộ dữ liệu mẫu (Demo Dataset)
Để các phân hệ AI (AI001 đến AI006) có sẵn dữ liệu hóa đơn, công nợ và dòng tiền để phân tích và demo:
```bash
./run.sh demo
```

*Kết quả tạo ra:*
* Doanh nghiệp mẫu: `Lotus-fin (Demo)`.
* Hệ thống tài khoản kế toán, bảng cân đối kế toán mẫu.
* Tập hợp hóa đơn bán hàng (`Sales Invoice`), phiếu thanh toán (`Payment Entry`) và công nợ phải thu (`AR Overdue`).
* Cấu hình phân hệ Copilot: `http://localhost:8080/desk/financial-health`.

---

## 3. CHECKLIST NGHIỆM THU BƯỚC 3

- [ ] Lệnh `docker ps` hiển thị đầy đủ 9 container có tiền tố `frappe_docker-`.
- [ ] Container `frappe_docker-db-1` có nhãn `(healthy)`.
- [ ] Lệnh `curl -I http://127.0.0.1:8080/api/method/ping` trả về `HTTP/1.1 200 OK` (pong).
- [ ] Lệnh `docker stats --no-stream` ghi nhận tổng RAM của 9 container dao động trong khoảng **750 MB – 1.1 GB** (dư dả RAM trên máy).

---

👉 **Chuyển sang:** [BƯỚC 4: CẤU HÌNH NGINX REVERSE PROXY & SSL HTTPS](./STEP_4_NGINX_AND_SSL_CONFIG.md)
