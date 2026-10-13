# Lotus Fin — Module AI006: Deterministic Repayment Schedule & Financial Stress Testing Engine


---

## 1. Vai trò của AI & Engine trong Phân hệ `AI-F006` Repayment & Stress Simulation

Theo kiến trúc cốt lõi của Lotus Fin, phân hệ **AI006** chịu trách nhiệm tính toán dòng tiền trả nợ tất định và đánh giá sức chống chịu tài chính của doanh nghiệp SME trước các cú sốc thị trường:

1. **Deterministic Multi-Method Amortization (Lập lịch trả nợ tất định đa phương pháp):**
   * Tính toán chi tiết từng kỳ trả nợ (gốc, lãi, số dư đầu/cuối kỳ, lũy kế) theo 4 chuẩn tài chính ngân hàng:
     - `EQUAL_INSTALLMENT`: Trả góp đều (PMT).
     - `EQUAL_PRINCIPAL`: Trả gốc đều, tiền lãi giảm dần theo dư nợ thực tế.
     - `FLAT_RATE`: Lãi phẳng tính trên gốc ban đầu.
     - `BULLET`: Trả lãi định kỳ, gốc tất toán toàn bộ ở kỳ cuối cùng.
   * Hỗ trợ thời gian ân hạn gốc (`grace_period_months`) và cơ cấu phí xử lý hồ sơ/bảo hiểm (`UPFRONT` hoặc `SPREAD`).

2. **Comprehensive Financial Stress Testing (Kiểm tra sức chịu đựng tài chính):**
   * Cho phép doanh nghiệp chạy giả lập 5 kịch bản rủi ro để chuẩn bị dòng tiền dự phòng:
     - **Rate Shock (+bps):** Mô phỏng rủi ro lãi suất thả nổi tăng vọt (ví dụ +200 bps = +2%/năm).
     - **Term Extension (+tháng):** Mô phỏng giãn nợ để giảm áp lực dòng tiền hàng tháng.
     - **Early Repayment:** Mô phỏng tất toán trước hạn tại kỳ thứ $t$ kèm phí phạt tất toán sớm.
     - **Grace Period Injection:** Đưa thêm kỳ ân hạn gốc vào khoản vay hiện hữu.
     - **Combined:** Phối hợp đồng thời nhiều cú sốc thị trường.

3. **Grounded AI Advisor & Narrative Explanation (Cố vấn AI có căn cứ):**
   * Tự động trích xuất các chỉ số Delta thay đổi giữa kịch bản gốc và kịch bản stress (`Total Interest`, `Total Payment`, `Average Monthly Payment`).
   * Phân loại đánh giá tác động định tính: `ADVERSE` (bất lợi 🔴), `FAVORABLE` (thuận lợi 🟢), `NEUTRAL` (trung lập ⚪).
   * Đưa ra khuyến nghị an toàn dòng tiền mà **tuyệt đối không bịa số liệu** (Zero Hallucination).

4. **Strict Decimal Precision & Invariant Compliance:**
   * Sử dụng kiểu `Decimal` với độ chính xác `Decimal("0.01")` và quy tắc `ROUND_HALF_UP` cho toàn bộ phép tính tài chính.
   * Tự động cân bằng sai số làm tròn ở kỳ cuối cùng để số dư nợ đóng kỳ (`closing_balance`) về chính xác `0.00`.
   * Mọi dữ liệu xuất ra luôn gắn cờ `data_mode = 'simulation'` và tuân thủ `R4/R5 bank-write = OFF` (không sinh bút toán tự ý vào General Ledger của ERPNext).

---

## 2. Sơ đồ Luồng Xử lý Lập Lịch Trả Nợ & Stress Test

