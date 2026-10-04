# Lotus Fin AI — Frontend Architecture & Developer Component Guide

Tài liệu quy chuẩn phát triển Frontend cho dự án **Lotus Fin AI** theo hệ thống thiết kế **Google Material 3 DNA**.

---

## 1. Triết lý Thiết kế (The Google Material 3 DNA)

- **Surface & Depth:**
  - Nền ứng dụng luôn dùng `var(--lotus-surface-app)` (`#F8FAFC` - Slate-50).
  - Khối chứa/Container dùng Card `var(--lotus-surface-card)` (`#FFFFFF`) với bo góc lớn `rounded-2xl` (`border-radius: 20px`) kết hợp `shadow-sm` để tạo hiệu ứng bồng bềnh (float).
  - Viền phân tách dùng tông xám nhẹ `border border-slate-200` (`#E2E8F0`).
- **Shape Language:**
  - Tất cả Nút bấm, Status Chips, Quick Prompts bắt buộc sử dụng hình viên thuốc (`rounded-full` / `var(--lotus-radius-pill)`).
  - Form inputs bo góc `rounded-xl` (`12px`).
  - Nút bấm luôn có micro-interaction khi nhấp chuột (`active:scale-95`).
- **Màu sắc chuẩn Google:**
  - **Primary Action:** Google Blue `#2563EB` (hover: `#1D4ED8`).
  - **AI Magic Action:** Indigo / Purple `#6366F1` & gradient `#4f46e5` &rarr; `#7c3aed`.
  - **Secondary Action:** Nền trắng viền xám `#FFFFFF border border-slate-300 text-slate-700`.
- **Khoảng thở (Whitespace):**
  - Mặc định các Card dùng padding `p-6` (24px) hoặc `p-8` (32px).

---

## 2. Hệ thống Thư viện UI Primitives (`lotus_fin.ui.*`)

Mọi trang chức năng mới bắt buộc phải sử dụng các components sau thay vì viết DOM thô:

### 2.1. Nút bấm — `lotus_fin.ui.Button`
```javascript
const btn = new lotus_fin.ui.Button({
    label: "Tính toán Lịch Trả Nợ",
    variant: "primary", // 'primary' | 'secondary' | 'ai'
    size: "md",         // 'sm' | 'md' | 'lg'
    icon: "⚡",
    onClick: function(e, buttonInstance) {
        buttonInstance.set_loading(true, "Đang tính toán...");
        // Gọi API...
    }
});
btn.appendTo("#actions-container");
```

### 2.2. Khối thẻ — `lotus_fin.ui.Card`
```javascript
const card = new lotus_fin.ui.Card({
    title: "🎯 Thông số Khoản vay",
    subtitle: "Mô phỏng áp lực sốc lãi suất và lịch trả nợ PMT",
    badge: "AI-F006",
    content: $(`<div>Nội dung form hoặc biểu đồ...</div>`)
});
card.appendTo(this.page.main);
```

### 2.3. Thẻ Chỉ số KPI — `lotus_fin.ui.MetricCard`
```javascript
const kpiCard = new lotus_fin.ui.MetricCard({
    label: "Doanh thu Thuần",
    value: "363,000,000 VND",
    subtext: "So với cùng kỳ năm trước",
    delta: "+12.4%",
    deltaType: "positive", // 'positive' | 'negative' | 'neutral'
    valueColor: "primary"  // 'primary' | 'success' | 'warning' | 'danger'
});
kpiCard.appendTo("#kpi-grid");
```

### 2.4. Bảng biểu dữ liệu — `lotus_fin.ui.Table`
```javascript
const table = new lotus_fin.ui.Table({
    columns: [
        { key: "period", label: "Kỳ #", align: "center" },
        { key: "startBal", label: "Dư nợ đầu kỳ", align: "right", format: (v) => lotus_fin.core.format_currency(v) },
        { key: "principalPaid", label: "Tiền gốc", align: "right", format: (v) => lotus_fin.core.format_currency(v) },
        { key: "interest", label: "Tiền lãi", align: "right", format: (v) => lotus_fin.core.format_currency(v) },
        { key: "totalPayment", label: "Tổng trả / kỳ", align: "right", format: (v) => lotus_fin.core.format_currency(v) },
        { key: "endBal", label: "Dư nợ cuối kỳ", align: "right", format: (v) => lotus_fin.core.format_currency(v) }
    ],
    data: rows
});
table.appendTo("#table-container");
```

---

## 3. Hệ thống Business Widgets (`lotus_fin.widgets.*`)

- `lotus_fin.widgets.ChatCopilot`: Khung chat thông minh đa kênh 7 modules AI001-AI007.
- `lotus_fin.widgets.WhatIfStudio`: Bảng mô phỏng 9-KPI đa biến số.
- `lotus_fin.widgets.FinancingMatcher`: Giao diện duyệt gói vay ngân hàng SME.
- `lotus_fin.widgets.RepaymentCalculator`: Máy tính trả nợ gốc lãi và sốc lãi suất.
- `lotus_fin.widgets.RiskSignalMonitor`: Thẻ giám sát tín hiệu rủi ro nợ quá hạn.
- `lotus_fin.widgets.HealthSnapshot`: Thẻ tổng quan 4 góc sức khỏe tài chính.

---

## 4. Quy ước Đặt tên & File Structuring

1. Mỗi trang chức năng tương ứng 1 folder trong `lotus_fin/lotus_fin_ai/page/<page_name>/`:
   - `<page_name>.json`: Page Doctype standard definition.
   - `<page_name>.py`: Context controller (`context.no_cache = 1`).
   - `<page_name>.js`: Page client controller kế thừa UI Primitives.
2. Mọi API gọi về Frappe qua `lotus_fin.core.api.call("method_name", args)` dạng Promise sạch sẽ.
