import { NavLink } from "react-router-dom";
import {
  BuildingIcon,
  DashboardIcon,
  GridIcon,
  UploadIcon,
  UsersIcon,
  WalletIcon,
} from "./icons";
import { Logomark } from "./Logomark";

const NAV_ITEMS = [
  { to: "/", label: "Dashboard", icon: DashboardIcon, end: true },
  { to: "/staff-audit", label: "Auditoría de meseros", icon: UsersIcon },
  { to: "/menu-engineering", label: "Ingeniería de menú", icon: GridIcon },
  { to: "/cash-audit", label: "Auditoría de caja", icon: WalletIcon },
  { to: "/sync-test", label: "Probar ingesta", icon: UploadIcon },
  { to: "/tenants", label: "Tenants", icon: BuildingIcon },
];

export function Sidebar() {
  return (
    <aside className="sidebar">
      <div className="sidebar__brand">
        <Logomark size={30} />
        <span className="sidebar__brand-name">itable app</span>
      </div>

      <nav className="sidebar__nav">
        {NAV_ITEMS.map(({ to, label, icon: ItemIcon, end }) => (
          <NavLink
            key={to}
            to={to}
            end={end}
            className={({ isActive }) => `sidebar__link${isActive ? " active" : ""}`}
          >
            <ItemIcon />
            <span>{label}</span>
          </NavLink>
        ))}
      </nav>
    </aside>
  );
}
