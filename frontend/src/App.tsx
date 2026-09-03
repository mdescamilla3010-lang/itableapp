import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { AppShell } from "./components/layout/AppShell";
import { RequireTenant } from "./components/layout/RequireTenant";
import { TenantProvider } from "./context/TenantContext";
import { CashAuditPage } from "./pages/CashAuditPage";
import { DashboardPage } from "./pages/DashboardPage";
import { MenuEngineeringPage } from "./pages/MenuEngineeringPage";
import { StaffAuditPage } from "./pages/StaffAuditPage";
import { SyncTestPage } from "./pages/SyncTestPage";
import { TenantsPage } from "./pages/TenantsPage";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      staleTime: 15_000,
    },
  },
});

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <TenantProvider>
        <BrowserRouter>
          <Routes>
            <Route element={<AppShell />}>
              <Route path="/tenants" element={<TenantsPage />} />

              <Route element={<RequireTenant />}>
                <Route index element={<DashboardPage />} />
                <Route path="/staff-audit" element={<StaffAuditPage />} />
                <Route path="/menu-engineering" element={<MenuEngineeringPage />} />
                <Route path="/cash-audit" element={<CashAuditPage />} />
                <Route path="/sync-test" element={<SyncTestPage />} />
              </Route>

              <Route path="*" element={<Navigate to="/" replace />} />
            </Route>
          </Routes>
        </BrowserRouter>
      </TenantProvider>
    </QueryClientProvider>
  );
}
