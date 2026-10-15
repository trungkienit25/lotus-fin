import React, { useState } from "react";

export interface L3FollowupChatCardProps {
  invoiceId?: string;
  customerName?: string;
  amountText?: string;
  onCreateTask?: (noteText: string) => void;
}

export const L3FollowupChatCard: React.FC<L3FollowupChatCardProps> = ({
  invoiceId = "SINV-2026-00088",
  customerName = "Công ty TNHH Sen Vàng",
  amountText = "87,000,000 VND",
  onCreateTask,
}) => {
  const [content, setContent] = useState(
    `Kính gửi Quý đối tác ${customerName},\n\nBộ phận Kế toán xin phép nhắc nhở về khoản công nợ của Hóa đơn ${invoiceId} với số tiền là ${amountText} hiện đã đến hạn thanh toán.\n\nKính mong Quý công ty kiểm tra và sắp xếp lịch thanh toán trong tuần này. Xin chân thành cảm ơn!`
  );
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="w-full rounded-2xl border border-slate-200/90 bg-white p-4 sm:p-5 shadow-2xs font-sans text-slate-800 space-y-3.5 my-2">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-100 pb-3">
        <div className="flex items-center gap-2">
          <div className="size-7 rounded-xl bg-purple-50 text-purple-600 flex items-center justify-center font-bold text-xs shadow-2xs">
            ✍️
          </div>
          <div>
            <h4 className="text-xs sm:text-sm font-bold text-slate-900 leading-tight">
              Bản nháp nhắc nợ cục bộ (L3 Followup Preview)
            </h4>
            <div className="text-[11px] text-slate-400">
              Đối tượng: <span className="font-semibold text-slate-700">{invoiceId}</span> ({customerName})
            </div>
          </div>
        </div>

        <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-50 text-amber-800 border border-amber-200">
          CHƯA LƯU · CHƯA GỬI
        </span>
      </div>

      {/* Safety Banner */}
      <div className="p-2.5 rounded-xl border border-amber-200/70 bg-amber-50/60 text-amber-900 text-[11px] flex items-center gap-2">
        <span className="text-sm">⚠️</span>
        <span>
          Nội dung soạn thảo cục bộ trên trình duyệt. Không có tác dụng phụ, không tự động gửi email ra ngoài.
        </span>
      </div>

      {/* Editable Area */}
      <div className="space-y-1.5">
        <label className="text-[11px] font-bold uppercase tracking-wider text-slate-400 block">
          Nội dung thư nhắc nợ:
        </label>
        <textarea
          rows={5}
          value={content}
          onChange={(e) => setContent(e.target.value)}
          className="w-full text-xs font-sans rounded-xl border border-slate-200 p-3 text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 leading-relaxed bg-slate-50/40"
        />
      </div>

      {/* Actions */}
      <div className="flex flex-wrap items-center justify-between gap-2 pt-1 border-t border-slate-100">
        <span className="text-[10px] text-slate-400">
          Bạn có thể sửa trực tiếp hoặc sao chép để gửi thủ công
        </span>

        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={handleCopy}
            className="px-3 py-1.5 rounded-xl border border-slate-200 bg-white hover:bg-slate-50 text-slate-700 text-xs font-semibold shadow-2xs transition-all cursor-pointer flex items-center gap-1.5"
          >
            {copied ? (
              <>
                <span className="text-emerald-600 font-bold">✓</span>
                <span className="text-emerald-700">Đã sao chép!</span>
              </>
            ) : (
              <>
                <span>📋</span>
                <span>Sao chép</span>
              </>
            )}
          </button>

          {onCreateTask && (
            <button
              type="button"
              onClick={() => onCreateTask(content)}
              className="px-3.5 py-1.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold shadow-xs transition-all cursor-pointer flex items-center gap-1.5"
            >
              <span>+ Tạo việc theo dõi L4</span>
            </button>
          )}
        </div>
      </div>
    </div>
  );
};
