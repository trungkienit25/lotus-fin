# BƯỚC 4: CẤU HÌNH NGINX REVERSE PROXY & SSL HTTPS

> **Giai đoạn:** Bước 4 / 7 trong quy trình triển khai Lotus Fin  
> **Mục tiêu:** Cấu hình máy chủ web Nginx trên máy chủ để phục vụ giao diện tĩnh React SPA, chuyển tiếp các yêu cầu API & Desk về Docker cổng 8080 và thiết lập chứng chỉ SSL HTTPS miễn phí.  
> **Điều kiện tiên quyết:** Đã hoàn thành [Bước 3: Triển khai cụm Backend Docker](./STEP_3_BACKEND_DEPLOYMENT.md).  

---

## 1. VAI TRÒ CỦA NGINX TRONG KIẾN TRÚC LOTUS FIN

Nginx được cài đặt trực tiếp trên hệ điều hành của máy chủ (Host Nginx) đóng vai trò là **Gateway duy nhất đón tiếp người dùng**:
1. **Phục vụ giao diện người dùng (Frontend Web Server):** Trực tiếp đọc các file tĩnh HTML, CSS, JavaScript của React từ thư mục `/var/www/lotus-fin-fe`. Tốc độ phản hồi dưới 10ms mà không cần đi qua Docker.
2. **Reverse Proxy API:** Chuyển hướng các request `/api/`, `/assets/`, `/desk/`, `/app/` sang Docker container `frappe_docker-frontend-1` tại cổng nội bộ `127.0.0.1:8080`.
3. **Ủy nhiệm WebSocket (Socket.io Proxy):** Giữ kết nối socket thời gian thực cho tính năng chat của AI Copilot và thanh thông báo Desk.
4. **Bảo mật & Mã hóa SSL (SSL Termination):** Xử lý mã hóa HTTPS tại cổng 443, giảm tải việc mã hóa cho các container bên trong.

---

## 2. QUY TRÌNH CẤU HÌNH CHI TIẾT

Đăng nhập vào máy chủ qua SSH: `ssh root@<YOUR_SERVER_IP>`.

### 2.1. Tạo cấu hình Virtual Host Nginx cho Lotus Fin
Tạo file cấu hình tại `/etc/nginx/sites-available/lotusfin`:

```bash
cat > /etc/nginx/sites-available/lotusfin << 'EOF'
server {
    listen 80;
    server_name _; # Điền domain của bạn nếu có (ví dụ: demo.lotusfin.vn)

    # Giới hạn kích thước tải file chứng từ lên (50MB)
    client_max_body_size 50m;

    # Ghi log chi tiết
    access_log /var/log/nginx/lotusfin_access.log;
    error_log /var/log/nginx/lotusfin_error.log;

    # -------------------------------------------------------------
    # 1. PHỤC VỤ REACT SINGLE PAGE APPLICATION (SPA)
    # -------------------------------------------------------------
    location / {
        root /var/www/lotus-fin-fe;
        index index.html;
        # Hỗ trợ React Router: Khi F5 không bị lỗi 404
        try_files $uri $uri/ /index.html;

        # Tối ưu cache cho các file tĩnh đã nén hash (JS/CSS/Hình ảnh)
        location ~* \.(js|css|png|jpg|jpeg|gif|svg|ico|woff|woff2|ttf)$ {
            expires 30d;
            add_header Cache-Control "public, no-transform";
        }
    }

    # -------------------------------------------------------------
    # 2. REVERSE PROXY CHO FRAPPE BACKEND & COPILOT API
    # -------------------------------------------------------------
    location ~ ^/(api|assets|files|socket.io|app|desk)/ {
        proxy_pass http://127.0.0.1:8080;
        proxy_http_version 1.1;

        # Cấu hình WebSocket cho tính năng Realtime & AI Copilot Chat
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";

        # Chuyển tiếp đúng Host và IP thực của người dùng
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Tăng timeout lên 180s để xử lý các báo cáo tính toán tài chính lớn
        proxy_connect_timeout 60s;
        proxy_send_timeout 180s;
        proxy_read_timeout 180s;

        # Tắt đệm proxy để phản hồi dạng Stream của AI không bị trễ
        proxy_buffering off;
    }
}
EOF
```

---

### 2.2. Kích hoạt Virtual Host & Kiểm tra cú pháp
Chạy khối lệnh sau để áp dụng cấu hình:

```bash
# 1. Gỡ bỏ file default cũ của Nginx
rm -f /etc/nginx/sites-enabled/default

# 2. Tạo liên kết kích hoạt cấu hình lotusfin
ln -sf /etc/nginx/sites-available/lotusfin /etc/nginx/sites-enabled/

# 3. Kiểm tra tính hợp lệ của cấu hình Nginx
nginx -t
```

👉 *Kỳ vọng:* Terminal in ra 2 dòng sau mà không có cảnh báo:
```text
nginx: the configuration file /etc/nginx/nginx.conf syntax is ok
nginx: configuration file /etc/nginx/nginx.conf test is successful
```

Sau đó reload Nginx để áp dụng ngay:
```bash
systemctl reload nginx
```

---

### 2.3. Cài đặt chứng chỉ SSL HTTPS miễn phí (Certbot Let's Encrypt)
*Lưu ý: Bước này áp dụng khi bạn đã trỏ một tên miền (Domain) về IP của máy chủ (ví dụ `demo.lotusfin.vn`). Nếu chỉ dùng IP trực tiếp, bạn bỏ qua bước này.*

1. **Cài đặt công cụ Certbot:**
   ```bash
   apt install -y certbot python3-certbot-nginx
   ```
2. **Kích hoạt HTTPS tự động bằng 1 lệnh duy nhất:**
   ```bash
   certbot --nginx -d demo.lotusfin.vn
   ```
   *Nhập email của bạn và chọn `Y` đồng ý điều khoản.*
3. **Kiểm tra tự động gia hạn chứng chỉ:**
   ```bash
   certbot renew --dry-run
   ```
   *Certbot sẽ tự tạo cronjob định kỳ tự động gia hạn trước khi hết hạn 30 ngày, bạn không cần phải can thiệp thủ công.*

---

## 3. CHECKLIST NGHIỆM THU BƯỚC 4

- [ ] Lệnh `nginx -t` trả về `syntax is ok` và `test is successful`.
- [ ] Lệnh `systemctl status nginx` hiển thị `active (running)`.
- [ ] Thử truy cập từ xa qua curl kiểm tra proxy API:
  ```bash
  curl -I http://<YOUR_SERVER_IP>/api/method/ping
  ```
  👉 *Kỳ vọng:* Trả về `HTTP/1.1 200 OK` (chứng tỏ Nginx đã forward thành công vào Docker).
- [ ] Mở trình duyệt truy cập `http://<YOUR_SERVER_IP>/desk` chuyển tiếp đến trang đăng nhập Frappe.

---

👉 **Chuyển sang:** [BƯỚC 5: ĐÓNG GÓI & TRIỂN KHAI GIAO DIỆN REACT FRONTEND](./STEP_5_FRONTEND_DEPLOYMENT.md)
