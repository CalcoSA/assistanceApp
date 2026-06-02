import { createContext, useCallback, useContext, useEffect, useMemo, useState, } from "react";
import type { AuthUser, LoginRequest } from "../models/Auth";
import { authService } from "../services/authService";

interface IntranetAccessRequest {
  userLogin: string;
  ts: string;
  sig: string;
}

interface AuthContextValue {
  user: AuthUser | null;
  token: string | null;
  loadingAuth: boolean;
  isAuthenticated: boolean;
  login: (data: LoginRequest) => Promise<void>;
  intranetAccess: (data: IntranetAccessRequest) => Promise<void>;
  logout: () => void;
  hasPermission: (path: string) => boolean;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [token, setToken] = useState<string | null>(localStorage.getItem("accessToken"));
  const [user, setUser] = useState<AuthUser | null>(null);
  const [loadingAuth, setLoadingAuth] = useState(true);

  const saveAuthSession = useCallback(
    (accessToken: string, authUser: AuthUser) => {
      localStorage.setItem("accessToken", accessToken);
      setToken(accessToken);
      setUser(authUser);
    },
    []
  );

  const logout = useCallback(() => {
    localStorage.removeItem("accessToken");
    setToken(null);
    setUser(null);
  }, []);

  const login = useCallback(
    async (data: LoginRequest) => {
      const response = await authService.login(data);

      if (!response.isSuccess || !response.result) {
        throw new Error(response.Message || "No se pudo iniciar sesión.");
      }

      saveAuthSession(response.result.accessToken, response.result.user);
    },
    [saveAuthSession]
  );

  const intranetAccess = useCallback(
    async (data: IntranetAccessRequest) => {
      const response = await authService.intranetAccess(data.userLogin, data.ts, data.sig);

      if (!response.isSuccess || !response.result) {
        throw new Error(
          response.Message || "No se pudo validar el acceso desde intranet."
        );
      }

      saveAuthSession(response.result.accessToken, response.result.user);
    },
    [saveAuthSession]
  );

  const hasPermission = useCallback(
    (path: string) => {
      if (path === "/") return true;

      return (
        user?.menuOptions.some(
          (item) => item.statusMenuOption && item.pathMenuOption === path
        ) ?? false
      );
    },
    [user]
  );

  useEffect(() => {
    const loadCurrentUser = async () => {
      const storedToken = localStorage.getItem("accessToken");

      if (!storedToken) {
        setLoadingAuth(false);
        return;
      }

      try {
        const response = await authService.me();

        if (!response.isSuccess || !response.result) {
          logout();
          return;
        }

        saveAuthSession(response.result.accessToken, response.result.user);
      } catch {
        logout();
      } finally {
        setLoadingAuth(false);
      }
    };

    loadCurrentUser();
  }, [logout, saveAuthSession]);

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      token,
      loadingAuth,
      isAuthenticated: Boolean(token && user),
      login,
      intranetAccess,
      logout,
      hasPermission,
    }),
    [
      user,
      token,
      loadingAuth,
      login,
      intranetAccess,
      logout,
      hasPermission,
    ]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);

  if (!context) {
    throw new Error("useAuth debe usarse dentro de AuthProvider.");
  }

  return context;
}