import React, { useState } from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import axios from "axios";
import { I18nProvider } from "../../frontend/src/i18n/I18nContext";
import { VercelChatPanel } from "../../frontend/src/pages/copilot/components/VercelChatPanel";
import { LotusCopilotDrawer } from "../../frontend/src/components/copilot/LotusCopilotDrawer";
import { CopilotMessageBody } from "../../frontend/src/pages/copilot/components/CopilotMessageBody";
import { useCopilotRequest } from "../../frontend/src/pages/copilot/components/useCopilotRequest";
import { InvoiceActionPanel } from "../../frontend/src/pages/copilot/actions/InvoiceActionPanel";
import type { InvoiceActionTransport } from "../../frontend/src/pages/copilot/actions/invoiceActionController";

// Synthetic transport for testing hook scenarios safely
const syntheticTransport = async (payload: unknown, config?: any) => {
  const res = await axios.post("/api/method/lotus_fin.api.copilot_api.chat_copilot", payload, config);
  return {
    data: res.data,
    status: res.status,
    headers: res.headers as Record<string, unknown>,
  };
};

const syntheticInvoiceTransport: InvoiceActionTransport = {
  async post(capability, payload, signal) {
    const res = await axios.post(
      `/api/method/lotus_fin.api.copilot_api.${capability.replace(".", "_")}`,
      payload,
      { signal, validateStatus: () => true }
    );
    return {
      status: res.status,
      data: res.data,
      headers: res.headers as Record<string, unknown>,
    };
  },
};

