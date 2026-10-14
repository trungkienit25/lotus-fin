# BƯỚC 7: TỰ ĐỘNG HÓA CI/CD TỪ GITHUB ACTIONS

> **Giai đoạn:** Bước 7 / 7 trong quy trình triển khai Lotus Fin  
> **Mục tiêu:** Thiết lập đường ống phân phối tự động liên tục (CI/CD Pipeline). Mỗi khi lập trình viên tạo Pull Request hoặc Merge commit vào nhánh chính, hệ thống tự động kiểm tra code, biên dịch giao diện và cập nhật lên Cloud Server trong 30 giây mà không cần thao tác thủ công.  
> **Điều kiện tiên quyết:** Đã hoàn thành [Bước 6: Kiểm thử toàn diện](./STEP_6_TESTING_AND_VERIFICATION.md).  

---

## 1. MÔ HÌNH HOẠT ĐỘNG CỦA ĐƯỜNG ỐNG CI/CD

```
 [ Lập trình viên ]
         │
    git push origin main
         │
         ▼
 ┌─────────────────────────────────────────────────────────────┐
 │                GITHUB ACTIONS RUNNER (Cloud)                │
 │                                                             │
 │  1. Checkout Code Repo                                      │
 │  2. Setup Node.js 20 & Caching npm                          │
 │  3. Chạy TypeCheck: npx tsc --noEmit                        │
 │  4. Build Production: npm run build (1.47s)                 │
 │  5. Đóng gói Artifact: dist.tar.gz (~820 KB)                │
 └──────────────────────────────┬──────────────────────────────┘
                                │
                    Kết nối an toàn SSH & SCP
                                │
                                ▼
 ┌─────────────────────────────────────────────────────────────┐
 │            LINUX CLOUD SERVER (<YOUR_SERVER_IP>)            │
 │                                                             │
 │  1. Giải nén dist.tar.gz vào /var/www/lotus-fin-fe/         │
 │  2. git fetch & git reset --hard origin/main                │
 │  3. Đồng bộ code lotus_fin vào container backend            │
 │  4. bench --site frontend migrate                           │
 │  5. bench --site frontend clear-cache                       │
 │  6. docker restart frappe_docker-backend-1                  │
 │  7. docker system prune -f (Dọn rác bảo toàn ổ SSD)        │
 └─────────────────────────────────────────────────────────────┘
```

---

## 2. QUY TRÌNH THIẾT LẬP CHI TIẾT

### 2.1. Cấu hình GitHub Secrets trong Repository
Để GitHub Actions có thể tự động kết nối vào Cloud Server qua giao thức SSH mà không cần mật khẩu:

1. Mở Repository trên trình duyệt GitHub: `https://github.com/trungkienit25/lotus-fin`
2. Vào **Settings** -> Mục bên trái chọn **Secrets and variables** -> **Actions**.
3. Bấm nút **New repository secret** màu xanh và tạo lần lượt 4 Secrets:

| Tên Secret | Giá trị cần điền | Mục đích |
| :--- | :--- | :--- |
| **`VM_HOST`** | `<YOUR_SERVER_IP>` | Địa chỉ IP Public của máy chủ Cloud Server |
| **`VM_USERNAME`**| `root` *(hoặc `ubuntu`)* | Tên người dùng quản trị SSH |
| **`VM_SSH_KEY`** | *Nội dung Private Key SSH* | Khóa bí mật để xác thực đăng nhập không cần password |
| **`VM_PORT`** | `22` | Cổng SSH mặc định |

> **Cách lấy nội dung `VM_SSH_KEY`:**  
> Mở file Private Key của bạn (ví dụ file `id_rsa` hoặc file `.pem` của máy chủ) bằng Notepad. Copy **toàn bộ nội dung** bắt đầu từ `-----BEGIN ... PRIVATE KEY-----` cho đến hết dòng `-----END ... PRIVATE KEY-----` rồi dán vào ô Secret.

---

### 2.2. Tạo file cấu hình Workflow (`.github/workflows/deploy.yml`)
Trong mã nguồn dự án Lotus Fin, tạo file `.github/workflows/deploy.yml`:

