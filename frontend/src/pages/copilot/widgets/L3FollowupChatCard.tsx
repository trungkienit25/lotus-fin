import React, { useState } from "react";
import { ModuleBadge } from "../components/ModuleBadge";

export interface L3FollowupChatCardProps {
  invoiceId?: string;
  customerName?: string;
  amountText?: string;
  dueDate?: string;
  recipientEmail?: string;
  onCreateTask?: (noteText: string) => void;
}

export const L3FollowupChatCard: React.FC<L3FollowupChatCardProps> = ({
  invoiceId = "ACC-SINV-2026-00001",
  customerName = "Grant Plastics Ltd.",
  amountText = "67,000,000 VND",
  dueDate = "25/10/2026",
  recipientEmail = "accounting@grantplastics.com",
  onCreateTask,
}) => {
  const [emailTo, setEmailTo] = useState<string>(recipientEmail);
  const [subject, setSubject] = useState<string>(
    `[PAYMENT REMINDER & STATEMENT] Invoice Settlement ${invoiceId} - ${customerName}`
  );
  const [content, setContent] = useState<string>(
    `Dear Finance & Accounting Team - ${customerName},\n\n` +
    `We hope this message finds your business thriving.\n\n` +
    `We are writing to provide a statement reconciliation and request payment for the following invoice:\n` +
    `• Invoice ID: ${invoiceId}\n` +
    `• Due Date: ${dueDate}\n` +
    `• Outstanding Balance: ${amountText}\n\n` +
    `We kindly ask that you review these details and arrange settlement within 3 to 5 business days to keep our mutual financial planning aligned.\n\n` +
    `If payment has already been initiated, please disregard this notice and reply with the payment confirmation receipt so we can update our ledger.\n\n` +
    `Thank you for your continued partnership!\n` +
    `Corporate Accounting & Treasury Department`
  );
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    const fullText = `To: ${emailTo}\nSubject: ${subject}\n\n${content}`;
    navigator.clipboard.writeText(fullText);
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
                Payment Reminder & Statement Dispatch
              </span>
              <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-500/20 text-emerald-300 border border-emerald-400/30">
                L3 Template
              </span>
            </div>
            <p className="text-xs text-slate-300 mt-0.5">
              Corporate Standard · Pre-populated with verified ledger data
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
            <span className="text-[11px] font-medium text-slate-400 block">Customer Account</span>
            <span className="text-xs font-bold text-slate-800 truncate block mt-0.5">{customerName}</span>
          </div>
          <div className="p-3 rounded-xl bg-[#F8FAFC] border border-slate-200/60">
            <span className="text-[11px] font-medium text-slate-400 block">Outstanding Balance</span>
            <span className="text-xs font-bold text-blue-700 font-mono block mt-0.5">{amountText}</span>
          </div>
          <div className="p-3 rounded-xl bg-[#F8FAFC] border border-slate-200/60">
            <span className="text-[11px] font-medium text-slate-400 block">Due Date</span>
            <span className="text-xs font-bold text-slate-800 font-mono block mt-0.5">{dueDate}</span>
          </div>
        </div>

        {/* Email Recipient and Subject Row */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <div>
            <label className="block text-[11px] font-bold uppercase tracking-wider text-slate-600 mb-1">
              Recipient Email:
            </label>
            <input
              type="email"
              value={emailTo}
              onChange={(e) => setEmailTo(e.target.value)}
              placeholder="accounting@clientcorp.com"
              className="w-full text-xs font-sans rounded-xl border border-slate-200 px-3.5 py-2 text-slate-800 focus:outline-none focus:ring-2 focus:ring-[#1E63B7]/20 focus:border-[#1E63B7] bg-[#F9FBFC] transition-all"
            />
          </div>
          <div>
            <label className="block text-[11px] font-bold uppercase tracking-wider text-slate-600 mb-1">
              Email Subject:
            </label>
            <input
              type="text"
              value={subject}
              onChange={(e) => setSubject(e.target.value)}
              className="w-full text-xs font-sans rounded-xl border border-slate-200 px-3.5 py-2 text-slate-800 focus:outline-none focus:ring-2 focus:ring-[#1E63B7]/20 focus:border-[#1E63B7] bg-[#F9FBFC] transition-all"
            />
          </div>
        </div>

        {/* Text Area */}
        <div className="space-y-1.5">
          <div className="flex items-center justify-between">
            <label className="text-xs font-bold text-slate-700">
              Notice Body (Directly editable):
            </label>
            <span className="text-[11px] text-slate-400">
              {content.length} characters
            </span>
          </div>
          <textarea
            rows={8}
            value={content}
            onChange={(e) => setContent(e.target.value)}
            className="w-full text-xs font-sans rounded-xl border border-slate-200 p-3.5 text-slate-800 focus:outline-none focus:ring-2 focus:ring-[#1E63B7]/20 focus:border-[#1E63B7] leading-relaxed bg-[#F9FBFC] transition-all resize-y min-h-[160px]"
          />
        </div>

        {/* Action Buttons */}
        <div className="pt-2 flex flex-wrap items-center justify-between gap-3 border-t border-slate-100">
          <span className="text-[11px] text-slate-400">
            Copy message body or promote to an audited follow-up task:
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
                  <span className="text-emerald-700">Copied</span>
                </>
              ) : (
                <>
                  <svg className="size-3.5 text-slate-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                  </svg>
                  <span>Copy Letter</span>
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
                <span>✦ Create L4 Proposal Task</span>
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
