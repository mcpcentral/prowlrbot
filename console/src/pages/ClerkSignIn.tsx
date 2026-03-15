import { SignIn } from "@clerk/react";
import { Card } from "antd";

/**
 * Full-page Clerk Sign In for the console.
 * Shown when Clerk is enabled and the user is not signed in.
 */
export default function ClerkSignInPage() {
  return (
    <div
      style={{
        minHeight: "100vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        background: "var(--pb-bg-page, #f5f5f5)",
        padding: 24,
      }}
    >
      <Card bordered={false} style={{ maxWidth: 420, width: "100%" }}>
        <SignIn
          fallbackRedirectUrl="/"
          signUpUrl="/sign-up"
        />
      </Card>
    </div>
  );
}
