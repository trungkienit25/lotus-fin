from lotus_fin.infrastructure.tool.registry.tool_registry import ToolRegistry
from lotus_fin.infrastructure.tool.impl.f001_health_tool import GetFinancialHealthTool
from lotus_fin.infrastructure.tool.impl.f002_cashflow_tool import GetCashflowForecastTool
from lotus_fin.infrastructure.tool.impl.f003_risk_tool import EvaluateRiskSignalTool
from lotus_fin.infrastructure.tool.impl.f004_whatif_tool import SimulateWhatIfTool
from lotus_fin.infrastructure.tool.impl.f005_financing_tool import MatchFinancingProductsTool
from lotus_fin.infrastructure.tool.impl.f006_repayment_tool import CalculateRepaymentScheduleTool


def create_default_tool_registry() -> ToolRegistry:
    registry = ToolRegistry()
    registry.register(GetFinancialHealthTool())
    registry.register(GetCashflowForecastTool())
    registry.register(EvaluateRiskSignalTool())
    registry.register(SimulateWhatIfTool())
    registry.register(MatchFinancingProductsTool())
    registry.register(CalculateRepaymentScheduleTool())
    return registry
