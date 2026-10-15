import React, { useState } from "react";
import { ModuleBadge } from "../components/ModuleBadge";

export interface L3FollowupChatCardProps {
  invoiceId?: string;
  customerName?: string;
  amountText?: string;
  dueDate?: string;
  onCreateTask?: (noteText: string) => void;
}

export const L3FollowupChatCard: React.FC<L3FollowupChatCardProps> = ({
  invoiceId = "SINV-2026-00088",
  customerName = "Công ty TNHH Sen Vàng",
  amountText = "87,000,000 VND",
  dueDate = "25/10/2026",
  onCreateTask,
}) => {
  const [content, setContent] = useState(
    `Kính gửi Quý đối tác ${customerName},\n\nBộ phận Kế toán xin phép gửi thông báo đối soát công nợ đối với Hóa đơn ${invoiceId} với giá trị thanh toán ${amountText}, ngày đến hạn ${dueDate}.\n\nKính mong Quý công ty kiểm tra thông tin và hỗ trợ sắp xếp tiến độ thanh toán theo quy định.\n\nTrân trọng cảm ơn sự hợp tác của Quý đối tác!`
  );
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="w-full mt-3 rounded-2xl border border-slate-200/80 bg-white overflow-hidden shadow-xs font-sans text-slate-800 transition-all">
      {/* Top Brand Banner */}
      <div className="p-4 sm:p-5 bg-gradient-to-r from-slate-900 via-indigo-950 to-blue-950 text-white flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <ModuleBadge moduleId="financial_health" size="sm" />
          <div>
            <div className="flex items-center gap-2">
              <span className="text-sm font-bold tracking-tight text-white">
                Bản nháp Thư nhắc nợ Khách hàng
              </span>
              <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-500/20 text-emerald-300 border border-emerald-400/30">
                L3 Preview
              </span>
            </div>
            <p className="text-xs text-slate-300 mt-0.5">
              Soạn thảo đối chiếu công nợ tức thì · Lưu trữ cục bộ an toàn
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 self-start sm:self-auto">
          <span className="px-2.5 py-1 rounded-full text-[10px] font-semibold bg-white/10 text-slate-200 border border-white/20 backdrop-blur font-mono">
            {invoiceId}
          </span>
        </div>
      </div>

      <div className="p-4 sm:p-5 space-y-4">
        {/* Meta summary cards */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          <div className="p-3 rounded-xl bg-[#F8FAFC] border border-slate-200/60">
            <span className="text-[11px] font-medium text-slate-400 block">Khách hàng đối soát</span>
            <span className="text-xs font-bold text-slate-800 truncate block mt-0.5">{customerName}</span>
          </div>
          <div className="p-3 rounded-xl bg-[#F8FAFC] border border-slate-200/60">
            <span className="text-[11px] font-medium text-slate-400 block">Dư nợ cần thanh toán</span>
            <span className="text-xs font-bold text-blue-700 font-mono block mt-0.5">{amountText}</span>
          </div>
          <div className="p-3 rounded-xl bg-[#F8FAFC] border border-slate-200/60">
            <span className="text-[11px] font-medium text-slate-400 block">Hạn thanh toán</span>
            <span className="text-xs font-bold text-slate-800 font-mono block mt-0.5">{dueDate}</span>
          </div>
        </div>

        {/* Text Area */}
        <div className="space-y-1.5">
          <div className="flex items-center justify-between">
            <label className="text-xs font-bold text-slate-700">
              Nội dung thông báo (Có thể chỉnh sửa trực tiếp):
            </label>
            <span className="text-[11px] text-slate-400">
              {content.length} ký tự
            </span>
          </div>
          <textarea
            rows={5}
            value={content}
            onChange={(e) => setContent(e.target.value)}
            className="w-full text-xs font-sans rounded-xl border border-slate-200 p-3.5 text-slate-800 focus:outline-none focus:ring-2 focus:ring-[#1E63B7]/20 focus:border-[#1E63B7] leading-relaxed bg-[#F9FBFC] transition-all resize-none"
          />
        </div>

        {/* Audit Notice */}
        <div className="p-3 rounded-xl bg-amber-50/70 border border-amber-200/70 text-amber-900 text-xs flex items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <span className="text-amber-600 font-bold">ℹ</span>
            <span>Nội dung chỉ hiển thị cục bộ trên trình duyệt. Hệ thống không tự động gửi email hoặc tác động vào sổ sách kế toán.</span>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="pt-2 flex flex-wrap items-center justify-between gap-3 border-t border-slate-100">
          <span className="text-[11px] text-slate-400">
            Chọn thao tác tiếp theo phù hợp:
          </span>

          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={handleCopy}
              className="px-3.5 py-2 rounded-xl border border-slate-200 bg-white hover:bg-slate-50 text-slate-700 text-xs font-bold shadow-2xs transition-all cursor-pointer flex items-center gap-1.5 hover:border-slate-300"
            >
              {copied ? (
                <>
                  <span className="text-emerald-600">✓</span>
                  <span className="text-emerald-700">Đã sao chép</span>
                </>
              ) : (
                <>
                  <svg className="size-3.5 text-slate-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                  </svg>
                  <span>Sao chép thư</span>
                </>
              )}
            </button>

            {onCreateTask && (
              <button
                type="button"
                onClick={() => onCreateTask(content)}
                className="px-4 py-2 rounded-xl text-white text-xs font-bold shadow-2xs transition-all cursor-pointer flex items-center gap-2 hover:opacity-95"
                style={{ background: "linear-gradient(135deg, #1E63B7 0%, #2FB29A 100%)" }}
              >
                <span>✦ Tạo Đề xuất Tác vụ L4</span>
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
