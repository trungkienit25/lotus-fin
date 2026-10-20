# 05 — Lotus Fin Brand Guideline & Visual Identity System

Tài liệu hướng dẫn quy chuẩn nhận diện thương hiệu (**Brand Guideline & Visual Identity**) của hệ thống **Lotus Fin — Intelligent ERP Desk**.

---

## 🌸 1. Brand Identity & Triết lý Thương hiệu

- **Tên thương hiệu**: **LOTUS FIN** (Lotus Financial Intelligence)
- **Slogan / Tagline**: *"INTELLIGENCE IN BLOOM"*
- **Thuộc tính thương hiệu (Brand Essence)**:
  - **Modern** (Hiện đại): Thiết kế tối giản, công nghệ tiên tiến, chuẩn quốc tế.
  - **Fresh** (Tươi mới): Màu sắc thanh khiết, trẻ trung, giao diện thoáng đãng.
  - **Trustworthy** (Đáng tin cậy): Nền tảng tài chính chuẩn mực, bảo mật, minh bạch.
  - **Growth** (Phát triển): Hoa sen nở rộ đại diện cho sự thịnh vượng và tăng trưởng bền vững của doanh nghiệp.

---

## 🖼️ 2. Hệ thống Tài nguyên Hình ảnh (Brand Assets)