const TestHarness: React.FC = () => {
  const [mode, setMode] = useState<string>("panel");
  const [testCompany, setTestCompany] = useState<string>("TestCorp");
  const [testContextKey, setTestContextKey] = useState<string>("ctx-1");
  const [qualifyContext, setQualifyContext] = useState<boolean>(false);
  const [testResult, setTestResult] = useState<any>(null);
  const [rawText, setRawText] = useState<string>("");

  const { loading, sendRequest, resetRequest } = useCopilotRequest({
    company: testCompany,
    contextKey: testContextKey,
    hasQualifiedContext: qualifyContext,
    transportFn: syntheticTransport,
  });

  const handleTestSend = async (query: string) => {
    const res = await sendRequest(query);
    setTestResult(res);
  };

  const handleCompanyChange = (newCompany: string) => {
    setTestCompany(newCompany);
    resetRequest();
    setTestResult(null);
  };

  const handleContextKeyChange = (newKey: string) => {
    setTestContextKey(newKey);
    resetRequest();
    setTestResult(null);
  };

  return (
    <div className="p-4 max-w-4xl mx-auto space-y-4 font-sans">
      <div className="flex gap-2 border-b pb-2">
        <button id="btn-mode-panel" onClick={() => setMode("panel")} className="px-3 py-1 bg-blue-100 rounded">
          Mount VercelChatPanel
        </button>
        <button id="btn-mode-drawer" onClick={() => setMode("drawer")} className="px-3 py-1 bg-green-100 rounded">
          Mount Drawer
        </button>
        <button id="btn-mode-hook" onClick={() => setMode("hook")} className="px-3 py-1 bg-purple-100 rounded">
          Test Request Hook
        </button>
        <button id="btn-mode-body" onClick={() => setMode("body")} className="px-3 py-1 bg-yellow-100 rounded">
          Test MessageBody
        </button>
        <button id="btn-mode-invoice" onClick={() => setMode("invoice")} className="px-3 py-1 bg-pink-100 rounded">
          Test Invoice Actions
        </button>
      </div>

      {mode === "panel" && (
        <div className="space-y-2">
          <div className="flex gap-2">
            <button
              id="btn-panel-company-a"
              onClick={() => handleCompanyChange("Company A")}
              className="px-2 py-1 bg-gray-200"
            >
              Set Company A
            </button>
            <button
              id="btn-panel-company-b"
              onClick={() => handleCompanyChange("Company B")}
              className="px-2 py-1 bg-gray-200"
            >
              Set Company B
            </button>
            <button
              id="btn-panel-ctx-b"
              onClick={() => handleContextKeyChange("ctx-2")}
              className="px-2 py-1 bg-gray-200"
            >
              Set Context B
            </button>
          </div>
          <div className="h-[600px] border rounded-xl overflow-hidden" id="fixture-panel-container">
            <VercelChatPanel company={testCompany} contextKey={testContextKey} onOpenInspector={() => {}} />
          </div>
        </div>
      )}

      {mode === "drawer" && (
        <div id="fixture-drawer-container">
          <LotusCopilotDrawer />
        </div>
      )}

      {mode === "hook" && (
        <div id="fixture-hook-container" className="space-y-3">
          <div className="flex gap-2">
            <button
              id="btn-switch-company"
              onClick={() => handleCompanyChange("NewCorp-" + Date.now())}
              className="px-2 py-1 bg-gray-200"
            >
              Change Company
            </button>
            <button
              id="btn-qualify-context"
              onClick={() => setQualifyContext(!qualifyContext)}
              className="px-2 py-1 bg-gray-200"
            >
              Toggle Context: {qualifyContext ? "QUALIFIED" : "UNQUALIFIED"}
            </button>
          </div>
          <div className="flex gap-2">
            <button
              id="btn-send-hook"
              onClick={() => handleTestSend("test query")}
              className="px-3 py-1 bg-blue-500 text-white rounded"
            >
              Send Hook Request
            </button>
          </div>
          <div id="hook-loading">{loading ? "LOADING" : "IDLE"}</div>
          <div id="hook-result-status">{testResult?.status || "NONE"}</div>
          <div id="hook-result-text">{testResult?.userFacingText || "NONE"}</div>
          <div id="hook-result-label">{testResult?.sourceLabel || "NONE"}</div>
          <div id="hook-result-cid">{testResult?.correlationId || "NONE"}</div>
          <div id="hook-result-widgets">{testResult?.allowFinancialWidgets ? "TRUE" : "FALSE"}</div>
        </div>
      )}

      {mode === "body" && (
        <div id="fixture-body-container" className="space-y-3">
          <textarea
            id="body-input"
            value={rawText}
            onChange={(e) => setRawText(e.target.value)}
            className="w-full border p-2"
          />
          <div id="body-rendered" className="p-3 border rounded bg-white">
            <CopilotMessageBody content={rawText} />
          </div>
        </div>
      )}

      {mode === "invoice" && (
        <div id="fixture-invoice-container" className="space-y-3 p-4 border rounded-xl bg-white shadow-sm">
          <div className="flex gap-2">
            <button
              id="btn-inv-company-a"
              onClick={() => handleCompanyChange("Company A")}
              className="px-2 py-1 bg-gray-200 rounded text-xs"
            >
              Set Company A
            </button>
            <button
              id="btn-inv-company-b"
              onClick={() => handleCompanyChange("Company B")}
              className="px-2 py-1 bg-gray-200 rounded text-xs"
            >
              Set Company B
            </button>
            <button
              id="btn-inv-ctx-switch"
              onClick={() => handleContextKeyChange("ctx-" + Date.now())}
              className="px-2 py-1 bg-gray-200 rounded text-xs"
            >
              Switch Scope Key
            </button>
          </div>
          <InvoiceActionPanel
            companyCandidate={testCompany}
            scopeKey={testContextKey}
            transport={syntheticInvoiceTransport}
            allowDemoSource={true}
          />
        </div>
      )}
    </div>
  );
};

const root = ReactDOM.createRoot(document.getElementById("root")!);
root.render(
  <React.StrictMode>
    <BrowserRouter>
      <I18nProvider>
        <TestHarness />
      </I18nProvider>
    </BrowserRouter>
  </React.StrictMode>
);
