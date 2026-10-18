import React, { useState, useEffect } from "react";
import { ModuleBadge } from "../components/ModuleBadge";
import { bootstrapSession } from "../../../providers/sessionBootstrap";

export interface DebtReminderManagementViewProps {
  company: string;
  onNavigateTab?: (tab: string) => void;
  onPrepareTask?: (noteText: string) => void;
}

interface OverdueInvoiceItem {
  invoiceId: string;
  customerName: string;
  postingDate: string;
  finalDueDate: string;
  overdueDays: number;
  currentOutstandingDecimal: string;
  outstandingAmount: number;
  partyAccountCurrency: string;
}

export const DebtReminderManagementView: React.FC<DebtReminderManagementViewProps> = ({
  company,
  onPrepareTask,
}) => {
  const [invoices, setInvoices] = useState<OverdueInvoiceItem[]>([]);
  const [selectedInvoice, setSelectedInvoice] = useState<OverdueInvoiceItem | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [sourceLabel, setSourceLabel] = useState<string>("Connecting to ERP...");

  // Draft state
  const [recipientEmail, setRecipientEmail] = useState<string>("");
  const [subject, setSubject] = useState<string>("");
  const [content, setContent] = useState<string>("");
  const [isCopied, setIsCopied] = useState<boolean>(false);
  const [isReviewed, setIsReviewed] = useState<boolean>(false);
  const [notification, setNotification] = useState<{ type: "success" | "error" | "info"; msg: string } | null>(null);

  // Fetch real overdue invoices for the selected company
  useEffect(() => {
    let isMounted = true;
    async function loadInvoices() {
      setLoading(true);
      try {
        const session = await bootstrapSession().catch(() => null);
        const headers: Record<string, string> = { "Content-Type": "application/json" };
        if (session?.csrfToken) {
          headers["X-Frappe-CSRF-Token"] = session.csrfToken;
        }

        const res = await fetch("/api/method/lotus_fin.api.copilot_api.get_real_overdue_invoices", {
          method: "POST",
          headers,
          credentials: "same-origin",
          body: JSON.stringify({ company }),
        });

        if (res.ok) {
          const wire = await res.json();
          const items: OverdueInvoiceItem[] = wire?.message?.items || [];
          if (isMounted) {
            setInvoices(items);
            setSourceLabel(wire?.message?.source || "ERPNext Live Database");
            if (items.length > 0) {
              selectInvoiceForDraft(items[0]);
            } else {
              setSelectedInvoice(null);
              setContent("");
            }
          }
        }
      } catch (err) {
        console.warn("Failed to load overdue invoices:", err);
      } finally {
        if (isMounted) setLoading(false);
      }
    }

    loadInvoices();
    return () => { isMounted = false; };
  }, [company]);

  const selectInvoiceForDraft = (inv: OverdueInvoiceItem) => {
    setSelectedInvoice(inv);
    const domain = inv.customerName
      ? inv.customerName.toLowerCase().replace(/[^a-z0-9]/g, "") + ".com"
      : "clientcorp.com";
    const email = `accounting@${domain}`;
    setRecipientEmail(email);

    const sub = `[PAYMENT REMINDER & STATEMENT] Invoice Settlement ${inv.invoiceId} - ${inv.customerName}`;
    setSubject(sub);

    const body =
      `Dear Finance & Accounting Team - ${inv.customerName},\n\n` +
      `We hope this message finds your business thriving.\n\n` +
      `We are writing to provide a statement reconciliation and request payment for the following invoice:\n` +
      `• Invoice ID: ${inv.invoiceId}\n` +
      `• Due Date: ${inv.finalDueDate}\n` +
      `• Outstanding Amount: ${inv.currentOutstandingDecimal} ${inv.partyAccountCurrency}\n` +
      `• Status: Overdue by ${inv.overdueDays} days\n\n` +
      `We kindly ask that you review these details and arrange settlement within 3 to 5 business days to keep our mutual financial planning aligned.\n\n` +
      `If payment has already been initiated, please disregard this notice and reply with the payment confirmation receipt so we can update our ledger.\n\n` +
      `Thank you for your continued partnership!\n` +
      `Corporate Accounting & Treasury Department`;
    setContent(body);
    setIsReviewed(false);
  };

  const handleCopy = async () => {
    try {
      const full = `To: ${recipientEmail}\nSubject: ${subject}\n\n${content}`;
      await navigator.clipboard.writeText(full);
      setIsCopied(true);
      setNotification({ type: "success", msg: "✓ Email draft copied to clipboard successfully." });
      setTimeout(() => setIsCopied(false), 2500);
    } catch {
      setNotification({ type: "error", msg: "Failed to copy automatically. Please select and copy manually." });
    }
  };

  const handleCreateTask = () => {
    if (onPrepareTask && selectedInvoice) {
      onPrepareTask(`Follow up overdue invoice ${selectedInvoice.invoiceId} ($${selectedInvoice.currentOutstandingDecimal} USD) - ${selectedInvoice.customerName}`);
      setNotification({ type: "info", msg: "Opening task confirmation modal..." });
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-4 font-sans text-slate-800">
      {/* Top Banner */}
      <div className="p-4 sm:p-5 bg-gradient-to-r from-slate-900 via-indigo-950 to-blue-950 text-white rounded-2xl flex flex-col sm:flex-row sm:items-center justify-between gap-3 shadow-xs">
        <div className="flex items-center gap-3">
          <ModuleBadge moduleId="debt_reminder" size="md" />
          <div>
            <div className="flex items-center gap-2">
              <span className="text-base font-bold tracking-tight text-white">
                Customer Debt Reminder & Statement Dispatch
              </span>
              <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-500/20 text-emerald-300 border border-emerald-400/30">
                ERP Live Data
              </span>
            </div>
            <p className="text-xs text-slate-300 mt-0.5">
              Auto-populated from real ledger invoices · Safe editable draft before dispatch
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 self-start sm:self-auto">
          <span className="px-2.5 py-1 rounded-full text-[10px] font-semibold bg-white/10 text-slate-200 border border-white/20 backdrop-blur font-mono">
            {company}
          </span>
        </div>
      </div>

      {notification && (
        <div
          className={`p-3 rounded-xl text-xs flex items-center justify-between border ${
            notification.type === "success"
              ? "bg-emerald-50 text-emerald-800 border-emerald-200"
              : notification.type === "error"
              ? "bg-rose-50 text-rose-800 border-rose-200"
              : "bg-blue-50 text-blue-800 border-blue-200"
          }`}
        >
          <span>{notification.msg}</span>
          <button
            onClick={() => setNotification(null)}
            className="text-xs font-bold px-1.5 py-0.5 hover:opacity-75 cursor-pointer"
          >
            ✕
          </button>
        </div>
      )}

      {/* Invoice Selector Strip */}
      <div className="p-4 rounded-2xl bg-white border border-slate-200/80 shadow-xs space-y-2.5">
        <div className="flex items-center justify-between">
          <span className="text-xs font-bold text-slate-700 uppercase tracking-wider">
            Select Overdue Invoice ({invoices.length} outstanding documents)
          </span>
          <span className="text-[11px] font-mono text-slate-400">{sourceLabel}</span>
        </div>

        {loading ? (
          <div className="py-4 text-center text-xs text-slate-400 animate-pulse">
            Loading overdue invoices from ERPNext...
          </div>
        ) : invoices.length === 0 ? (
          <div className="py-4 text-center text-xs text-slate-500 bg-slate-50 rounded-xl">
            No overdue invoices currently recorded for this company.
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2.5">
            {invoices.map((inv) => {
              const isSelected = selectedInvoice?.invoiceId === inv.invoiceId;
              return (
                <div
                  key={inv.invoiceId}
                  onClick={() => selectInvoiceForDraft(inv)}
                  className={`p-3 rounded-xl border text-xs cursor-pointer transition-all ${
                    isSelected
                      ? "bg-blue-50/80 border-blue-400 ring-2 ring-blue-500/10 shadow-2xs"
                      : "bg-slate-50/60 border-slate-200 hover:bg-slate-100 hover:border-slate-300"
                  }`}
                >
                  <div className="flex items-center justify-between font-mono font-bold text-slate-900">
                    <span>{inv.invoiceId}</span>
                    <span className="text-rose-600 font-semibold text-[11px]">+{inv.overdueDays} days</span>
                  </div>
                  <div className="text-[11px] text-slate-600 truncate mt-0.5 font-medium">
                    {inv.customerName}
                  </div>
                  <div className="text-xs font-bold text-blue-700 font-mono mt-1 flex items-center justify-between">
                    <span>{inv.currentOutstandingDecimal} {inv.partyAccountCurrency}</span>
                    <span className="text-[10px] text-slate-400 font-normal">Due: {inv.finalDueDate}</span>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Editor & Preparation Workspace */}
      {selectedInvoice && (
        <div className="p-4 sm:p-5 rounded-2xl bg-white border border-slate-200/80 shadow-xs space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <div>
              <h4 className="text-sm font-bold text-slate-900">
                Payment Reminder & Reconciliation Draft
              </h4>
              <p className="text-xs text-slate-500 mt-0.5">
                Review and edit notice details before copying or creating an L4 follow-up task
              </p>
            </div>
            <button
              onClick={() => selectInvoiceForDraft(selectedInvoice)}
              className="text-xs text-blue-600 hover:text-blue-800 font-medium cursor-pointer"
            >
              ↺ Reset to default template
            </button>
          </div>

          {/* Email Headers */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label className="block text-[11px] font-bold uppercase tracking-wider text-slate-600 mb-1">
                Recipient Email:
              </label>
              <input
                type="email"
                value={recipientEmail}
                onChange={(e) => setRecipientEmail(e.target.value)}
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

          {/* Body Content */}
          <div className="space-y-1.5">
            <div className="flex items-center justify-between">
              <label className="text-xs font-bold text-slate-700">
                Reminder Notice Body (Directly editable):
              </label>
              <span className="text-[11px] text-slate-400">
                {content.length} characters
              </span>
            </div>
            <textarea
              rows={9}
              value={content}
              onChange={(e) => setContent(e.target.value)}
              className="w-full text-xs font-sans rounded-xl border border-slate-200 p-3.5 text-slate-800 focus:outline-none focus:ring-2 focus:ring-[#1E63B7]/20 focus:border-[#1E63B7] leading-relaxed bg-[#F9FBFC] transition-all resize-y min-h-[180px]"
            />
          </div>

          {/* Safety Checkbox */}
          <div className="flex items-center gap-2.5 p-3 rounded-xl bg-slate-50 border border-slate-200/60">
            <input
              type="checkbox"
              id="confirm-review-chx"
              checked={isReviewed}
              onChange={(e) => setIsReviewed(e.target.checked)}
              className="h-4 w-4 text-blue-600 focus:ring-[#1E63B7] border-slate-300 rounded cursor-pointer"
            />
            <label htmlFor="confirm-review-chx" className="text-xs font-semibold text-slate-700 cursor-pointer select-none">
              I have reviewed the balance and statement details prior to dispatching to the customer
            </label>
          </div>

          {/* Footer Actions */}
          <div className="flex flex-wrap items-center justify-between gap-3 pt-3 border-t border-slate-100">
            <div className="text-[11px] text-slate-500">
              💡 Note: Preparing and copying reminders does not modify general ledger accounting entries.
            </div>

            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={handleCopy}
                className="px-4 py-2 rounded-xl border border-slate-200 bg-white hover:bg-slate-50 text-slate-700 text-xs font-bold shadow-2xs transition-all cursor-pointer flex items-center gap-1.5 hover:border-slate-300"
              >
                {isCopied ? (
                  <>
                    <span className="text-emerald-600">✓</span>
                    <span className="text-emerald-700">Copied</span>
                  </>
                ) : (
                  <>
                    <svg className="size-3.5 text-slate-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                    </svg>
                    <span>Copy Draft 📋</span>
                  </>
                )}
              </button>

              <button
                type="button"
                onClick={handleCreateTask}
                className="px-4 py-2 rounded-xl text-white text-xs font-bold shadow-2xs transition-all cursor-pointer flex items-center gap-2 hover:opacity-95"
                style={{ background: "linear-gradient(135deg, #1E63B7 0%, #2FB29A 100%)" }}
              >
                <span>✦ Create L4 Follow-up Task</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
