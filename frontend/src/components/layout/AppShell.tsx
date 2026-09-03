import { Outlet } from "react-router-dom";
import { Sidebar } from "./Sidebar";
import { TenantSwitcher } from "./TenantSwitcher";
import { HealthIndicator } from "./HealthIndicator";

export function AppShell() {
  return (
    <div className="app-shell">
      <Sidebar />
      <div className="main-column">
        <header className="topbar">
          <span />
          <div className="topbar__actions">
            <HealthIndicator />
            <TenantSwitcher />
          </div>
        </header>
        <main className="content">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
