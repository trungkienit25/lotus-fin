# KẾ HOẠCH TRIỂN KHAI END-TO-END: LOTUS FIN TRÊN LINUX CLOUD SERVER

> **Tài liệu:** End-to-End Cloud Deployment & Verification Plan  
> **Dự án:** Lotus Fin — SME Financial Management Core with AI Key Report Pipeline  
> **Môi trường mục tiêu:** Linux Cloud Server / VPS (Ubuntu 22.04 LTS / 2 vCPU / 8 GB RAM / 40 GB SSD)  
> **Phiên bản tài liệu:** v1.0 — Tháng 10/2026  

---

## 1. TỔNG QUAN KIẾN TRÚC & MỤC TIÊU TRIỂN KHAI

### 1.1. Mô hình kiến trúc đơn máy chủ (Single VM Architecture)
Hệ thống được thiết kế chạy trọn gói trên **1 máy chủ ảo Compute duy nhất** (không phát sinh chi phí Cloud Load Balancer riêng):

```
                                [ Người dùng / Trình duyệt ]
                                             │
                                   HTTP :80 / HTTPS :443
                                             ▼
                        ┌─────────────────────────────────────────┐
                        │        Linux Cloud Server / VPS         │
                        │         (IP: <YOUR_SERVER_IP>)          │
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

### 1.2. Mục tiêu triển khai
1. Khảo sát chi tiết hiện trạng cấu hình phần cứng, mạng và phần mềm của máy chủ.
2. Thiết lập môi trường nền tảng an toàn (Swap, Docker, Nginx, Log Rotation).
3. Triển khai cụm backend 9 containers (Frappe v16, ERPNext, MariaDB 11.8, Redis, Workers).
4. Đồng bộ ứng dụng `lotus_fin` và nạp dữ liệu mẫu kế toán doanh nghiệp.
5. Cấu hình Nginx phục vụ giao diện React Frontend và proxy API liền mạch.
6. Thực hiện bộ kiểm thử end-to-end (Unit test, What-If simulation, AI Copilot API).
7. Tự động hóa quy trình cập nhật liên tục (CI/CD) qua GitHub Actions.

---

## 2. GIAI ĐOẠN 1: KHẢO SÁT & ĐÁNH GIÁ HIỆN TRẠNG CLOUD SERVER

Trước khi cài đặt bất kỳ thành phần nào, tiến hành khảo sát máy chủ từ xa qua SSH:

### 2.1. Lệnh khảo sát tổng thể (All-in-one Diagnostic Script)
Chạy script chẩn đoán trên máy chủ:

```bash
cat << 'EOF' > /tmp/server_survey.sh
#!/usr/bin/env bash
echo "=========================================================="
echo "          LOTUS FIN - BÁO CÁO KHẢO SÁT HỆ THỐNG          "
echo "=========================================================="

echo -e "\n[1] THÔNG TIN HỆ ĐIỀU HÀNH & KERNEL"
echo "Hostname: $(hostname)"
echo "Kernel: $(uname -r)"
echo "OS: $(lsb_release -ds 2>/dev/null || cat /etc/os-release | grep PRETTY_NAME | cut -d= -f2)"

echo -e "\n[2] TÀI NGUYÊN PHẦN CỨNG (CPU / RAM / DISK)"
echo "CPU Cores: $(nproc)"
echo "RAM:"
free -h
echo "Ổ cứng (Disk):"
df -h /

echo -e "\n[3] PHẦN MỀM CƠ BẢN"
echo "Git: $(git --version 2>/dev/null || echo 'CHƯA CÀI')"
echo "Docker: $(docker -v 2>/dev/null || echo 'CHƯA CÀI')"
echo "Docker Compose: $(docker compose version 2>/dev/null || echo 'CHƯA CÀI')"
echo "Nginx: $(nginx -v 2>&1 || echo 'CHƯA CÀI')"

echo -e "\n[4] CÁC CỔNG MẠNG ĐANG CHIẾM DỤNG (80, 443, 8080, 3306, 6379)"
ss -tulpn | grep -E ':80|:443|:8080|:3306|:6379' || echo "-> Tất cả các cổng đều đang rảnh."

echo -e "\n[5] TƯỜNG LỬA NỘI BỘ (UFW)"
ufw status

