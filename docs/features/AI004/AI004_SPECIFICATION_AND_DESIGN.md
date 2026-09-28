# AI-F004 — WHAT-IF SCENARIO AGENT SPECIFICATION & DESIGN

> **Version:** 1.0.0  
> **Status:** Approved Architecture & Implementation  
> **Feature Code:** `AI-F004`  
> **Computation Class:** `deterministic_simulation` + `llm_explanation` (Hybrid)  
> **Invariants Enforced:** Zero DB Mutation, Strict Decimal Arithmetic, `data_mode = "simulation"`  

---

## 1. Mục Tiêu & Phạm Vi (Scope)

`AI-F004` cung cấp năng lực mô phỏng giả lập các tình huống tài chính ("What-If Scenarios") cho doanh nghiệp vừa và nhỏ (SME).

Doanh nghiệp có thể đặt các câu hỏi giả định dạng:
1. **Sốc Doanh Thu (Sales Shock)**: *"Nếu doanh thu quý tới giảm 20% thì sao?"*
2. **Trễ Hạn Thu Tiền (Collection Delay)**: *"Nếu khách hàng thanh toán trễ trung bình 15 ngày thì dòng tiền có bị âm không?"*
3. **Dãn Hạn Nợ Nhà Cung Cấp (Payable Shift)**: *"Nếu thương lượng lùi ngày trả nợ nhà cung cấp thêm 30 ngày thì cải thiện được bao nhiêu tiền mặt?"*
4. **Cú Sốc Chi Phí (Expense Shock)**: *"Nếu chi phí lương tăng 10% hoặc phát sinh chi phí đột xuất 50 triệu thì doanh nghiệp còn đủ tiền hoạt động trong bao lâu?"*
5. **Bơm Vốn Tài Trợ (Financing Injection)**: *"Nếu vay được 200 triệu vào ngày 15 tháng này thì có vượt qua được đợt thiếu hụt tiền không?"*

---

## 2. Các Quy Tắc Bất Biến (Safety Invariants)

| Invariant Code | Quy Tắc |
| :--- | :--- |
| **`INV-SIM-01` (Zero Mutation)** | Mọi phép tính mô phỏng chỉ diễn ra trên bộ nhớ (In-Memory). Tuyệt đối **không được ghi đè, tạo mới hoặc sửa đổi bất kỳ chứng từ thật nào trong cơ sở dữ liệu**. |
| **`INV-SIM-02` (Simulation Stamping)** | Mọi output của mô phỏng (từ Entity, DTO, API response cho đến giao diện) đều phải mang cờ `data_mode = "simulation"`. |
| **`INV-SIM-03` (Deterministic Math)** | Tất cả các phép biến đổi số tiền, tỷ lệ phần trăm và dòng tiền chạy bằng **Python `Decimal`**, không dùng `float`. Không để LLM tính toán số học. |
| **`INV-SIM-04` (Isolated Baseline)** | Baseline (kịch bản cơ sở) được đọc ở chế độ Read-Only và giữ nguyên vẹn để làm mốc đối chứng (Delta calculation). |

---

## 3. Bản Hợp Đồng Dữ Liệu (Data Contracts)

### A. Input: `ScenarioParameters`
```json
{
  "scenario_name": "Sales Drop 20% and 15 Days Delay",
  "company": "Lotus-fin",
  "as_of": "2026-01-01",
  "horizon_days": 30,
  "sales_change_pct": "-0.20",
  "collection_delay_days": 15,
  "supplier_due_shift_days": 0,
  "payroll_change_pct": "0.00",
  "opex_change_pct": "0.00",
  "one_off_expense": "0.00",
  "one_off_expense_date": null,
  "financing_amount": "0.00",
  "financing_date": null
}
```

### B. Output: `ScenarioResult`
```json
{
  "scenario_id": "SCEN-2026-001",
  "company": "Lotus-fin",
  "data_mode": "simulation",
  "as_of": "2026-01-01",
  "horizon_days": 30,
  "baseline_metrics": {
    "opening_cash": "50000000.00",
    "closing_cash": "30000000.00",
    "minimum_cash": "20000000.00",
    "has_shortfall": false,
    "runway_days": 30
  },
  "simulated_metrics": {
    "opening_cash": "50000000.00",
    "closing_cash": "5000000.00",
    "minimum_cash": "-15000000.00",
    "has_shortfall": true,
    "first_shortfall_date": "2026-01-18",
    "runway_days": 18
  },
  "delta_metrics": {
    "closing_cash_delta": "-25000000.00",
    "minimum_cash_delta": "-35000000.00",
    "runway_delta_days": -12,
    "shortfall_worsened": true
  },
  "applied_modifiers": [
    "SalesModifier(sales_change_pct=-0.20)",
    "CollectionModifier(collection_delay_days=15)"
  ],
  "narrative_explanation": "Kịch bản giảm 20% doanh thu và thu tiền trễ 15 ngày khiến dòng tiền bị âm 15.000.000 VND từ ngày 18/01/2026, làm giảm 12 ngày runway so với kịch bản cơ sở."
}
```
