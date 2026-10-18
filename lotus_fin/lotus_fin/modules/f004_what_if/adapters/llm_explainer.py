from typing import Optional
from decimal import Decimal
from lotus_fin.modules.f004_what_if.domain.models import ScenarioResult


class ScenarioExplainer:
    """
    Produces grounded, factual explanations for What-If scenario results.
    Strictly forbids inventing numbers (Zero Hallucination).
    """

    def explain(self, result: ScenarioResult) -> str:
        """
        Generates an authoritative, factual summary of the simulation vs baseline.
        """
        delta = result.delta_metrics
        sim = result.simulated_metrics
        base = result.baseline_metrics
        params = result.parameters

        lines = []
        lines.append(f"### Kết quả Mô phỏng Kịch bản: {result.scenario_name}")
        lines.append(f"- **Doanh nghiệp**: {result.company} | **Kỳ phân tích**: {result.horizon_days} ngày từ {result.as_of}")
        
        # 1. Tác động số dư
        closing_sign = "+" if delta.closing_cash_delta >= Decimal("0.00") else ""
        lines.append(f"- **Tiền cuối kỳ dự kiến**: ${sim.closing_cash:,.2f} USD (Biến động: {closing_sign}${delta.closing_cash_delta:,.2f} USD so với cơ sở).")
        
        # 2. Cảnh báo thâm hụt
        if delta.new_shortfall_introduced:
            lines.append(f"⚠️ **CẢNH BÁO RỦI RO THANH KHOẢN MỚI**: Kịch bản này làm xuất hiện tình trạng thâm hụt tiền mặt từ ngày **{sim.first_shortfall_date}**, mức thâm hụt sâu nhất đạt **${sim.minimum_cash:,.2f} USD**.")
            lines.append(f"- **Thời gian an toàn (Runway)**: Giảm {abs(delta.runway_delta_days)} ngày (từ {base.runway_days} ngày xuống còn {sim.runway_days} ngày).")
        elif sim.has_shortfall:
            lines.append(f"⚠️ **Duy trì cảnh báo thiếu hụt**: Dòng tiền tiếp tục âm từ ngày **{sim.first_shortfall_date}**, mức tiền thấp nhất là **${sim.minimum_cash:,.2f} USD**.")
        else:
            lines.append("✅ **An toàn thanh khoản**: Doanh nghiệp duy trì dòng tiền dương trong toàn bộ chu kỳ mô phỏng.")

        # 3. Tổng hợp biến đổi
        if result.applied_modifier_descriptions:
            lines.append("\n**Các giả định đã áp dụng:**")
            for desc in result.applied_modifier_descriptions:
                lines.append(f"  • {desc}")

        return "\n".join(lines)
