import { createGlobalStyle } from "antd-style";
import { ConfigProvider, Spin } from "antd";
import { BrowserRouter, useLocation } from "react-router-dom";
import * as Sentry from "@sentry/react";
import { ThemeProvider, useTheme } from "./contexts/ThemeContext";
import { AuthProvider, useAuth } from "./contexts/AuthContext";
import MainLayout from "./layouts/MainLayout";
import LoginPage from "./pages/Login";
import ClerkSignInPage from "./pages/ClerkSignIn";
import ClerkSignUpPage from "./pages/ClerkSignUp";

const useClerk = !!(import.meta.env.VITE_CLERK_PUBLISHABLE_KEY as string | undefined);
import "./styles/theme.css";
import "./styles/layout.css";
import "./styles/form-override.css";

const GlobalStyle = createGlobalStyle`
* {
  margin: 0;
  box-sizing: border-box;
}
`;

function AuthGate() {
  const { isAuthenticated, loading } = useAuth();
  const { pathname } = useLocation();

  if (loading) {
    return (
      <div style={{ display: "flex", justifyContent: "center", alignItems: "center", height: "100vh" }}>
        <Spin size="large" />
      </div>
    );
  }

  if (isAuthenticated) return <MainLayout />;
  if (useClerk) {
    return pathname === "/sign-up" ? <ClerkSignUpPage /> : <ClerkSignInPage />;
  }
  return <LoginPage />;
}

function ThemedApp() {
  const { antAlgorithm, antTokenOverrides } = useTheme();

  return (
    <ConfigProvider
      prefixCls="prowlrbot"
      theme={{
        algorithm: antAlgorithm,
        token: antTokenOverrides,
      }}
    >
      <AuthProvider useClerk={useClerk}>
        <AuthGate />
      </AuthProvider>
    </ConfigProvider>
  );
}

function App() {
  return (
    <Sentry.ErrorBoundary fallback={<p>Something went wrong.</p>}>
      <BrowserRouter>
        <GlobalStyle />
        <ThemeProvider>
          <ThemedApp />
        </ThemeProvider>
      </BrowserRouter>
    </Sentry.ErrorBoundary>
  );
}

export default App;
