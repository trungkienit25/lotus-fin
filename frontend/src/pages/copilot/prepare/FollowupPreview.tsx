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
    <div className="p-4 border border-gray-300 rounded-lg bg-white shadow-sm max-w-2xl mx-auto space-y-4" data-testid="followup-preview-container">
      <div className="border-b pb-2">
        <h3 className="text-base font-semibold text-gray-900" id="preview-heading">Bản nháp cục bộ — chưa lưu, chưa gửi</h3>
        <p className="text-xs text-amber-700 bg-amber-50 p-1.5 rounded mt-1" role="note">Nội dung gợi ý; chưa xác minh thông tin tài chính</p>
      </div>

      {state.lifecycle === "EMPTY" && (
        <div className="py-6 text-center space-y-3">
          <p className="text-sm text-gray-500">Chưa có bản xem trước nào được khởi tạo.</p>
          <button type="button" onClick={() => controller.prepare(DEFAULT_REQ)} data-testid="btn-prepare"
            className="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500">
            Tạo bản xem trước nhắc nhở
          </button>
          {state.errorMessage && (
            <div className="text-xs text-red-600 bg-red-50 p-2 rounded" role="alert" data-testid="error-message">
              {state.errorMessage}
            </div>
          )}
        </div>
      )}

      {state.lifecycle === "EXPIRED" && (
        <div className="space-y-3">
          <div className="p-3 bg-red-50 text-red-700 text-sm rounded" role="alert" data-testid="alert-expired">
            {state.errorMessage || "Bản xem trước đã hết hạn (10 phút)."}
          </div>
          <div className="text-center">
            <button type="button" onClick={() => controller.prepare(DEFAULT_REQ)} data-testid="btn-prepare"
              className="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500">
              Tạo bản xem trước nhắc nhở
            </button>
          </div>
        </div>
      )}

      {(state.lifecycle === "EDITABLE" || state.lifecycle === "REVIEWED") && (
        <div className="space-y-3">
          <div className="flex items-center justify-between text-xs">
            <span className={`font-mono px-2 py-0.5 rounded ${state.provenance === "SUGGESTED" ? "bg-blue-100 text-blue-800" : "bg-purple-100 text-purple-800"}`} data-testid="provenance-badge">
              Nguồn: {state.provenance === "SUGGESTED" ? "Gợi ý (SUGGESTED)" : "Người dùng nhập (USER_ENTERED)"}
            </span>
            <button type="button" onClick={() => controller.resetTemplate()} data-testid="btn-reset-template" className="text-xs text-gray-600 hover:text-gray-900 underline">
              Đặt lại mẫu gợi ý
            </button>
          </div>

          <div>
            <label htmlFor="followup-preview-textarea" className="block text-xs font-medium text-gray-700 mb-1">Nội dung thông điệp:</label>
            <textarea id="followup-preview-textarea" value={localText}
              onChange={(e) => { setLocalText(e.target.value); controller.updateBody(e.target.value); }}
              rows={6} data-testid="preview-textarea" aria-labelledby="preview-heading"
              className="w-full p-2.5 text-sm border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none resize-y font-sans"
              placeholder="Nhập nội dung nhắc nhở..." />
          </div>

          <div className="flex items-center gap-2">
            <input type="checkbox" id="review-checkbox" checked={state.isReviewed} onChange={(e) => controller.setReviewed(e.target.checked)} data-testid="checkbox-review" className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded" />
            <label htmlFor="review-checkbox" className="text-sm font-medium text-gray-800">Tôi đã xem xét nội dung (Xác nhận xem xét)</label>
          </div>

          {state.errorMessage && (
            <div className="text-xs text-red-600 bg-red-50 p-2 rounded" role="alert" data-testid="error-message">
              {state.errorMessage}
            </div>
          )}
          {state.lastActionStatus === "COPIED" && (
            <div className="text-xs text-green-700 bg-green-50 p-2 rounded" role="status" data-testid="notice-copied">
              Đã sao chép vào bộ nhớ tạm (Plain text).
            </div>
          )}
          {state.lastActionStatus === "COPY_FAILED" && (
            <div className="text-xs text-red-700 bg-red-50 p-2 rounded" role="alert" data-testid="notice-copy-failed">
              Sao chép thất bại. Vui lòng cấp quyền clipboard hoặc sao chép thủ công.
            </div>
          )}

          <div className="flex items-center justify-end gap-2 pt-2 border-t">
            {onPrepareTask && <button type="button" disabled={isCopyDisabled} onClick={() => { if (!controller.checkExpiry() && controller.getState().isReviewed) onPrepareTask(controller.getState().body); }} className="border rounded p-2 text-sm">Chuẩn bị đề xuất Task (L4)</button>}
            <button type="button" onClick={() => { controller.discard(); setLocalText(""); }} data-testid="btn-discard"
              className="px-3 py-1.5 text-sm font-medium text-gray-700 bg-gray-100 hover:bg-gray-200 rounded focus:outline-none focus:ring-2 focus:ring-gray-400">
              Hủy bỏ (Discard)
            </button>
            <button type="button" onClick={() => controller.copy()} disabled={isCopyDisabled} data-testid="btn-copy"
              className={`px-3 py-1.5 text-sm font-medium text-white rounded focus:outline-none focus:ring-2 ${isCopyDisabled ? "bg-gray-400 cursor-not-allowed" : "bg-blue-600 hover:bg-blue-700 focus:ring-blue-500"}`}>
              {state.isCopying ? "Đang sao chép..." : "Sao chép (Copy text)"}
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
