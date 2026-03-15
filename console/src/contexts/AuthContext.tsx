import { createContext, useContext, useEffect, useState, useCallback } from "react";
import type { ReactNode } from "react";
import { useAuth as useClerkAuth } from "@clerk/react";
import {
  fetchMe,
  getStoredToken,
  clearStoredToken,
  setStoredToken,
  type AuthUser,
} from "../api/modules/auth";
import { setTokenProvider } from "../api/config";

interface AuthContextValue {
  user: AuthUser | null;
  loading: boolean;
  isAuthenticated: boolean;
  /** Call after a successful login/register to refresh user state (legacy auth only). */
  onLogin: (token: string) => void;
  /** Clear token and user state. */
  onLogout: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

/** When Clerk is enabled, wire token provider and derive state from Clerk + /auth/me. */
function ClerkAuthProvider({ children }: { children: ReactNode }) {
  const { getToken, isSignedIn, signOut } = useClerkAuth();
  const [user, setUser] = useState<AuthUser | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setTokenProvider(() => getToken({ template: "default" }));
  }, [getToken]);

  const loadUser = useCallback(async () => {
    if (!isSignedIn) {
      setUser(null);
      setLoading(false);
      return;
    }
    try {
      const me = await fetchMe();
      setUser(me);
    } catch {
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, [isSignedIn]);

  useEffect(() => {
    loadUser();
  }, [loadUser]);

  const onLogout = useCallback(() => {
    signOut();
    setUser(null);
  }, [signOut]);

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        isAuthenticated: !!isSignedIn,
        onLogin: () => {},
        onLogout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

/** Legacy auth: localStorage token + /auth/me. */
function LegacyAuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [loading, setLoading] = useState(true);

  const loadUser = useCallback(async () => {
    const token = getStoredToken();
    if (!token) {
      setUser(null);
      setLoading(false);
      return;
    }
    try {
      const me = await fetchMe();
      setUser(me);
    } catch {
      clearStoredToken();
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadUser();
  }, [loadUser]);

  useEffect(() => {
    const hash = window.location.hash;
    const match = hash.match(/[?&]token=([^&]+)/);
    if (match) {
      const token = decodeURIComponent(match[1]);
      setStoredToken(token);
      window.history.replaceState(null, "", window.location.pathname);
      loadUser();
    }
  }, [loadUser]);

  const onLogin = useCallback(
    (token: string) => {
      setStoredToken(token);
      loadUser();
    },
    [loadUser],
  );

  const onLogout = useCallback(() => {
    clearStoredToken();
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        isAuthenticated: !!user,
        onLogin,
        onLogout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

interface AuthProviderProps {
  children: ReactNode;
  /** When true, use Clerk for auth (must be wrapped in ClerkProvider). */
  useClerk?: boolean;
}

export function AuthProvider({ children, useClerk = false }: AuthProviderProps) {
  if (useClerk) {
    return <ClerkAuthProvider>{children}</ClerkAuthProvider>;
  }
  return <LegacyAuthProvider>{children}</LegacyAuthProvider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
