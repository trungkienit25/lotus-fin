# BƯỚC 1: KHẢO SÁT & ĐÁNH GIÁ HIỆN TRẠNG CLOUD SERVER

> **Giai đoạn:** Bước 1 / 7 trong quy trình triển khai Lotus Fin  
> **Mục tiêu:** Rà soát toàn diện phần cứng, hệ điều hành, cấu hình mạng, cổng dịch vụ đang chạy và kết nối Internet trước khi cài đặt.  
> **Môi trường:** Linux Cloud Server / VPS (Ubuntu 22.04 LTS / Debian 12)  

---

## 1. MỤC TIÊU KHẢO SÁT
Trước khi cài đặt bất kỳ gói phần mềm nào, kỹ sư vận hành bắt buộc phải nắm rõ:
1. **Tài nguyên phần cứng:** Số vCPU, dung lượng RAM thực tế, dung lượng ổ đĩa SSD còn trống.
2. **Hệ điều hành:** Phiên bản Linux Kernel và bản phân phối Ubuntu/Debian (đảm bảo tương thích với Docker & Frappe v16).
3. **Các cổng mạng (Network Ports):** Kiểm tra xem cổng `80` (HTTP), `443` (HTTPS), `8080` (Frappe), `3306` (MariaDB) có đang bị tiến trình nào chiếm dụng hay không.
4. **Tường lửa (Firewall):** Kiểm tra trạng thái tường lửa cục bộ `ufw` trên máy chủ và Security Group trên bảng điều khiển Cloud Server.
5. **Khả năng kết nối Internet ra ngoài:** Đảm bảo máy chủ có thể kéo mã nguồn từ GitHub và tải Docker Images từ Docker Hub mà không bị chặn mạng.

---

## 2. KỊCH BẢN CHẨN ĐOÁN TỰ ĐỘNG (DIAGNOSTIC SCRIPT)

Đăng nhập vào máy chủ qua SSH với quyền `root` (hoặc user có quyền `sudo`):
```bash
ssh root@<YOUR_SERVER_IP>
```

Tạo và chạy script khảo sát toàn diện:
```bash
cat << 'EOF' > /tmp/survey.sh
#!/usr/bin/env bash
set -e

echo "=========================================================="
echo "          LOTUS FIN - BÁO CÁO KHẢO SÁT HỆ THỐNG          "
echo "=========================================================="

echo -e "\n[1] THÔNG TIN HỆ ĐIỀU HÀNH & KERNEL"
echo "Hostname: $(hostname)"
echo "Kernel: $(uname -r)"
echo "OS: $(lsb_release -ds 2>/dev/null || cat /etc/os-release | grep PRETTY_NAME | cut -d= -f2)"

echo -e "\n[2] TÀI NGUYÊN PHẦN CỨNG (CPU / RAM / DISK)"
echo "CPU Cores: $(nproc) vCPU"
echo "Model CPU: $(lscpu | grep 'Model name' | sed 's/Model name:[ \t]*//' || echo 'Virtual CPU')"
echo -e "\nRAM & Swap:"
free -h
echo -e "\nỔ đĩa lưu trữ (Disk Space):"
df -h /

echo -e "\n[3] PHẦN MỀM HỆ THỐNG CƠ BẢN"
echo "Git: $(git --version 2>/dev/null || echo 'CHƯA CÀI')"
echo "Docker: $(docker -v 2>/dev/null || echo 'CHƯA CÀI')"
echo "Docker Compose: $(docker compose version 2>/dev/null || echo 'CHƯA CÀI')"
echo "Nginx: $(nginx -v 2>&1 || echo 'CHƯA CÀI')"
echo "Python: $(python3 -V 2>/dev/null || echo 'CHƯA CÀI')"

echo -e "\n[4] KIỂM TRA CỔNG MẠNG ĐANG MỞ (PORTS LISTENING)"
ss -tulpn | grep -E ':80|:443|:8080|:3306|:6379' || echo "-> Các cổng chuẩn đều đang rảnh."

echo -e "\n[5] TRẠNG THÁI TƯỜNG LỬA NỘI BỘ (UFW)"
ufw status

echo -e "\n[6] KẾT NỐI MẠNG RA NGOÀI (OUTBOUND CONNECTIVITY)"
echo -n "1. Kết nối GitHub (Code Repo): "
curl -Is --connect-timeout 5 https://github.com | head -n 1
echo -n "2. Kết nối Docker Hub (Registry): "
curl -Is --connect-timeout 5 https://registry-1.docker.io/v2/ | head -n 1
echo -n "3. Phân giải DNS (Google DNS): "
getent hosts google.com > /dev/null && echo "OK" || echo "LỖI DNS"

echo "=========================================================="
EOF
chmod +x /tmp/survey.sh
/tmp/survey.sh
```

---

## 3. BẢNG TIÊU CHUẨN ĐÁNH GIÁ & ĐỐI SOÁT THỰC TẾ

Dưới đây là kết quả đối chiếu giữa tiêu chuẩn yêu cầu và các mốc đánh giá kỹ thuật chuẩn:

| Hạng mục khảo sát | Lệnh kiểm tra thủ công | Tiêu chuẩn Lotus Fin | Khuyến nghị hành động |
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

## 4. KẾT LUẬN & HÀNH ĐỘNG TIẾP THEO

* **Đánh giá tổng quan:** Khi máy chủ đáp ứng đầy đủ năng lực xử lý (RAM $\ge$ 4GB, SSD trống $\ge$ 20GB, mạng thông suốt), hệ thống sẵn sàng sang bước cấu hình.
* **Nhiệm vụ cần thực hiện ngay ở Bước 2:**
  1. Tạo **2GB Swap** để bảo vệ hệ thống trước các đỉnh tải CPU/RAM khi tính toán kịch bản Stress-test.
  2. Cài đặt **Docker Engine & Docker Compose Plugin** bản chính thức từ Docker repository.
  3. Bật cấu hình **Docker Log Rotation** (10MB/file) để ngăn chặn việc ghi log làm đầy ổ SSD theo thời gian.

👉 **Chuyển sang:** [BƯỚC 2: CHUẨN BỊ & TỐI ƯU HÓA MÔI TRƯỜNG OS](./STEP_2_OS_HARDENING_AND_DOCKER.md)
