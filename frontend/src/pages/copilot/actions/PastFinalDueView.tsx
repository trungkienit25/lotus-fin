import React from "react";
import { PastFinalDueResponseVm, PastFinalDueItemVm } from "./pastFinalDueTypes";

interface PastFinalDueViewProps {
  data: PastFinalDueResponseVm;
  onSelectInvoice?: (item: PastFinalDueItemVm) => void;
  onRefresh?: () => void;
}

export const PastFinalDueView: React.FC<PastFinalDueViewProps> = ({
  data,
  onSelectInvoice,
  onRefresh,
}) => {
  const isDemo = data.providerMode === "DEMO";
  const isCore = data.providerMode === "CORE";
  const isPartial = !data.coverage.complete;

  return (
    <div className="past-final-due-container" style={{ padding: 16, fontFamily: "sans-serif" }}>
      {/* Header and Isolation Badges */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
        <div>
          <h3 style={{ margin: 0, fontSize: 18, fontWeight: 600 }}>
            Hóa đơn đã qua hạn cuối còn dư nợ (Past-Final-Due)
          </h3>
          <span style={{ fontSize: 12, color: "#666" }}>
            Site Date: {data.siteLocalDate} ({data.siteTimezone}) | Scope: {data.authorizedScope}
          </span>
        </div>
        <div style={{ display: "flex", gap: 8 }}>
          {isDemo && (
            <span
              style={{
                backgroundColor: "#e0e7ff",
                color: "#3730a3",
                padding: "4px 8px",
                borderRadius: 4,
                fontSize: 12,
                fontWeight: 600,
              }}
            >
              DEMO DATA (FICTIONAL)
            </span>
          )}
          {isCore && (
            <span
              style={{
                backgroundColor: "#fee2e2",
                color: "#991b1b",
                padding: "4px 8px",
                borderRadius: 4,
                fontSize: 12,
                fontWeight: 600,
              }}
            >
              NATIVE SOURCE NOT CONFIGURED
            </span>
          )}
          {isPartial && (
            <span
              style={{
                backgroundColor: "#fef3c7",
                color: "#92400e",
                padding: "4px 8px",
                borderRadius: 4,
                fontSize: 12,
                fontWeight: 600,
              }}
            >
              PARTIAL COVERAGE
            </span>
          )}
        </div>
      </div>

      {/* Limitations Warning */}
      {data.limitations && data.limitations.length > 0 && (
        <div
          style={{
            backgroundColor: "#fffbeb",
            border: "1px solid #fef3c7",
            padding: 8,
            borderRadius: 4,
            marginBottom: 12,
            fontSize: 12,
            color: "#b45309",
          }}
        >
          <strong>Limitations:</strong> {data.limitations.join(", ")}
        </div>
      )}

      {/* Invoice Table */}
      {data.items.length === 0 ? (
        <div style={{ padding: 24, textAlign: "center", color: "#888", border: "1px dashed #ccc", borderRadius: 4 }}>
          {isCore ? "Native source adapter is not configured. No data available." : "Không tìm thấy hóa đơn quá hạn thỏa mãn điều kiện."}
        </div>
      ) : (
        <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13, textAlign: "left" }}>
          <thead>
            <tr style={{ borderBottom: "2px solid #eee", backgroundColor: "#f9fafb" }}>
              <th style={{ padding: "8px 12px" }}>Invoice ID</th>
              <th style={{ padding: "8px 12px" }}>Hạn cuối (Final Due)</th>
              <th style={{ padding: "8px 12px" }}>Số ngày quá hạn</th>
              <th style={{ padding: "8px 12px", textAlign: "right" }}>Dư nợ hiện tại (Residual)</th>
              <th style={{ padding: "8px 12px" }}>Loại tiền</th>
              <th style={{ padding: "8px 12px", textAlign: "center" }}>Hành động</th>
            </tr>
          </thead>
          <tbody>
            {data.items.map((item) => (
              <tr key={item.invoiceId} style={{ borderBottom: "1px solid #f3f4f6" }}>
                <td style={{ padding: "8px 12px", fontWeight: 500 }}>{item.invoiceId}</td>
                <td style={{ padding: "8px 12px" }}>{item.finalDueDate}</td>
                <td style={{ padding: "8px 12px", color: "#dc2626", fontWeight: 600 }}>
                  +{item.overdueDays} ngày
                </td>
                <td style={{ padding: "8px 12px", textAlign: "right", fontFamily: "monospace" }}>
                  {item.currentOutstandingDecimal}
                </td>
                <td style={{ padding: "8px 12px" }}>{item.partyAccountCurrency}</td>
                <td style={{ padding: "8px 12px", textAlign: "center" }}>
                  <button
                    disabled={!item.selectionRef}
                    onClick={() => onSelectInvoice && onSelectInvoice(item)}
                    style={{
                      padding: "4px 8px",
                      borderRadius: 4,
                      border: "1px solid #d1d5db",
                      backgroundColor: item.selectionRef ? "#2563eb" : "#e5e7eb",
                      color: item.selectionRef ? "#fff" : "#9ca3af",
                      cursor: item.selectionRef ? "pointer" : "not-allowed",
                      fontSize: 12,
                    }}
                  >
                    {item.selectionRef ? "Xem chi tiết" : "Chưa xác thực"}
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {/* Footer & Freshness */}
      <div style={{ marginTop: 12, display: "flex", justifyContent: "space-between", fontSize: 11, color: "#9ca3af" }}>
        <span>
          Scanned: {data.coverage.scannedRows} | Returned: {data.coverage.returnedRows} | Observed: {data.observedAtUtc}
        </span>
        {onRefresh && (
          <button
            onClick={onRefresh}
            style={{ background: "none", border: "none", color: "#2563eb", cursor: "pointer", fontSize: 11 }}
          >
            Làm mới (Fresh Authorization)
          </button>
        )}
      </div>
    </div>
  );
};
