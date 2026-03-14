import { AuthenticateWithRedirectCallback } from "@clerk/react";

/**
 * Handles OAuth redirect from Clerk (e.g. after "Sign in with Google").
 * Clerk redirects to /sign-in/sso-callback; this route must exist or you get "No routes matched".
 */
export function SignInSsoCallbackPage() {
  return (
    <div
      style={{
        minHeight: "100vh",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        padding: "var(--space-4)",
        color: "var(--text-muted)",
      }}
    >
      <AuthenticateWithRedirectCallback />
      <p style={{ marginTop: "var(--space-4)", fontSize: "0.875rem" }}>
        Completing sign-in…
      </p>
    </div>
  );
}
