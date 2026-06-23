import { Navigate, useLocation } from "react-router-dom";
import { useAuth } from "./AuthContext";
import type { UserRole } from "@/api/types";

interface Props {
  roles: UserRole[];
  children: JSX.Element;
}

// Route guard. Renders children only if the current user is logged in AND
// has one of the allowed roles. Otherwise redirects (preserving the path the
// user tried to reach so we can return them there after login).
export default function RequireRole({ roles, children }: Props) {
  const { user, loading } = useAuth();
  const loc = useLocation();
  if (loading) return <div className="p-8 text-slate-500">Loading…</div>;
  if (!user) return <Navigate to="/login" state={{ from: loc }} replace />;
  if (!roles.includes(user.role)) return <Navigate to="/" replace />;
  return children;
}