```mermaid
sequenceDiagram
    autonumber
    actor User as 👤 SME CFO / Accountant
    participant API as 🌐 Frappe REST API / SDK
    participant RepayEngine as ⚙️ Deterministic Repayment Engine
    participant StressEngine as ⚡ Stress Simulation Engine
    participant Advisor as 🧠 Grounded AI Advisor

    alt Luồng 1: Lập lịch trả nợ cơ sở (Base Schedule)
        User->>API: calculate_repayment_schedule(terms)
        API->>RepayEngine: calculate_schedule(LoanTerms)
        RepayEngine->>RepayEngine: Tính gốc/lãi từng kỳ (PMT / Gốc đều / Bullet)
        RepayEngine->>RepayEngine: Xử lý ân hạn gốc & cân đối số dư kỳ cuối = 0.00
        RepayEngine-->>Advisor: RepaymentScheduleResult
        Advisor->>Advisor: Tổng hợp giải thích số liệu & lưu ý
        Advisor-->>User: Lịch trả nợ chi tiết + AI Narrative
    else Luồng 2: Kiểm tra sức chịu đựng (Stress Test)
        User->>API: run_stress_test(base_terms, stress_params)
        API->>StressEngine: run_stress_test(base_terms, stress_params)
        StressEngine->>RepayEngine: 1. Tính Base Schedule
        StressEngine->>StressEngine: 2. Áp dụng Stress (Lãi suất shock / Kéo dài kỳ / Trả sớm)
        StressEngine->>RepayEngine: 3. Tính Stressed Schedule
        StressEngine->>StressEngine: 4. So sánh Delta KPIs & Đánh giá rủi ro
        StressEngine-->>Advisor: StressTestResult
        Advisor->>Advisor: Sinh báo cáo phân tích biến động & khuyến nghị dự phòng
        Advisor-->>User: Bảng so sánh Delta KPIs + AI Risk Assessment
    end
```

---

## 3. Kiến trúc Nghiệp vụ & Phương pháp Phân bổ Nợ

### 3.1. Sơ đồ Cấu trúc Thành phần Module

```mermaid
flowchart TD
    subgraph Inputs["1. Dữ liệu Đầu vào"]
        LT["LoanTerms: Gốc, Lãi suất, Kỳ hạn, Phương pháp, Ân hạn, Phí"]
        SP["StressScenarioParams: Loại stress, Rate shock bps, Tháng trả sớm, Phí phạt"]
    end

    subgraph Core_Engines["2. Bộ máy Tính toán Tất định (Decimal Engine)"]
        RE["RepaymentEngine: Bộ máy tính lịch trả nợ"]
        SE["StressSimulationEngine: Bộ máy kiểm tra sức chịu đựng"]
        
        M1["EQUAL_INSTALLMENT (Trả góp đều)"]
        M2["EQUAL_PRINCIPAL (Gốc đều, lãi giảm dần)"]
        M3["FLAT_RATE (Lãi phẳng trên gốc ban đầu)"]
        M4["BULLET (Lãi hàng kỳ, gốc cuối kỳ)"]

        RE --> M1
        RE --> M2
        RE --> M3
        RE --> M4
        SE --> RE
    end

    subgraph AI_Advisor["3. Tầng Cố vấn Trí tuệ Nhân tạo (Grounded AI)"]
        Adv["RepaymentAdvisor: Giải thích có căn cứ"]
        Rec["Đánh giá Rủi ro (ADVERSE / FAVORABLE) + Khuyến nghị"]
        Adv --> Rec
    end

    subgraph Outputs["4. Kết quả Mô phỏng (data_mode = 'simulation')"]
        Out1["RepaymentScheduleResult: Lịch chi tiết từng kỳ + Báo cáo Dòng tiền"]
        Out2["StressTestResult: So sánh Delta Lãi/Phí + Khuyến nghị rủi ro"]
    end

    LT --> RE
    RE --> Out1
    Out1 --> Adv

    LT --> SE
    SP --> SE
    SE --> Out2
    Out2 --> Adv
```

### 3.2. Bảng So sánh 4 Phương pháp Phân bổ Nợ

| Phương pháp | Công thức Tính toán | Đặc điểm Dòng tiền Doanh nghiệp | Trường hợp Áp dụng |
| :--- | :--- | :--- | :--- |
| **`EQUAL_INSTALLMENT`** *(Trả góp đều / PMT)* | \( PMT = P \times \frac{r(1+r)^n}{(1+r)^n - 1} \)<br>Gốc tăng dần, lãi giảm dần, tổng trả cố định mỗi kỳ. | Dòng tiền chi trả hàng tháng ổn định, dễ lập kế hoạch tài chính. | Vay trung/dài hạn mua máy móc, xe tải, mở rộng kinh doanh. |
| **`EQUAL_PRINCIPAL`** *(Gốc đều, lãi giảm dần)* | \( \text{Gốc kỳ} = P / n \)<br>\( \text{Lãi kỳ} = \text{Dư nợ đầu kỳ} \times r \) | Áp lực trả nợ nặng ở các tháng đầu, sau đó giảm dần theo thời gian. | Doanh nghiệp có nguồn thu lớn ngay sau giải ngân. |
| **`FLAT_RATE`** *(Lãi phẳng)* | \( \text{Gốc kỳ} = P / n \)<br>\( \text{Lãi kỳ} = P \times \frac{r_{\text{năm}}}{\text{số kỳ/năm}} \) | Lãi tính đều trên gốc ban đầu suốt kỳ; tổng lãi thực tế cao hơn PMT. | Vay tín chấp tiểu thương hoặc các gói tín dụng vi mô. |
| **`BULLET`** *(Lãi định kỳ, gốc cuối kỳ)* | Kỳ 1 đến n-1: Gốc = 0, Lãi = \( P \times r \)<br>Kỳ n: Gốc = P, Lãi = \( P \times r \) | Áp lực trả hàng tháng rất nhẹ, nhưng phải tích lũy dòng tiền để trả gốc cuối kỳ. | Vay bổ sung vốn lưu động xoay vòng theo mùa vụ/hợp đồng dự án. |

