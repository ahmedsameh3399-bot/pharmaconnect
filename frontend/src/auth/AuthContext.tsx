import { createContext, useCallback, useContext, useEffect, useState, ReactNode } from "react";
import { fetchMe, logout as apiLogout } from "@/api/auth";
import { tokenStore } from "@/api/client";
import type { CurrentUser } from "@/api/types";

interface AuthState {
  user: CurrentUser | null;
  loading: boolean;
  // Called after a successful login/register to populate the cached user.
  refresh: () => Promise<void>;
  logout: () => void;
}

const AuthCtx = createContext<AuthState | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<CurrentUser | null>(null);
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    if (!tokenStore.access) {
      setUser(null);
      setLoading(false);
      return;
    }
    try {
      setUser(await fetchMe());
    } catch {
      tokenStore.clear();
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const logout = () => {
    apiLogout();
    setUser(null);
  };

  return <AuthCtx.Provider value={{ user, loading, refresh, logout }}>{children}</AuthCtx.Provider>;
}

export function useAuth(): AuthState {
  const ctx = useContext(AuthCtx);
  if (!ctx) throw new Error("useAuth must be used inside <AuthProvider>");
  return ctx;
}
