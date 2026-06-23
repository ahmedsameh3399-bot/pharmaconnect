import { useState } from "react";
import { Link, Navigate, NavLink, Outlet, useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { useAuth } from "@/auth/AuthContext";
import { useNotifications } from "@/hooks/useNotifications";

// Top-level shell: collapsible sidebar on desktop, drawer on mobile, plus
// a sticky top bar with the brand and a logout button. Responsive without
// fighting Tailwind: visibility flips on the `md:` breakpoint.
export default function AppLayout() {
  const { user, loading, logout } = useAuth();
  const nav = useNavigate();
  const { t } = useTranslation();
  const [drawerOpen, setDrawerOpen] = useState(false);

  // Subscribe to SSE only when the user is logged in.
  useNotifications(Boolean(user));

  // While the AuthContext is verifying the stored token, show a spinner
  // rather than a blank screen.
  if (loading) return <div className="p-8 text-slate-500">Loading…</div>;
  // Unauthenticated users hitting any layout-wrapped route get sent to login.
  // (Previously this returned null, which rendered a white screen.)
  if (!user) return <Navigate to="/login" replace />;

  const linksForRole = (() => {
    if (user.role === "PHARMACY") {
      return [
        { to: "/pharmacy", label: t("nav.dashboard"), end: true },
        { to: "/pharmacy/search", label: t("nav.search") },
        { to: "/pharmacy/orders", label: t("nav.myOrders") },
        { to: "/pharmacy/chatbot", label: t("nav.chatbot") },
      ];
    }
    if (user.role === "DISTRIBUTOR") {
      return [
        { to: "/distributor", label: t("nav.dashboard"), end: true },
        { to: "/distributor/catalog", label: t("nav.catalog") },
        { to: "/distributor/orders", label: t("nav.incomingOrders") },
        { to: "/distributor/alerts", label: t("nav.stockAlerts") },
      ];
    }
    return [
      { to: "/admin", label: t("nav.metrics"), end: true },
      { to: "/admin/users", label: t("nav.users") },
    ];
  })();

  const SideMenu = (
    <nav className="flex flex-col gap-1">
      {linksForRole.map((l) => (
        <NavLink
          key={l.to}
          to={l.to}
          end={l.end}
          onClick={() => setDrawerOpen(false)}
          className={({ isActive }) =>
            `px-3 py-2 rounded-lg text-sm font-medium ${
              isActive ? "bg-brand-600 text-white" : "text-slate-700 hover:bg-slate-100"
            }`
          }
        >
          {l.label}
        </NavLink>
      ))}
    </nav>
  );

  return (
    <div className="min-h-screen flex flex-col">
      <header className="sticky top-0 z-30 bg-white border-b border-slate-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 h-14 flex items-center gap-3">
          {/* Mobile hamburger - hidden on md+ */}
          <button
            onClick={() => setDrawerOpen(true)}
            className="md:hidden p-2 rounded hover:bg-slate-100"
            aria-label="Open menu"
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="4" y1="6" x2="20" y2="6" />
              <line x1="4" y1="12" x2="20" y2="12" />
              <line x1="4" y1="18" x2="20" y2="18" />
            </svg>
          </button>
          <Link to="/" className="font-bold text-lg text-brand-700">
            {t("app.name")}
          </Link>
          <div className="ml-auto flex items-center gap-3">
            <span className="hidden sm:block text-sm text-slate-600">{user.full_name}</span>
            <span className="badge bg-brand-50 text-brand-700">{user.role}</span>
            <button
              onClick={() => {
                logout();
                nav("/login");
              }}
              className="btn-secondary text-xs"
            >
              {t("nav.logout")}
            </button>
          </div>
        </div>
      </header>

      <div className="flex-1 flex max-w-7xl mx-auto w-full">
        {/* Desktop sidebar */}
        <aside className="hidden md:block w-56 shrink-0 p-4 border-r border-slate-200">
          {SideMenu}
        </aside>

        {/* Mobile drawer */}
        {drawerOpen && (
          <div
            className="md:hidden fixed inset-0 z-40 bg-black/40"
            onClick={() => setDrawerOpen(false)}
          >
            <div
              className="absolute top-0 left-0 h-full w-64 bg-white p-4 shadow-xl"
              onClick={(e) => e.stopPropagation()}
            >
              {SideMenu}
            </div>
          </div>
        )}

        <main className="flex-1 p-4 sm:p-6 min-w-0">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
