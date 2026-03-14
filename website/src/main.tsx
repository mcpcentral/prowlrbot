import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import { ClerkProvider } from "@clerk/react";
import { AuthProvider } from "./contexts/AuthContext";
import App from "./App";

const base = import.meta.env.BASE_URL || "/";
const clerkKey = import.meta.env.VITE_CLERK_PUBLISHABLE_KEY as string | undefined;

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <BrowserRouter basename={base.replace(/\/$/, "")}>
      {clerkKey ? (
        <ClerkProvider
          publishableKey={clerkKey}
          afterSignOutUrl={base ? `${base}/` : "/"}
        >
          <AuthProvider enabled={true}>
            <App />
          </AuthProvider>
        </ClerkProvider>
      ) : (
        <AuthProvider enabled={false}>
          <App />
        </AuthProvider>
      )}
    </BrowserRouter>
  </StrictMode>,
);