Các tệp ảnh gốc được lưu trữ trực tiếp tại thư mục [`frontend/public/brand/`](file:///d:/Coding/lotus-fin/frontend/public/brand):

| Tài nguyên | Đường dẫn Public | Định dạng | Mô tả & Cách sử dụng |
| :--- | :--- | :--- | :--- |
| **Brand Palette** | `/brand/brand-guideline.jpg` | JPG / Key Visual | Bảng màu quy chuẩn, thông số RGB/HEX và hướng dẫn sử dụng Gradient. |
| **Logo Emblem** | `/brand/logo.jpg` | JPG / Transparent | Biểu tượng hoa sen cách điệu nhiều lớp với hiệu ứng chuyển màu rực rỡ. |
| **App Icon / Favicon** | `/brand/favicon.jpg` | JPG / Squircle | Biểu tượng ứng dụng bo góc mềm mại (iOS Squircle) trên nền sáng dịu. |
| **Wordmark / Text** | `/brand/text.jpg` | JPG / Horizontal | Logotype ngang "LOTUS FIN" kèm khẩu hiệu "INTELLIGENCE IN BLOOM". |

---

## 🎨 3. Bảng màu Quy chuẩn (Color Palette)

### 3.1. Màu chủ đạo (Brand Colors)

| Màu sắc | Tên gọi | Mã HEX | RGB | HSL | Ý nghĩa & Vị trí sử dụng |
| :--- | :--- | :--- | :--- | :--- | :--- |
| <span style="display:inline-block;width:18px;height:18px;background:#1E63B7;border-radius:4px;"></span> | **Blue Deep** | `#1E63B7` | `rgb(30, 99, 183)` | `213°, 72%, 42%` | **Màu thương hiệu gốc**: Nút hành động chính, chữ "LOTUS", viền tiêu điểm, thanh điều hướng. |
| <span style="display:inline-block;width:18px;height:18px;background:#6EC1F6;border-radius:4px;"></span> | **Blue Light** | `#6EC1F6` | `rgb(110, 193, 246)` | `203°, 89%, 70%` | **Màu chuyển tiếp**: Điểm giữa gradient chính, hover state, biểu tượng thông tin. |
| <span style="display:inline-block;width:18px;height:18px;background:#39C6B7;border-radius:4px;"></span> | **Teal** | `#39C6B7` | `rgb(57, 198, 183)` | `174°, 55%, 50%` | **Cân bằng & Tăng trưởng**: Tagline "INTELLIGENCE IN BLOOM", biểu đồ phân tích. |
| <span style="display:inline-block;width:18px;height:18px;background:#2FB29A;border-radius:4px;"></span> | **Mint Green** | `#2FB29A` | `rgb(47, 178, 154)` | `169°, 58%, 44%` | **Tài chính & Sức khỏe**: Chữ "FIN", chỉ số tài chính dương, badge hoàn thành/thành công. |
| <span style="display:inline-block;width:18px;height:18px;background:#FF8FB1;border-radius:4px;"></span> | **Pink Accent** | `#FF8FB1` | `rgb(255, 143, 177)` | `342°, 100%, 78%` | **Điểm nhấn nhụy sen**: Nụ hoa đỉnh logo, thông báo nổi bật, huy hiệu AI Copilot, highlight quan trọng. |

---

### 3.2. Màu phụ & Nền (Neutral & Support Colors)

| Màu sắc | Tên gọi | Mã HEX | RGB | Vị trí sử dụng |
| :--- | :--- | :--- | :--- | :--- |
| <span style="display:inline-block;width:18px;height:18px;background:#2E3A59;border-radius:4px;"></span> | **Text Primary** | `#2E3A59` | `rgb(46, 58, 89)` | Văn bản chính, tiêu đề H1-H6, nhãn trường dữ liệu (Độ tương phản cao). |
| <span style="display:inline-block;width:18px;height:18px;background:#8FA1B3;border-radius:4px;"></span> | **Text Secondary** | `#8FA1B3` | `rgb(143, 161, 179)` | Văn bản phụ, placeholder, đường dẫn breadcrumb mờ, mô tả tính năng. |
| <span style="display:inline-block;width:18px;height:18px;background:#E8F2FB;border-radius:4px;"></span> | **Background Light**| `#E8F2FB` | `rgb(232, 242, 251)` | Nền trang tổng quan, vùng chứa card, background widget mềm mại. |

---

## 🌈 4. Hệ thống Dải màu Chuyển động (Gradients)

```mermaid
flowchart LR
    subgraph PrimaryGrad ["Gradient Chính (Key Visual / Hero / Logo)"]
        G1["#1E63B7\n(Blue Deep - 0%)"] --> G2["#6EC1F6\n(Blue Light - 50%)"] --> G3["#2FB29A\n(Mint Green - 100%)"]
    end
    
    subgraph AccentGrad ["Gradient Bổ trợ (Highlight / Accent / Badges)"]
        A1["#FFDDE7\n(Soft Rose - 0%)"] --> A2["#FF8FB1\n(Pink Accent - 100%)"]
    end
```

### 4.1. Gradient Chính (Primary Gradient)
- **Mã màu**: `#1E63B7` (0%) ➔ `#6EC1F6` (50%) ➔ `#2FB29A` (100%)
- **CSS Code**:
  ```css
  background: linear-gradient(90deg, #1E63B7 0%, #6EC1F6 50%, #2FB29A 100%);
  ```
- **Tailwind Utility**:
  ```html
  <div class="bg-gradient-to-r from-[#1E63B7] via-[#6EC1F6] to-[#2FB29A] text-white">
    Lotus Fin Key Visual
  </div>
  ```
- **Phạm vi sử dụng**: Banner chính, Hero section, thanh tiêu đề của Lotus Copilot, dải màu gradient trên cánh hoa sen.

### 4.2. Gradient Bổ trợ (Accent Gradient)
- **Mã màu**: `#FFDDE7` (0%) ➔ `#FF8FB1` (100%)
- **CSS Code**:
  ```css
  background: linear-gradient(90deg, #FFDDE7 0%, #FF8FB1 100%);
  ```
- **Tailwind Utility**:
  ```html
  <button class="bg-gradient-to-r from-[#FFDDE7] to-[#FF8FB1] text-gray-900 font-semibold shadow-sm">
    AI Quick Action
  </button>
  ```
- **Phạm vi sử dụng**: Nút tương tác nhanh (CTA nổi bật), điểm nhấn thông báo, nụ sen trên đỉnh logo.

### 4.3. Overlay Gradient (Tạo chiều sâu cho Layout)
- **CSS Code**:
  ```css
  background: linear-gradient(180deg, rgba(232, 242, 251, 0.7) 0%, rgba(255, 255, 255, 0) 100%);
  ```
- **Phạm vi sử dụng**: Phủ mờ nhẹ nhàng ở đầu các trang danh sách / báo cáo giúp tạo chiều sâu thị giác thanh thoát.

---

## 🔤 5. Kiểu chữ & Font Chữ Quy chuẩn (Typography)

- **Font chữ giao diện chính**: `Satoshi`, `Inter`, `-apple-system`, `sans-serif`
- **Font số liệu / Code**: `JetBrains Mono`, `Fira Code`, `monospace`
- **Quy cách thể hiện Logotype**:
  - `LOTUS`: Font Sans-serif viết hoa, độ đậm **Bold / Heavy** (900), màu `#1E63B7`.
  - `FIN`: Font Sans-serif viết hoa, độ đậm **Bold nghiêng (Italic)**, màu `#2FB29A`.
  - `INTELLIGENCE IN BLOOM`: Font Sans-serif viết hoa, giãn khoảng cách ký tự rộng (`letter-spacing: 0.25em`), màu `#39C6B7`.

---

## 💻 6. Cấu hình Tailwind CSS Khuyên dùng (`tailwind.config.js`)

Để sử dụng trực tiếp các token màu của Lotus Fin trong source code:

```javascript
module.exports = {
  theme: {
    extend: {
      colors: {
        lotus: {
          blue: "#1E63B7",
          "blue-light": "#6EC1F6",
          teal: "#39C6B7",
          mint: "#2FB29A",
          pink: "#FF8FB1",
          "pink-light": "#FFDDE7",
          "text-primary": "#2E3A59",
          "text-secondary": "#8FA1B3",
          bg: "#E8F2FB",
        },
      },
      backgroundImage: {
        "lotus-gradient": "linear-gradient(90deg, #1E63B7 0%, #6EC1F6 50%, #2FB29A 100%)",
        "lotus-accent": "linear-gradient(90deg, #FFDDE7 0%, #FF8FB1 100%)",
      },
    },
  },
};
```

