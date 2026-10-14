import React, { useState } from "react";
import ReactDOM from "react-dom/client";
import { FollowupPreview } from "../../frontend/src/pages/copilot/prepare/FollowupPreview.tsx";
import type { ClipboardPort, Clock } from "../../frontend/src/pages/copilot/prepare/followupPreviewController.ts";

// Synthetic sentinels that must NEVER leak into preview body, textarea or clipboard
(window as any).__INVOICE_SENTINEL__ = "INVOICE-100-SECRET-VAL";
(window as any).__AUTH_TOKEN_SENTINEL__ = "BEARER-TOKEN-SECRET-XYZ";
(window as any).__CUSTOMER_SENTINEL__ = "ACME-CORP-SECRET-NAME";

// Exposed synthetic clipboard inspection for test assertions
(window as any).__clipboardWrites = [];
const fixtureClipboard: ClipboardPort = {
  async writeText(text: string) {
    if ((window as any).__clipboardShouldFail) {
      throw new Error("Clipboard permission denied");
    }
    (window as any).__clipboardWrites.push(text);
  },
};

// Exposed synthetic clock for test manipulation
(window as any).__mockClockTime = 1000;
const fixtureClock: Clock = {
  now() {
    return (window as any).__mockClockTime;
  },
};

const FixtureApp: React.FC = () => {
  const [scopeEpoch, setScopeEpoch] = useState<string>("epoch-init");
  const [isMounted, setIsMounted] = useState<boolean>(true);

  return (
    <div className="p-6 max-w-3xl mx-auto space-y-6">
      <div className="bg-white p-4 rounded border shadow-sm flex flex-wrap gap-2 items-center">
        <button
          id="btn-switch-scope"
          type="button"
          onClick={() => setScopeEpoch("epoch-" + Date.now())}
          className="px-3 py-1 bg-amber-100 text-amber-800 rounded text-sm hover:bg-amber-200"
        >
          Đổi Scope (Scope Epoch Change)
        </button>
        <button
          id="btn-toggle-mount"
          type="button"
          onClick={() => setIsMounted((prev) => !prev)}
          className="px-3 py-1 bg-red-100 text-red-800 rounded text-sm hover:bg-red-200"
        >
          {isMounted ? "Unmount Preview" : "Remount Preview"}
        </button>
        <span id="current-scope" className="text-xs text-gray-500 font-mono">
          Scope: {scopeEpoch}
        </span>
      </div>

      <div id="fixture-mount-container">
        {isMounted ? (
          <FollowupPreview
            scopeEpoch={scopeEpoch}
            controllerOptions={{
              clipboard: fixtureClipboard,
              clock: fixtureClock,
            }}
          />
        ) : (
          <div id="unmounted-indicator" className="p-4 text-center text-gray-400">
            Preview Unmounted
          </div>
        )}
      </div>
    </div>
  );
};

const rootEl = document.getElementById("root");
if (rootEl) {
  ReactDOM.createRoot(rootEl).render(<FixtureApp />);
}