---

## 4. Cấu trúc Thư mục Module `AI006`

```
lotus_fin/lotus_fin/AI006/
├── __init__.py           # Package interfaces & Canonical alias exports
├── models.py             # Data models, Enums (LoanTerms, StressScenarioParams, StressComparisonKPI)
├── engine.py             # Deterministic Repayment Engine (4 phương pháp phân bổ, xử lý làm tròn Decimal)
├── stress.py             # Stress Simulation Engine (5 kịch bản rủi ro, so sánh delta KPIs)
├── ai_advisor.py         # Grounded AI Advisor sinh giải thích tài chính không bịa số
├── service.py            # Service Layer & Frappe Whitelisted REST Endpoints
├── test_ai006.py         # Unit test suites kiểm chứng độ chính xác toán học
└── README.md             # Tài liệu đặc tả kiến trúc và hướng dẫn
```

---

## 5. Hướng dẫn Sử dụng

### 5.1. Sử dụng qua Python SDK

```python
from decimal import Decimal
from lotus_fin.AI006 import (
    LoanTerms, 
    RepaymentEngine, 
    AmortizationMethod,
    StressScenarioParams,
    StressSimulationEngine,
    StressType,
    RepaymentAdvisor
)

# 1. Tính toán lịch trả nợ cơ sở (Base Schedule)
terms = LoanTerms(
    principal=Decimal("1000000000"),          # 1 Tỷ VND
    annual_rate=Decimal("0.10"),              # 10%/năm
    term_months=12,                           # 12 tháng
    amortization_method=AmortizationMethod.EQUAL_INSTALLMENT
)
engine = RepaymentEngine()
result = engine.calculate_schedule(terms)

print(f"Tổng lãi dự kiến: {result.summary['total_interest']:,.0f} VND")
print(f"Trả hàng tháng (PMT): {result.summary['average_monthly_payment']:,.0f} VND")

# 2. Chạy bài kiểm tra sức chịu đựng (Stress Test: Lãi suất tăng +200 bps = 2%)
stress_engine = StressSimulationEngine()
stress_params = StressScenarioParams(
    stress_type=StressType.RATE_SHOCK,
    rate_shock_bps=200,                       # Tăng thêm 2%
    description="Kịch bản lãi suất thả nổi tăng 2% do thị trường thắt chặt"
)
stress_result = stress_engine.run_stress_test(terms, stress_params)

# 3. AI Advisor giải thích rủi ro
advisor = RepaymentAdvisor()
explanation = advisor.explain_stress_test(stress_result)
print("\n--- BÁO CÁO CỐ VẤN AI ---")
print(explanation["narrative"])
```

### 5.2. Gọi qua REST API (Frappe Whitelist)

* **Endpoint Lập lịch trả nợ:**
  `POST /api/method/lotus_fin.AI006.service.calculate_repayment_schedule`
  ```json
  {
    "principal": 1000000000,
    "annual_rate": 0.10,
    "term_months": 12,
    "amortization_method": "EQUAL_INSTALLMENT",
    "grace_period_months": 0,
    "processing_fee_pct": 0.01
  }
  ```

* **Endpoint Kiểm tra sức chịu đựng (Stress Test):**
  `POST /api/method/lotus_fin.AI006.service.run_stress_test`
  ```json
  {
    "principal": 1000000000,
    "annual_rate": 0.10,
    "term_months": 12,
    "stress_type": "RATE_SHOCK",
    "rate_shock_bps": 200,
    "amortization_method": "EQUAL_INSTALLMENT"
  }
  ```

---

## 6. Chạy Kiểm thử Tự động (Unit Tests)

```powershell
$env:PYTHONPATH="M:\lotus-fin-feature-kiennt-refactor-fe\lotus-fin-feature-kiennt-refactor-fe\lotus_fin"
python -m unittest lotus_fin.modules.f006_repayment.test_ai006
```
