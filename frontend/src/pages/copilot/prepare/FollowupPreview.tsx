import React, { useEffect, useState, useMemo } from "react";
import { FollowupPreviewController, type ControllerState, type ControllerOptions } from "./followupPreviewController.ts";
import { type PrepareRequest } from "./followupPreview.ts";

export interface FollowupPreviewProps {
  controllerOptions?: Partial<ControllerOptions>;
  scopeEpoch: string;
  onPrepareTask?: (body: string) => void;
}

const DEFAULT_REQ: PrepareRequest = {
  contract_version: "l3.followup.local.v0.1",
  capability: "followup.prepare_text",
  template_id: "followup.neutral.vi.v1",
  locale: "vi-VN",
};

export const FollowupPreview: React.FC<FollowupPreviewProps> = ({ controllerOptions, scopeEpoch, onPrepareTask }) => {
  const controller = useMemo(
    () => new FollowupPreviewController({ ...controllerOptions, scopeEpoch }),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    []
  );

  const [state, setState] = useState<ControllerState>(() => controller.getState());
  const [localText, setLocalText] = useState<string>(state.body);

  useEffect(() => {
    controller.setScopeEpoch(scopeEpoch);
  }, [controller, scopeEpoch]);

  useEffect(() => {
    const unsubscribe = controller.subscribe((next) => {
      setState(next);
      setLocalText(next.body);
    });

    const timer = setInterval(() => {
      controller.checkExpiry();
    }, 500);

    const onVisibilityChange = () => {
      if (typeof document !== "undefined" && !document.hidden) {
        controller.checkExpiry();
      }
    };
    if (typeof document !== "undefined") {
      document.addEventListener("visibilitychange", onVisibilityChange);
    }

    return () => {
      clearInterval(timer);
      if (typeof document !== "undefined") {
        document.removeEventListener("visibilitychange", onVisibilityChange);
      }
      unsubscribe();
      controller.dispose();
      setLocalText("");
    };
  }, [controller]);

  const isCopyDisabled = !state.isReviewed || state.lifecycle !== "REVIEWED" || state.isCopying;

  return (
    <div className="p-5 border border-slate-200/80 rounded-2xl bg-white shadow-xs max-w-2xl mx-auto space-y-4 font-sans text-slate-800" data-testid="followup-preview-container">
      <div className="border-b border-slate-100 pb-3">
        <h3 className="text-base font-bold text-slate-900 tracking-tight" id="preview-heading">
          Soạn thảo Thư nhắc nợ & Đối soát công nợ
        </h3>
        <p className="text-xs text-amber-800 bg-amber-50/80 border border-amber-200/60 p-2 rounded-xl mt-1.5 flex items-center gap-1.5" role="note">
          <span>ℹ️</span>
          <span>Bản nháp được lưu giữ cục bộ trên trình duyệt. Hệ thống không tự động gửi hoặc can thiệp dữ liệu hạch toán.</span>
        </p>
      </div>

      {state.lifecycle === "EMPTY" && (
        <div className="py-8 text-center space-y-3">
          <p className="text-xs text-slate-500">Chưa có nội dung nhắc nợ nào được tạo.</p>
          <button
            type="button"
            onClick={() => controller.prepare(DEFAULT_REQ)}
            data-testid="btn-prepare"
            className="px-4 py-2 bg-blue-600 text-white text-xs font-bold rounded-xl hover:bg-blue-700 shadow-2xs transition-all cursor-pointer"
          >
            ✦ Tạo bản nháp thư nhắc nợ
          </button>
          {state.errorMessage && (
            <div className="text-xs text-rose-700 bg-rose-50 p-2.5 rounded-xl border border-rose-200" role="alert" data-testid="error-message">
              {state.errorMessage}
            </div>
          )}
        </div>
      )}

      {state.lifecycle === "EXPIRED" && (
        <div className="space-y-3">
          <div className="p-3 bg-rose-50 text-rose-700 text-xs rounded-xl border border-rose-200" role="alert" data-testid="alert-expired">
            {state.errorMessage || "Bản nháp đã hết hạn hiệu lực (10 phút). Vui lòng tạo lại."}
          </div>
          <div className="text-center">
            <button
              type="button"
              onClick={() => controller.prepare(DEFAULT_REQ)}
              data-testid="btn-prepare"
              className="px-4 py-2 bg-blue-600 text-white text-xs font-bold rounded-xl hover:bg-blue-700 shadow-2xs transition-all cursor-pointer"
            >
              ✦ Tạo lại bản nháp
            </button>
          </div>
        </div>
      )}

      {(state.lifecycle === "EDITABLE" || state.lifecycle === "REVIEWED") && (
        <div className="space-y-3.5">
          <div className="flex items-center justify-between text-xs">
            <span
              className={`font-semibold text-[10px] px-2.5 py-1 rounded-full border ${
                state.provenance === "SUGGESTED"
                  ? "bg-blue-50 text-blue-700 border-blue-200"
                  : "bg-purple-50 text-purple-700 border-purple-200"
              }`}
              data-testid="provenance-badge"
            >
              Nguồn: {state.provenance === "SUGGESTED" ? "Gợi ý tự động" : "Người dùng chỉnh sửa"}
            </span>
            <button
              type="button"
              onClick={() => controller.resetTemplate()}
              data-testid="btn-reset-template"
              className="text-[11px] text-blue-600 hover:text-blue-700 font-medium cursor-pointer"
            >
              ↺ Đặt lại mẫu mặc định
            </button>
          </div>

          <div>
            <label htmlFor="followup-preview-textarea" className="block text-[11px] font-bold uppercase tracking-wider text-slate-600 mb-1.5">
              Nội dung thông báo đối soát:
            </label>
            <textarea
              id="followup-preview-textarea"
              value={localText}
              onChange={(e) => {
                setLocalText(e.target.value);
                controller.updateBody(e.target.value);
              }}
              rows={6}
              data-testid="preview-textarea"
              aria-labelledby="preview-heading"
              className="w-full p-3.5 text-xs border border-slate-200 rounded-xl bg-[#F9FBFC] focus:ring-2 focus:ring-[#1E63B7]/20 focus:border-[#1E63B7] outline-none resize-none font-sans leading-relaxed text-slate-800 transition-all"
              placeholder="Nhập nội dung nhắc nợ..."
            />
          </div>

          <div className="flex items-center gap-2.5 p-3 rounded-xl bg-slate-50 border border-slate-200/60">
            <input
              type="checkbox"
              id="review-checkbox"
              checked={state.isReviewed}
              onChange={(e) => controller.setReviewed(e.target.checked)}
              data-testid="checkbox-review"
              className="h-4 w-4 text-blue-600 focus:ring-[#1E63B7] border-slate-300 rounded cursor-pointer"
            />
            <label htmlFor="review-checkbox" className="text-xs font-semibold text-slate-700 cursor-pointer select-none">
              Tôi đã kiểm tra kỹ lưỡng nội dung trước khi sử dụng
            </label>
          </div>

          {state.errorMessage && (
            <div className="text-xs text-rose-700 bg-rose-50 p-2.5 rounded-xl border border-rose-200" role="alert" data-testid="error-message">
              {state.errorMessage}
            </div>
          )}
          {state.lastActionStatus === "COPIED" && (
            <div className="text-xs text-emerald-800 bg-emerald-50 p-2.5 rounded-xl border border-emerald-200" role="status" data-testid="notice-copied">
              ✓ Đã sao chép nội dung vào bộ nhớ tạm thành công.
            </div>
          )}
          {state.lastActionStatus === "COPY_FAILED" && (
            <div className="text-xs text-rose-700 bg-rose-50 p-2.5 rounded-xl border border-rose-200" role="alert" data-testid="notice-copy-failed">
              Sao chép thất bại. Vui lòng cấp quyền clipboard hoặc bôi đen văn bản để sao chép.
            </div>
          )}

          <div className="flex flex-wrap items-center justify-end gap-2 pt-3 border-t border-slate-100">
            {onPrepareTask && (
              <button
                type="button"
                disabled={isCopyDisabled}
                onClick={() => {
                  if (!controller.checkExpiry() && controller.getState().isReviewed) {
                    onPrepareTask(controller.getState().body);
                  }
                }}
                className="px-3.5 py-2 rounded-xl text-xs font-bold border border-blue-200 bg-blue-50 text-blue-700 hover:bg-blue-100 transition-all cursor-pointer disabled:opacity-50"
              >
                ✦ Tạo đề xuất Task (L4)
              </button>
            )}
            <button
              type="button"
              onClick={() => {
                controller.discard();
                setLocalText("");
              }}
              data-testid="btn-discard"
              className="px-3.5 py-2 text-xs font-bold text-slate-600 bg-slate-100 hover:bg-slate-200 rounded-xl transition-all cursor-pointer"
            >
              Hủy bỏ
            </button>
            <button
              type="button"
              onClick={() => controller.copy()}
              disabled={isCopyDisabled}
              data-testid="btn-copy"
              className={`px-4 py-2 text-xs font-bold text-white rounded-xl shadow-2xs transition-all ${
                isCopyDisabled
                  ? "bg-slate-300 text-slate-500 cursor-not-allowed"
                  : "bg-blue-600 hover:bg-blue-700 cursor-pointer"
              }`}
            >
              {state.isCopying ? "Đang sao chép..." : "Sao chép thư 📋"}
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