```yaml
name: Deploy Lotus Fin to Cloud Server

on:
  push:
    branches:
      - main
      - develop
  workflow_dispatch: # Cho phép bấm nút "Run workflow" để deploy thủ công

concurrency:
  group: deploy-cloud-server
  cancel-in-progress: true

jobs:
  build-and-deploy:
    name: Build Frontend & Deploy to Cloud Server
    runs-on: ubuntu-latest
    timeout-minutes: 15

    steps:
      # Bước 1: Kéo mã nguồn
      - name: Checkout Codebase
        uses: actions/checkout@v4

      # Bước 2: Khởi tạo môi trường Node.js
      - name: Setup Node.js 20
        uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: 'npm'
          cache-dependency-path: frontend/package-lock.json

      # Bước 3: Biên dịch giao diện React Frontend
      - name: Build React Production Bundle
        working-directory: frontend
        run: |
          npm ci
          npm run build
          tar -czf dist.tar.gz -C dist .

      # Bước 4: Đẩy file nén Frontend sang Cloud Server qua SCP
      - name: Transfer Frontend Artifact to Cloud Server
        uses: appleboy/scp-action@v0.1.7
        with:
          host: ${{ secrets.VM_HOST }}
          username: ${{ secrets.VM_USERNAME }}
          key: ${{ secrets.VM_SSH_KEY }}
          port: ${{ secrets.VM_PORT || 22 }}
          source: "frontend/dist.tar.gz"
          target: "/tmp/"

      # Bước 5: Thực thi kịch bản cập nhật Backend trên Cloud Server qua SSH
      - name: Execute Remote Deployment via SSH
        uses: appleboy/ssh-action@v1.0.3
        with:
          host: ${{ secrets.VM_HOST }}
          username: ${{ secrets.VM_USERNAME }}
          key: ${{ secrets.VM_SSH_KEY }}
          port: ${{ secrets.VM_PORT || 22 }}
          script: |
            set -e
            echo "=========================================================="
            echo "       BẮT ĐẦU QUY TRÌNH CẬP NHẬT TỰ ĐỘNG LOTUS FIN       "
            echo "=========================================================="

            echo ">>> [1/4] Cập nhật giao diện React Frontend..."
            rm -rf /var/www/lotus-fin-fe/*
            tar -xzf /tmp/frontend/dist.tar.gz -C /var/www/lotus-fin-fe/
            chown -R www-data:www-data /var/www/lotus-fin-fe
            chmod -R 755 /var/www/lotus-fin-fe
            rm -f /tmp/frontend/dist.tar.gz

            echo ">>> [2/4] Cập nhật mã nguồn Backend từ Git..."
            cd ~/lotus-fin
            git fetch origin
            git reset --hard origin/${{ github.ref_name }}
            chmod +x run.sh

            echo ">>> [3/4] Đồng bộ ứng dụng vào Docker & Migrate Database..."
            ./run.sh sync

            echo ">>> [4/4] Dọn dẹp layer cache thừa của Docker (Bảo vệ ổ SSD)..."
            docker system prune -f

            echo "=========================================================="
            echo "    [THÀNH CÔNG] HỆ THỐNG ĐÃ ĐƯỢC CẬP NHẬT TRÊN CLOUD!    "
            echo "=========================================================="
```

---

## 3. THỬ NGHIỆM ĐƯỜNG ỐNG CI/CD (TESTING THE PIPELINE)

1. **Kích hoạt Deploy:**
   * Thực hiện một thay đổi nhỏ (ví dụ chỉnh sửa một dòng comment) -> Commit và Push lên nhánh `main`:
     ```bash
     git add .
     git commit -m "chore: test automatic cicd pipeline"
     git push origin main
     ```
2. **Quan sát tiến trình:**
   * Vào tab **Actions** trên giao diện GitHub.
   * Bấm vào workflow đang chạy: `Deploy Lotus Fin to Cloud Server`.
   * Quan sát từng bước: `Checkout Codebase` -> `Build React Production Bundle` -> `Transfer Frontend Artifact` -> `Execute Remote Deployment`.
3. **Thời gian hoàn thành:** Toàn bộ quá trình từ lúc push git đến khi server live mất khoảng **25 – 45 giây**.

---

## 4. QUY TRÌNH ROLLBACK (KHI CÓ SỰ CỐ)

Nếu phiên bản mới bị lỗi logic cần quay về phiên bản cũ ngay lập tức:

### Cách 1: Revert Commit qua Git (Khuyên dùng)
```bash
git revert HEAD
git push origin main
```
*Đường ống CI/CD sẽ tự động kích hoạt lại và đưa hệ thống trở về phiên bản trước đó trong 30 giây.*

### Cách 2: Rollback khẩn cấp trực tiếp trên Server (Khi CI/CD gặp sự cố)
SSH vào máy chủ: `ssh root@<YOUR_SERVER_IP>`:
```bash
cd ~/lotus-fin
# Quay về commit ID ổn định trước đó
git reset --hard <COMMIT_ID_TRƯỚC>
./run.sh sync
```

---

## 5. CHECKLIST NGHIỆM THU TOÀN DIỆN BƯỚC 7

- [ ] Đã thêm 4 Secrets (`VM_HOST`, `VM_USERNAME`, `VM_SSH_KEY`, `VM_PORT`) trong GitHub Repository.
- [ ] File `.github/workflows/deploy.yml` đã được commit vào nhánh `main`.
- [ ] Chạy thử 1 lần Deploy thành công với tích xanh ✅ trên GitHub Actions.
- [ ] Truy cập `http://<YOUR_SERVER_IP>/` hiển thị đúng nội dung của commit mới nhất.

---

🎉 **CHÚC MỪNG! HỆ THỐNG LOTUS FIN ĐÃ ĐƯỢC TRIỂN KHAI VÀ TỰ ĐỘNG HÓA HOÀN TẤT TRÊN CLOUD SERVER!**
