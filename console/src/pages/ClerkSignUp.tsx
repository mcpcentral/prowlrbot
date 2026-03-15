import { SignUp } from "@clerk/react";
import { Card } from "antd";

/**
 * Full-page Clerk Sign Up for the console.
 * Shown when Clerk is enabled and the user navigates to /sign-up.
 */
export default function ClerkSignUpPage() {
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
        <SignUp
          fallbackRedirectUrl="/"
          signInUrl="/sign-in"
        />
      </Card>
    </div>
  );
}
