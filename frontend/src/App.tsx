import React from "react";
import { Refine, Authenticated } from "@refinedev/core";
import { BrowserRouter, Routes, Route, Navigate, Outlet } from "react-router-dom";
import routerBindings, { NavigateToResource, CatchAllNavigate } from "@refinedev/react-router";

import { authProvider } from "./providers/authProvider";
import { dataProvider } from "./providers/dataProvider";
import { AppLayout } from "./components/layout/AppLayout";
import { LoginPage } from "./pages/login";
import { ModuleSelectorHome } from "./pages/home/ModuleSelectorHome";
import { UniversalListView } from "./pages/dynamic/UniversalListView";
import { UniversalFormView } from "./pages/dynamic/UniversalFormView";
import { UniversalWorkspaceView } from "./pages/dynamic/UniversalWorkspaceView";
import { UniversalReportView } from "./pages/dynamic/UniversalReportView";
import { UniversalPageView } from "./pages/dynamic/UniversalPageView";
import { I18nProvider } from "./i18n";

export function App() {
  return (
    <I18nProvider>
      <BrowserRouter>
        <Refine
        authProvider={authProvider}
        dataProvider={dataProvider}
        routerProvider={routerBindings}
        options={{
          syncWithLocation: true,
          warnWhenUnsavedChanges: true,
        }}
      >
        <Routes>
          <Route
            element={
              <Authenticated
                key="authenticated-inner"
                fallback={<CatchAllNavigate to="/login" />}
              >
                <AppLayout>
                  <Outlet />
                </AppLayout>
              </Authenticated>
            }
          >
            {/* 1. Màn hình Chọn Module dạng lưới Icon chuẩn như Trang chủ Desk gốc (Ảnh 1) */}
            <Route index element={<ModuleSelectorHome />} />
            <Route path="/home" element={<ModuleSelectorHome />} />

            {/* 2. Màn hình Module Dashboard (Invoicing, Stock, Buying...) chuẩn như Ảnh 2 */}
            <Route path="/workspace/:workspaceName" element={<UniversalWorkspaceView />} />

            {/* 3. Màn hình Báo cáo động (General Ledger, Trial Balance, Accounts Receivable...) */}
            <Route path="/report/:reportName" element={<UniversalReportView />} />

            {/* 4. Màn hình Trang tương tác (Sales Funnel, POS, Leaderboard...) */}
            <Route path="/page/:pageName" element={<UniversalPageView />} />

            {/* 5. Bộ Route động kết xuất 100% DocType (Customer, Sales Invoice, Item...) */}
            <Route path="/app/:doctype" element={<UniversalListView />} />
            <Route path="/app/:doctype/new" element={<UniversalFormView />} />
            <Route path="/app/:doctype/:id" element={<UniversalFormView />} />
          </Route>

          <Route
            element={
              <Authenticated key="authenticated-outer" fallback={<Outlet />}>
                <NavigateToResource />
              </Authenticated>
            }
          >
            <Route path="/login" element={<LoginPage />} />
          </Route>
        </Routes>
      </Refine>
    </BrowserRouter>
  </I18nProvider>
  );
}

export default App;
