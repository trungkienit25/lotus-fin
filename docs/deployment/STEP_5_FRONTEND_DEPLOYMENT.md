# BƯỚC 5: ĐÓNG GÓI & TRIỂN KHAI GIAO DIỆN REACT FRONTEND

> **Giai đoạn:** Bước 5 / 7 trong quy trình triển khai Lotus Fin  
> **Mục tiêu:** Biên dịch ứng dụng React (TypeScript / Vite / Tailwind) tại máy phát triển thành gói tĩnh tối ưu và triển khai lên máy chủ web Nginx.  
> **Điều kiện tiên quyết:** Đã hoàn thành [Bước 4: Cấu hình Nginx Web Server](./STEP_4_NGINX_AND_SSL_CONFIG.md).  

---

## 1. NGUYÊN TẮC TỐI ƯU HÓA: BUILD TẠI LOCAL vs BUILD TRÊN VM

Một sai lầm phổ biến khi triển khai Single Page App là cài đặt Node.js và chạy `npm install` trực tiếp trên máy chủ. Trong dự án Lotus Fin, chúng ta áp dụng quy trình tối ưu tuyệt đối:

| Tiêu chí | Build trực tiếp trên VM | Build tại Local / GitHub Runner (Áp dụng) |
| :--- | :--- | :--- |
| **Tiêu hao ổ cứng VM** | Tốn thêm **~1.2 GB** cho thư mục `node_modules` | **Chỉ tốn ~820 KB** (đúng bằng dung lượng file `dist`) |
| **Tiêu hao RAM khi build** | Ngốn đỉnh điểm **1.5 GB RAM** của máy chủ | Máy chủ không tốn 1 byte RAM nào cho quá trình build |
| **Thời gian thực thi** | 45 – 90 giây | **1.47 giây** (nhờ Vite & Rolldown engine trên máy dev) |
| **Rủi ro vận hành** | Dễ gây lỗi OOM nếu đang có user truy cập | Không ảnh hưởng đến dịch vụ đang chạy trên server |

---

## 2. QUY TRÌNH THỰC HIỆN CHI TIẾT

Quy trình gồm 2 phần: Thao tác tại Máy tính của bạn (Local Machine) và Thao tác trên Cloud Server.

### PHẦN A: Thao tác tại Máy tính cá nhân (Local Machine)

Mở cửa sổ PowerShell hoặc Terminal tại thư mục gốc của dự án `d:\Coding\lotus-fin`:

```powershell
# 1. Di chuyển vào thư mục frontend
cd frontend

# 2. Chạy kiểm tra TypeScript và Build phiên bản Production
npm run build
```

👉 *Kết quả đo được thực tế:*
```text
vite building client environment for production...
✓ 371 modules transformed.
dist/index.html                   0.83 kB │ gzip:   0.47 kB
dist/assets/index-Hdtseq5b.css   62.30 kB │ gzip:  10.78 kB
dist/assets/index-o2lwkPo2.js   758.90 kB │ gzip: 217.33 kB
✓ built in 1.47s
```

```powershell
# 3. Đóng gói thư mục dist thành file nén duy nhất
tar -czf dist.tar.gz -C dist .

# 4. Tải file dist.tar.gz lên thư mục tạm /tmp/ trên Cloud Server qua SCP
scp -P 22 .\dist.tar.gz root@<YOUR_SERVER_IP>:/tmp/
```
*(Nhập mật khẩu SSH của root khi được hỏi. Quá trình tải lên file 800KB chỉ mất 1 – 2 giây).*

---

### PHẦN B: Thao tác trên Cloud Server (Qua SSH)

Đăng nhập vào máy chủ qua SSH: `ssh root@<YOUR_SERVER_IP>` và chạy khối lệnh giải nén:

```bash
# 1. Dọn sạch thư mục web tĩnh cũ
rm -rf /var/www/lotus-fin-fe/*

# 2. Giải nén file dist.tar.gz vừa tải lên vào thư mục web
tar -xzf /tmp/dist.tar.gz -C /var/www/lotus-fin-fe/

# 3. Phân quyền chuẩn cho tiến trình Nginx đọc file
chown -R www-data:www-data /var/www/lotus-fin-fe
chmod -R 755 /var/www/lotus-fin-fe

# 4. Xóa file nén tạm để giữ sạch ổ cứng
rm -f /tmp/dist.tar.gz
```

*Kiểm tra danh sách file đã có trong thư mục web:*
```bash
ls -la /var/www/lotus-fin-fe/
```
👉 *Kỳ vọng:* Thấy xuất hiện file `index.html` và thư mục `assets/` chứa các bundle `.js` và `.css`.

---

## 3. KIỂM TRA TRỰC TIẾP TRÊN TRÌNH DUYỆT (BROWSER TEST)

1. Mở trình duyệt web (Chrome, Edge hoặc Firefox).
2. Truy cập vào địa chỉ: **`http://<YOUR_SERVER_IP>/`**
3. **Kiểm tra giao diện người dùng:**
   * Giao diện **Lotus Fin (TailAdmin)** tải lên nhanh chóng (< 1 giây).
   * Font chữ `font-satoshi` chuẩn thương hiệu Lotus Fin.
   * Màu sắc chủ đạo: Xanh `#1E63B7` và Cyan `#6EC1F6`, hiển thị chuẩn Light Mode.
4. **Kiểm tra AI Copilot Chat Drawer:**
   * Ở góc dưới bên phải màn hình có nút tròn floating dạng Messenger (kích thước `size-12`).
   * Bấm vào nút chat: Cửa sổ popup chat hiện lên mượt mà kích thước `420px x 580px`.
   * Thử gõ câu hỏi: `sức khỏe tài chính` -> Kiểm tra phản hồi phân tích tài chính trả về từ backend.
5. **Kiểm tra Network trong DevTools (F12):**
   * Tab **Console:** Không có lỗi đỏ (No CORS error, No unhandled promise).
   * Tab **Network:** Các request API gửi về `/api/method/...` đều trả về mã HTTP `200 OK`.

---

## 4. CHECKLIST NGHIỆM THU BƯỚC 5

- [ ] File `index.html` nằm tại `/var/www/lotus-fin-fe/index.html`.
- [ ] Truy cập `http://<YOUR_SERVER_IP>/` hiển thị trang chủ Lotus Fin.
- [ ] Bấm F5 tải lại trang bất kỳ (ví dụ `/lotus-copilot`) không bị lỗi 404 (chứng tỏ rule `try_files` của Nginx hoạt động đúng).
- [ ] Bong bóng chat AI Copilot ở góc phải mở ra và tương tác bình thường.

---

👉 **Chuyển sang:** [BƯỚC 6: KẾ HOẠCH KIỂM THỬ TOÀN DIỆN & ĐỐI SOÁT](./STEP_6_TESTING_AND_VERIFICATION.md)