echo -e "\n[6] KẾT NỐI INTERNET RA NGOÀI (GITHUB / DOCKER HUB)"
echo -n "GitHub ping: "
curl -Is --connect-timeout 5 https://github.com | head -n 1
echo -n "Docker Hub ping: "
curl -Is --connect-timeout 5 https://registry-1.docker.io/v2/ | head -n 1

echo "=========================================================="
EOF
chmod +x /tmp/server_survey.sh
/tmp/server_survey.sh
```

### 2.2. Bảng đối chiếu kết quả khảo sát thực tế (Baseline Audit Checklist)

| Tiêu chí khảo sát | Lệnh kiểm tra thủ công | Tiêu chuẩn Lotus Fin | Khuyến nghị hành động |
| :--- | :--- | :--- | :--- |
| **CPU Cores** | `nproc` | Tối thiểu 2 vCPU | Đảm bảo $\ge$ 2 Core để xử lý đa nhiệm |
| **RAM vật lý** | `free -m` | Tối thiểu 4 GB, khuyên dùng 8 GB | Chạy 9 container cần ~1.2 GB RAM |
| **Dung lượng SSD** | `df -h /` | Tối thiểu 20 GB, khuyên dùng 40 GB | Đảm bảo dung lượng trống $\ge$ 15 GB |
| **Swap Space** | `swapon --show` | Bắt buộc $\ge$ 2 GB | Nếu chưa có (0B), tạo ở Bước 2 |
| **Hệ điều hành** | `lsb_release -a` | Ubuntu 22.04 LTS x86_64 / Debian 12 | Bản phân phối chuẩn tương thích Docker |
| **Cổng 80 (HTTP)** | `ss -tulpn \| grep :80` | Nginx Host đón tiếp | Cấu hình làm Reverse Proxy ở Bước 4 |
| **Cổng 8080 (Frappe)**| `ss -tulpn \| grep :8080`| Cần rảnh cho container | Tránh xung đột cổng |
| **Cổng 3306 (DB)** | `ss -tulpn \| grep :3306`| Cần rảnh cho MariaDB container | Chạy độc lập trong Docker |
| **Docker Engine** | `docker -v` | Phiên bản 24.x trở lên | Cài đặt bản chính thức ở Bước 2 |
| **Docker Compose** | `docker compose version`| Compose Plugin v2 | Cài đặt plugin ở Bước 2 |
| **Git CLI** | `git --version` | Git 2.25+ | Dùng để clone và pull mã nguồn |
| **Tường lửa UFW** | `ufw status` | Không chặn cổng 22, 80, 443 | Kiểm tra Security Group của Cloud Provider |
| **GitHub Access** | `curl -Is https://github.com` | `HTTP/2 200` | Đảm bảo server kết nối Internet |
| **Docker Hub** | `curl -Is https://registry-1.docker.io/v2/` | `HTTP/2 401` *(chuẩn unauth)*| Sẵn sàng kéo image container |

---

## 3. GIAI ĐOẠN 2: CHUẨN BỊ & TỐI ƯU MÔI TRƯỜNG OS (OS HARDENING)

### 3.1. Tạo 2GB Swap Memory
Dù máy chủ có 8GB RAM, việc kích hoạt 2GB Swap với độ ưu tiên swap thấp (`swappiness=10`) là bắt buộc để triệt tiêu nguy cơ tiến trình MariaDB/Gunicorn bị Linux OOM Killer tắt ngang khi có đỉnh tải đột biến:

```bash
# Tạo file swap 2GB
fallocate -l 2G /swapfile
chmod 600 /swapfile
mkswap /swapfile
swapon /swapfile

# Cấu hình tự động kích hoạt khi reboot
echo '/swapfile none swap sw 0 0' >> /etc/fstab

# Tối ưu swappiness (chỉ dùng swap khi RAM thực tế còn dưới 10%)
sysctl vm.swappiness=10
echo 'vm.swappiness=10' >> /etc/sysctl.conf
```

### 3.2. Cài đặt Docker Engine & Docker Compose chính thức
```bash
apt update
apt install -y ca-certificates curl gnupg lsb-release

# Thêm GPG key chính thức của Docker
mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg

echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null

# Cài đặt Docker CE & Compose plugin
apt update
apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Cấu hình Docker tự khởi động cùng OS
systemctl enable docker
systemctl start docker
```

