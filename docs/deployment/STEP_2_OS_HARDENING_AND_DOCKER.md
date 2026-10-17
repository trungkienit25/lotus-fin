# BƯỚC 2: CHUẨN BỊ & TỐI ƯU HÓA MÔI TRƯỜNG OS (OS HARDENING & DOCKER)

> **Giai đoạn:** Bước 2 / 7 trong quy trình triển khai Lotus Fin  
> **Mục tiêu:** Kích hoạt bộ nhớ đệm Swap 2GB, cài đặt Docker CE & Docker Compose v2 chính thức, cấu hình xoay vòng log chống tràn ổ đĩa SSD và tạo các thư mục ứng dụng.  
> **Điều kiện tiên quyết:** Đã hoàn thành [Bước 1: Khảo sát hiện trạng](./STEP_1_SERVER_SURVEY.md).  

---

## 1. TẠI SAO PHẢI THỰC HIỆN CÁC THIẾT LẬP NÀY?

1. **Bộ nhớ ảo (Swap Memory):**
   * Khi chạy các lệnh nặng như `bench migrate`, `bench build`, hoặc khi MariaDB nạp nhiều giao dịch chứng từ, Linux kernel cần một vùng nhớ đệm an toàn.
   * Nếu không có Swap, khi RAM chạm 100%, tiến trình `mysqld` hoặc `gunicorn` sẽ bị **OOM Killer** của hệ điều hành tắt đột ngột, gây hỏng dữ liệu (Database corruption).
2. **Cấu hình Docker Log Rotation:**
   * Mặc định, Docker ghi log container dạng file JSON và **không giới hạn dung lượng**. Sau 1 – 2 tuần chạy liên tục, log có thể phình to lên tới 10 – 20 GB, làm **đầy sạch ổ cứng**.
   * Thiết lập `max-size: 10m` và `max-file: 3` đảm bảo mỗi container chỉ dùng tối đa **30 MB log**, giữ ổ cứng luôn sạch sẽ và an toàn.

---

## 2. QUY TRÌNH THỰC HIỆN CHI TIẾT

Đăng nhập vào máy chủ: `ssh root@<YOUR_SERVER_IP>` và thực hiện lần lượt các bước sau:

### 2.1. Tạo 2GB Swap Memory & Tinh chỉnh Swappiness
Chạy khối lệnh sau để cấp phát và cố định Swap:

```bash
# 1. Tạo file swap 2GB
fallocate -l 2G /swapfile

# 2. Khóa quyền chỉ cho phép root đọc/ghi
chmod 600 /swapfile

# 3. Định dạng phân vùng swap
mkswap /swapfile

# 4. Kích hoạt swap vào hệ thống
swapon /swapfile

# 5. Lưu vào fstab để tự động bật mỗi khi khởi động lại máy
if ! grep -q '/swapfile' /etc/fstab; then
    echo '/swapfile none swap sw 0 0' >> /etc/fstab
fi

# 6. Tối ưu giá trị swappiness = 10 (chỉ dùng Swap khi RAM thực tế còn dưới 10%)
sysctl vm.swappiness=10
if ! grep -q 'vm.swappiness' /etc/sysctl.conf; then
    echo 'vm.swappiness=10' >> /etc/sysctl.conf
fi
```

*Kiểm tra kết quả:*
```bash
free -h
```
👉 *Kỳ vọng:* Dòng `Swap:` hiển thị `total: 2.0Gi`.

---

### 2.2. Cài đặt Docker Engine & Docker Compose chính thức (Docker CE)
Cài đặt bản Docker chính thức từ Docker Hub repository (tránh dùng bản đóng gói cũ của Ubuntu):

```bash
# 1. Cài các gói tiện ích bảo mật
apt update
apt install -y ca-certificates curl gnupg lsb-release

# 2. Đăng ký GPG Key chính thức của Docker
mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg --yes

# 3. Đăng ký Apt Repository của Docker
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null

# 4. Cập nhật và cài đặt Docker CE & Docker Compose Plugin
apt update
apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# 5. Bật Docker service tự khởi động cùng máy chủ
systemctl enable docker
systemctl start docker
```

*Kiểm tra phiên bản:*
```bash
docker --version && docker compose version
```
👉 *Kỳ vọng:*  
* `Docker version 27.x.x` (hoặc mới hơn)  
* `Docker Compose version v2.x.x`

---

### 2.3. Cấu hình giới hạn Docker Log (Chống tràn ổ đĩa SSD)
Tạo file cấu hình daemon của Docker:

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

# Áp dụng cấu hình ngay lập tức
systemctl restart docker
```

---

### 2.4. Chuẩn bị các thư mục ứng dụng
Tạo sẵn thư mục chứa mã nguồn backend và thư mục web chứa React Frontend:

```bash
# Thư mục chứa gói tĩnh của React Frontend (Nginx sẽ đọc thư mục này)
mkdir -p /var/www/lotus-fin-fe
chmod -R 755 /var/www/lotus-fin-fe

# Thư mục chứa mã nguồn chính của dự án Lotus Fin
mkdir -p ~/lotus-fin
```

---

## 3. CHECKLIST NGHIỆM THU BƯỚC 2

Trước khi chuyển sang Bước 3, đảm bảo tất cả các điều kiện sau đã đạt:

- [ ] Lệnh `swapon --show` trả về `/swapfile partition 2G`.
- [ ] Lệnh `sysctl vm.swappiness` trả về `vm.swappiness = 10`.
- [ ] Lệnh `docker info` chạy thành công, không báo lỗi daemon chưa bật.
- [ ] Lệnh `docker compose version` nhận diện được compose plugin v2.
- [ ] File `/etc/docker/daemon.json` có thiết lập `max-size: 10m`.
- [ ] Thư mục `/var/www/lotus-fin-fe` đã được tạo thành công.

---

👉 **Chuyển sang:** [BƯỚC 3: TRIỂN KHAI CỤM FRAPPE / ERPNEXT BACKEND DOCKER](./STEP_3_BACKEND_DEPLOYMENT.md)
