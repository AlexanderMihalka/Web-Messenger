import { useQueryClient } from "@tanstack/react-query";
import { createContext, useCallback, useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";
import { useNavigate } from "react-router-dom";

import { authApi, type RegisterPayload } from "../api/auth";
import { registerUnauthorizedHandler, setAccessToken } from "../api/client";
import type { UserMe } from "../api/types";

export interface AuthContextValue {
  user: UserMe | null;
  status: "loading" | "authenticated" | "anonymous";
  login: (login: string, password: string) => Promise<void>;
  register: (payload: RegisterPayload) => Promise<void>;
  logout: () => Promise<void>;
  refreshMe: () => Promise<void>;
}

// Сам контекст експортується окремо від хука (hooks/useAuth.ts) — так усі файли, що
// експортують лише компоненти, лишаються сумісними з React Fast Refresh.
export const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserMe | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const handleUnauthorized = useCallback(() => {
    setUser(null);
    queryClient.clear();
    navigate("/login", { replace: true });
  }, [navigate, queryClient]);

  useEffect(() => {
    registerUnauthorizedHandler(handleUnauthorized);
  }, [handleUnauthorized]);

  // При старті застосунку намагаємось тихо відновити сесію через httpOnly refresh-cookie,
  // щоб перезавантаження сторінки не вимагало повторного входу.
  useEffect(() => {
    let cancelled = false;
    authApi
      .refresh()
      .then((tokens) => {
        setAccessToken(tokens.access_token);
        return authApi.me();
      })
      .then((me) => {
        if (!cancelled) setUser(me);
      })
      .catch(() => {
        if (!cancelled) setAccessToken(null);
      })
      .finally(() => {
        if (!cancelled) setIsLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const login = useCallback(async (loginValue: string, password: string) => {
    const tokens = await authApi.login(loginValue, password);
    setAccessToken(tokens.access_token);
    setUser(await authApi.me());
  }, []);

  const register = useCallback(async (payload: RegisterPayload) => {
    const tokens = await authApi.register(payload);
    setAccessToken(tokens.access_token);
    setUser(await authApi.me());
  }, []);

  const logout = useCallback(async () => {
    try {
      await authApi.logout();
    } finally {
      setAccessToken(null);
      setUser(null);
      queryClient.clear();
    }
  }, [queryClient]);

  const refreshMe = useCallback(async () => {
    setUser(await authApi.me());
  }, []);

  const status: AuthContextValue["status"] = isLoading
    ? "loading"
    : user
      ? "authenticated"
      : "anonymous";

  const value = useMemo(
    () => ({ user, status, login, register, logout, refreshMe }),
    [user, status, login, register, logout, refreshMe],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