### 3.3. Cấu hình xoay vòng log (Chống tràn ổ cứng SSD)
Mặc định Docker lưu trữ log không giới hạn. Bắt buộc giới hạn 10MB/file:

```bash
cat > /etc/docker/daemon.json <<EOF
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}
EOF
systemctl restart docker
```

### 3.4. Chuẩn bị thư mục chứa mã nguồn & Web tĩnh
```bash
mkdir -p /var/www/lotus-fin-fe
mkdir -p ~/lotus-fin
```

---

## 4. GIAI ĐOẠN 3: TRIỂN KHAI CỤM FRAPPE BACKEND (DOCKER COMPOSE)

### 4.1. Kéo mã nguồn & Cụm Frappe Docker
```bash
cd ~
git clone https://github.com/trungkienit25/lotus-fin.git ~/lotus-fin
cd ~/lotus-fin

# Cấp quyền thực thi script điều khiển
chmod +x run.sh
```

### 4.2. Khởi tạo 9 Container Dịch vụ
Chạy lệnh khởi tạo ban đầu:
```bash
./run.sh up
```
*Lưu ý:* Ở lần chạy đầu tiên, Docker sẽ tải các images (`frappe/erpnext:v16.36.1`, `mariadb:11.8`, `redis:6.2-alpine`) và tạo cơ sở dữ liệu `frontend`. Quá trình này mất khoảng 2 – 3 phút.

Kiểm tra trạng thái các container:
```bash
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
```
*Đảm bảo 9/9 containers đều ở trạng thái `Up`:*
1. `frappe_docker-frontend-1` (:8080)
2. `frappe_docker-backend-1`
3. `frappe_docker-db-1` (healthy)
4. `frappe_docker-redis-cache-1`
5. `frappe_docker-redis-queue-1`
6. `frappe_docker-queue-short-1`
7. `frappe_docker-queue-long-1`
8. `frappe_docker-scheduler-1`
9. `frappe_docker-websocket-1`

### 4.3. Đồng bộ ứng dụng Lotus Fin & Migrate Database
```bash
./run.sh sync
```
Lệnh trên thực hiện:
* Đồng bộ code `lotus_fin` vào thư mục bench trong container.
* Cài đặt app `lotus_fin` vào site `frontend`.
* Chạy migration lược đồ cơ sở dữ liệu (`bench --site frontend migrate`).
* Xóa sạch cache hệ thống (`clear-cache`).
* Nạp cấu hình demo chuẩn.

### 4.4. Nạp bộ dữ liệu mẫu tài chính kế toán
```bash
./run.sh demo
```
Tạo sẵn tài khoản doanh nghiệp mẫu (`Lotus-fin (Demo)`), các năm tài chính, hóa đơn và dữ liệu phục vụ các module AI001 – AI006.

---

## 5. GIAI ĐOẠN 4: CẤU HÌNH NGINX REVERSE PROXY & SSL

### 5.1. Tạo cấu hình Virtual Host Nginx
Tạo file cấu hình `/etc/nginx/sites-available/lotusfin`:

```bash
cat > /etc/nginx/sites-available/lotusfin << 'EOF'
server {
    listen 80;
    server_name _; # Điền tên miền nếu có (ví dụ: demo.lotusfin.vn)

    client_max_body_size 50m;

    # 1. Phục vụ giao diện React Frontend tĩnh
    location / {
        root /var/www/lotus-fin-fe;
        index index.html;
        try_files $uri $uri/ /index.html;
    }

    # 2. Reverse Proxy API, SocketIO và Desk về Frappe Backend Docker (:8080)
    location ~ ^/(api|assets|files|socket.io|app|desk)/ {
        proxy_pass http://127.0.0.1:8080;
        proxy_http_version 1.1;

        # Hỗ trợ kết nối thời gian thực WebSocket cho Copilot & Desk
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";

        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Tăng timeout cho các báo cáo tài chính lớn và kịch bản stress-test
        proxy_connect_timeout 60s;
        proxy_send_timeout 180s;
        proxy_read_timeout 180s;

        # Tắt đệm proxy để phản hồi dạng Stream của AI không bị trễ
        proxy_buffering off;
    }
}
EOF
```

