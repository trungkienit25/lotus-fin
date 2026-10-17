# 🌿 Lotus Fin — Operations & Deployment Manual (Run Scripts Guide)

Hướng dẫn toàn diện về cấu trúc kịch bản vận hành, kiểm thử môi trường, đóng gói container và triển khai ứng dụng 1-click lên Cloud Server.

---

## 📁 Cấu trúc Thư mục Kịch bản (`/scripts`)

```
scripts/
├── deploy/                 # Kịch bản triển khai tự động lên Cloud / Web Server
│   └── run-deploy.sh       # 🚀 Pipeline 1-click: kiểm tra môi trường, nạp DB seed, deploy port 80
├── dev/                    # Kịch bản dành cho Developer khi phát triển cục bộ
│   ├── run-dev.sh          # Linux / macOS / WSL: Tự động cài đặt & mở Vite dev server (port 5173)
│   └── run-dev.ps1         # Windows PowerShell: Tự động khởi động dev stack
├── packaging/              # Kịch bản đóng gói container images chuẩn production
│   └── run-packaging.sh    # Build multi-stage image lotus-fin/gateway (React SPA + Nginx)
├── container/              # Quản lý vòng đời container production
│   └── run-container.sh    # Start, stop, restart, logs, status trên port 80
└── data/                   # Dữ liệu dự phòng & snapshot phục vụ di chuyển máy chủ
    └── database/           
        └── initial_db_seed.sql.gz  # Snapshot toàn bộ CSDL và sổ cái kế toán để mang lên server
```

---

## 🚀 1. Triển khai 1-Click lên Cloud Server (`run-deploy.sh`)

Khi bạn mua VPS mới (Ubuntu 22.04 / 24.04, Debian, AWS EC2, DigitalOcean) và clone dự án về, bạn chỉ cần chạy **duy nhất 1 script**:

```bash
chmod +x run.sh scripts/*/*.sh
./run.sh deploy
# hoặc chạy trực tiếp:
./scripts/deploy/run-deploy.sh
```

### Quy trình tự động 7 bước của `run-deploy.sh`:
1. **Kiểm tra tài nguyên:** Kiểm tra RAM, CPU; tự động tạo **2GB Swapfile** nếu máy chủ là VPS cấu hình thấp để Frappe không bị OOM (Out Of Memory).
2. **Kiểm tra & Cài đặt Docker:** Tự động cài Docker Engine và Docker Compose plugin chính thức nếu server chưa có.
3. **Cấu hình môi trường:** Tự động tạo và kiểm tra `docker/production/.env.production`.
4. **Đóng gói Gateway:** Tự động build image `lotus-fin/gateway:latest` tích hợp Nginx Reverse Proxy và mã nguồn Frontend React SPA.
5. **Khởi chạy container:** Chạy cụm multi-container production xuất trực tiếp ra **Port 80**.
6. **Tự động Hydrate Database:**
   - Tự động nạp file snapshot CSDL [`scripts/data/database/initial_db_seed.sql.gz`](file:///d:/Coding/lotus-fin/scripts/data/database/initial_db_seed.sql.gz) lên site `frontend`.
   - Chạy `bench migrate` để đồng bộ cấu trúc DocType.
   - Nạp cấu hình SMTP Email Account mặc định và dữ liệu kế toán mẫu (`Lotus-fin Demo`).
7. **Kiểm tra nghiệm thu (Readiness Audit):** Kiểm tra HTTP ping; in ra địa chỉ IP công khai của server để truy cập ngay.

---

## 💻 2. Dành cho Developer (`run-dev.sh` / `run-dev.ps1`)

Khi bạn hoặc đồng đội clone repo về máy local để code:

### Trên Linux / macOS / WSL / Git Bash:
```bash
./run.sh dev
# hoặc:
./scripts/dev/run-dev.sh
```

### Trên Windows PowerShell:
```powershell
.\scripts\dev\run-dev.ps1
```

- Hệ thống sẽ tự nhận diện OS, nạp các container nền (MariaDB, Redis, Frappe Backend), đồng bộ module `lotus_fin` và khởi chạy Vite Dev Server tại `http://localhost:5173`.

---

## 📦 3. Đóng gói Container Production (`run-packaging.sh`)

Để đóng gói lại container trước khi release hoặc khi có cập nhật giao diện frontend mới:

```bash
./run.sh packaging
# hoặc:
./scripts/packaging/run-packaging.sh
```

- Image `lotus-fin/gateway:latest` sẽ được build với Multi-stage Dockerfile:
  - Stage 1: Build React/TypeScript bằng `node:20-alpine`.
  - Stage 2: Copy file tĩnh vào `nginx:alpine` kèm file cấu hình reverse-proxy tối ưu.

---

## 🐳 4. Điều khiển Container Production (`run-container.sh`)

```bash
./scripts/container/run-container.sh start    # Bật toàn bộ cụm container (Port 80)
./scripts/container/run-container.sh status   # Xem trạng thái các container
./scripts/container/run-container.sh logs     # Xem log realtime
./scripts/container/run-container.sh restart  # Khởi động lại
./scripts/container/run-container.sh stop     # Tắt cụm container
```

---

## 🌐 5. Cấu hình Nginx & Cổng Port 80

Dự án sử dụng Nginx Gateway làm cổng vào duy nhất tại `Port 80`:
- **Đường dẫn `/`:** Phục vụ ứng dụng React SPA (TailAdmin/Lotus Copilot).
- **Đường dẫn `/api`, `/desk`, `/assets`, `/socket.io`:** Proxy trực tiếp tới backend Frappe/ERPNext (`frappe-frontend:8080`).
- Người dùng cuối và nhân viên tài chính chỉ cần truy cập vào `http://<IP-SERVER>/` mà không cần nhập thêm cổng `:8080` hay cấu hình domain phức tạp.
