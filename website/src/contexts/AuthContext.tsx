import { createContext, useContext, type ReactNode } from "react";

const AuthContext = createContext<boolean>(false);

export function AuthProvider({
  enabled,
  children,
}: {
  enabled: boolean;
  children: ReactNode;
}) {
  return (
    <AuthContext.Provider value={enabled}>{children}</AuthContext.Provider>
  );
}

export function useAuthEnabled(): boolean {
  return useContext(AuthContext);
}