### 5.2. Kích hoạt Virtual Host & Reload Nginx
```bash
rm -f /etc/nginx/sites-enabled/default
ln -sf /etc/nginx/sites-available/lotusfin /etc/nginx/sites-enabled/
nginx -t && systemctl reload nginx
```

### 5.3. (Tùy chọn) Kích hoạt HTTPS với Certbot Let's Encrypt
Nếu có trỏ tên miền:
```bash
apt install -y certbot python3-certbot-nginx
certbot --nginx -d demo.lotusfin.vn
```

---

## 6. GIAI ĐOẠN 5: TRIỂN KHAI FRONTEND REACT (TAILADMIN)

Do Frontend build chỉ mất **1.47 giây** và sinh ra gói `dist` **< 1 MB**, phương án tối ưu nhất là build tại máy local (hoặc GitHub Actions) rồi rsync/scp lên server:

### 6.1. Build tại máy phát triển (Local Machine)
Tại thư mục `d:\Coding\lotus-fin\frontend`:
```bash
npm run build
tar -czf dist.tar.gz -C dist .
```

### 6.2. Đẩy file lên Cloud Server và giải nén
Từ máy local:
```powershell
scp -P 22 .\dist.tar.gz root@<YOUR_SERVER_IP>:/tmp/
```

Trên Cloud Server:
```bash
rm -rf /var/www/lotus-fin-fe/*
tar -xzf /tmp/dist.tar.gz -C /var/www/lotus-fin-fe/
rm -f /tmp/dist.tar.gz
```

---

## 7. GIAI ĐOẠN 6: KẾ HOẠCH THỬ NGHIỆM & ĐỐI SOÁT (VERIFICATION MATRIX)

Sau khi hoàn tất cài đặt, tiến hành chạy toàn bộ 6 kịch bản thử nghiệm:

```
[Kịch bản 1: Network & Ping]  ──>  [Kịch bản 2: Desk Login]  ──>  [Kịch bản 3: AI Copilot API]
                                                                          │
[Kịch bản 6: Resource Audit]  <──  [Kịch bản 5: Stress Test] <──  [Kịch bản 4: Suite Test]
```

### Kịch bản 1: Kiểm tra kết nối HTTP/HTTPS
* **Lệnh:**
  ```bash
  curl -I http://127.0.0.1/
  curl -I http://127.0.0.1/api/method/ping
  ```
* **Kỳ vọng:** Trả về `HTTP/1.1 200 OK` (pong).

### Kịch bản 2: Đăng nhập giao diện Frappe Desk
* **URL:** `http://<YOUR_SERVER_IP>/desk/financial-health`
* **Tài khoản:** `Administrator` / `admin`
* **Kỳ vọng:** Đăng nhập thành công, bảng điều khiển Financial Health hiển thị các biểu đồ KPI doanh thu, chi phí, dòng tiền.

### Kịch bản 3: Kiểm tra API AI Copilot Endpoint
* **Lệnh kiểm tra từ dòng lệnh:**
  ```bash
  curl -s -X POST "http://127.0.0.1:8080/api/method/lotus_fin.api.copilot_api.chat_copilot" \
       -H "Content-Type: application/json" \
       -d '{"query": "sức khỏe tài chính", "company": "Lotus-fin (Demo)"}'
  ```
* **Kỳ vọng:** JSON trả về phân tích chỉ số tài chính, khuyến nghị và dữ liệu widget cấu trúc (status 200).

### Kịch bản 4: Chạy bộ kiểm thử tự động tài chính (Integration Tests)
* **Lệnh:**
  ```bash
  cd ~/lotus-fin
  ./run.sh test lotus_fin.tests.test_financial_health
  ```
* **Kỳ vọng:** `Ran 15 tests ... OK` trong thời gian $< 0.5$ giây.

### Kịch bản 5: Chạy mô phỏng kịch bản sốc tài chính What-If (AI004)
* **Lệnh:**
  ```bash
  ./run.sh simulate
  ```
* **Kỳ vọng:** Trả về đủ ma trận 9 lớp chỉ số KPI (`revenue`, `gross_margin`, `ar_outstanding`, `dso`, `net_cash_flow`, `ending_cash`, `ccc`, `cash_shortfall`).

### Kịch bản 6: Đo lường tải tài nguyên sau kiểm thử (Resource Audit)
* **Lệnh:**
  ```bash
  docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}"
  ```
