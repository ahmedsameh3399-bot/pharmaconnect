import { Navigate, Route, Routes } from "react-router-dom";
import { useAuth } from "@/auth/AuthContext";
import RequireRole from "@/auth/RequireRole";
import AppLayout from "@/components/AppLayout";
import LoginPage from "@/features/auth/LoginPage";
import RegisterPage from "@/features/auth/RegisterPage";
import PharmacyHome from "@/features/pharmacy/PharmacyHome";
import SearchPage from "@/features/pharmacy/SearchPage";
import ComparePage from "@/features/pharmacy/ComparePage";
import MyOrdersPage from "@/features/pharmacy/MyOrdersPage";
import OrderDetailPage from "@/features/pharmacy/OrderDetailPage";
import ChatbotPage from "@/features/pharmacy/ChatbotPage";
import DistributorHome from "@/features/distributor/DistributorHome";
import CatalogPage from "@/features/distributor/CatalogPage";
import IncomingOrdersPage from "@/features/distributor/IncomingOrdersPage";
import StockAlertsPage from "@/features/distributor/StockAlertsPage";
import AdminHome from "@/features/admin/AdminHome";
import AdminUsersPage from "@/features/admin/UsersPage";

// `/` redirects to the role-appropriate home so a fresh login always lands
// on something meaningful instead of a 404 or a blank page.
function HomeRedirect() {
  const { user, loading } = useAuth();
  if (loading) return <div className="p-8 text-slate-500">Loading…</div>;
  if (!user) return <Navigate to="/login" replace />;
  if (user.role === "PHARMACY") return <Navigate to="/pharmacy" replace />;
  if (user.role === "DISTRIBUTOR") return <Navigate to="/distributor" replace />;
  return <Navigate to="/admin" replace />;
}

export default function Router() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />

      <Route element={<AppLayout />}>
        <Route path="/" element={<HomeRedirect />} />

        {/* Pharmacy */}
        <Route
          path="/pharmacy"
          element={<RequireRole roles={["PHARMACY"]}><PharmacyHome /></RequireRole>}
        />
        <Route
          path="/pharmacy/search"
          element={<RequireRole roles={["PHARMACY"]}><SearchPage /></RequireRole>}
        />
        <Route
          path="/pharmacy/compare/:id"
          element={<RequireRole roles={["PHARMACY"]}><ComparePage /></RequireRole>}
        />
        <Route
          path="/pharmacy/orders"
          element={<RequireRole roles={["PHARMACY"]}><MyOrdersPage /></RequireRole>}
        />
        <Route
          path="/pharmacy/orders/:id"
          element={<RequireRole roles={["PHARMACY"]}><OrderDetailPage /></RequireRole>}
        />
        <Route
          path="/pharmacy/chatbot"
          element={<RequireRole roles={["PHARMACY"]}><ChatbotPage /></RequireRole>}
        />

        {/* Distributor */}
        <Route
          path="/distributor"
          element={<RequireRole roles={["DISTRIBUTOR"]}><DistributorHome /></RequireRole>}
        />
        <Route
          path="/distributor/catalog"
          element={<RequireRole roles={["DISTRIBUTOR"]}><CatalogPage /></RequireRole>}
        />
        <Route
          path="/distributor/orders"
          element={<RequireRole roles={["DISTRIBUTOR"]}><IncomingOrdersPage /></RequireRole>}
        />
        <Route
          path="/distributor/orders/:id"
          element={<RequireRole roles={["DISTRIBUTOR"]}><OrderDetailPage /></RequireRole>}
        />
        <Route
          path="/distributor/alerts"
          element={<RequireRole roles={["DISTRIBUTOR"]}><StockAlertsPage /></RequireRole>}
        />

        {/* Admin */}
        <Route path="/admin" element={<RequireRole roles={["ADMIN"]}><AdminHome /></RequireRole>} />
        <Route
          path="/admin/users"
          element={<RequireRole roles={["ADMIN"]}><AdminUsersPage /></RequireRole>}
        />
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