* **Kỳ vọng:**
  * Tổng RAM 9 container $\le$ 1.5 GB.
  * RAM máy chủ còn rảnh $\ge$ 5.5 GB.
  * CPU rảnh $\ge$ 95%.

---

## 8. GIAI ĐOẠN 7: TỰ ĐỘNG HÓA CI/CD TỪ GITHUB ACTIONS

Thiết lập file workflow `.github/workflows/deploy.yml` để mỗi khi merge code vào nhánh `main` hoặc `develop`, hệ thống tự động build Frontend và sync Backend:

### 8.1. Các Secret cần cấu hình trên GitHub Repo
Vào **Settings** -> **Secrets and variables** -> **Actions** -> **New repository secret**:
* `VM_HOST`: `<YOUR_SERVER_IP>`
* `VM_USERNAME`: `root`
* `VM_SSH_KEY`: Private Key SSH dùng để kết nối vào máy chủ.
* `VM_PORT`: `22`

### 8.2. Cấu trúc Pipeline CI/CD
```yaml
name: Deploy Lotus Fin to Cloud Server

on:
  push:
    branches: [main, develop]
  workflow_dispatch:

concurrency:
  group: deploy-cloud-server
  cancel-in-progress: true

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout Code
        uses: actions/checkout@v4

      - name: Setup Node.js 20
        uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: 'npm'
          cache-dependency-path: frontend/package-lock.json

      - name: Build React Frontend
        working-directory: frontend
        run: |
          npm ci
          npm run build
          tar -czf dist.tar.gz -C dist .

      - name: Transfer Artifacts to Cloud Server
        uses: appleboy/scp-action@v0.1.7
        with:
          host: ${{ secrets.VM_HOST }}
          username: ${{ secrets.VM_USERNAME }}
          key: ${{ secrets.VM_SSH_KEY }}
          port: ${{ secrets.VM_PORT || 22 }}
          source: "frontend/dist.tar.gz"
          target: "/tmp/"

      - name: Deploy Code & Reload Services
        uses: appleboy/ssh-action@v1.0.3
        with:
          host: ${{ secrets.VM_HOST }}
          username: ${{ secrets.VM_USERNAME }}
          key: ${{ secrets.VM_SSH_KEY }}
          port: ${{ secrets.VM_PORT || 22 }}
          script: |
            set -e

            # 1. Cập nhật Frontend
            rm -rf /var/www/lotus-fin-fe/*
            tar -xzf /tmp/frontend/dist.tar.gz -C /var/www/lotus-fin-fe/
            rm -f /tmp/frontend/dist.tar.gz

            # 2. Cập nhật Backend Code
            cd ~/lotus-fin
            git fetch origin main
            git reset --hard origin/main
            chmod +x run.sh

            # 3. Đồng bộ vào container & Migrate
            ./run.sh sync

            # 4. Dọn dẹp cache Docker bảo toàn ổ cứng
            docker system prune -f

            echo ">>> TRIỂN KHAI THÀNH CÔNG LÊN CLOUD SERVER! <<<"
```

---

## 9. QUY TRÌNH BẢO TRÌ & XỬ LÝ SỰ CỐ (TROUBLESHOOTING)

| Tình huống sự cố | Dấu hiệu nhận biết | Lệnh xử lý nhanh |
| :--- | :--- | :--- |
| **Hết dung lượng ổ đĩa** | `No space left on device` | `docker system prune -af --volumes`<br>`journalctl --vacuum-time=3d` |
| **Tràn RAM / OOM** | Container bị restart liên tục | `free -h` kiểm tra swap.<br>`docker restart frappe_docker-backend-1` |
| **Lỗi 502 Bad Gateway** | Nginx không kết nối được Backend | Kiểm tra container frontend Frappe: `docker ps`<br>`docker logs frappe_docker-frontend-1 --tail 50` |
| **Không tải được dữ liệu demo** | Báo lỗi DocType missing | Chạy lại: `./run.sh sync && ./run.sh demo` |
| **Xem log realtime của Backend** | Debug lỗi API Copilot | `docker logs -f frappe_docker-backend-1 --tail 100` |

---

*Tài liệu được biên soạn bởi Đội ngũ Kỹ thuật Lotus Fin — Lưu hành nội bộ.*
