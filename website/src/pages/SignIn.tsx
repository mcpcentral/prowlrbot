import { Link } from "react-router-dom";
import { SignIn as ClerkSignIn } from "@clerk/react";
import { Nav } from "../components/Nav";
import { Footer } from "../components/Footer";
import type { SiteConfig } from "../config";
import { type Lang } from "../i18n";

interface SignInProps {
  config: SiteConfig;
  lang: Lang;
  theme: "dark" | "light";
  onThemeToggle: () => void;
}

export function SignInPage({
  config,
  lang,
  theme,
  onThemeToggle,
}: SignInProps) {
  const base = (import.meta.env.BASE_URL ?? "/").replace(/\/$/, "") || "";
  return (
    <>
      <Nav
        projectName={config.projectName}
        lang={lang}
        theme={theme}
        onThemeToggle={onThemeToggle}
        docsPath={config.docsPath}
        repoUrl={config.repoUrl}
        consoleUrl={config.consoleUrl}
      />
      <div style={{ paddingTop: "3.5rem" }} />
      <main
        style={{
          minHeight: "calc(100vh - 8rem)",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          padding: "var(--space-8) var(--space-4)",
        }}
      >
        <div style={{ marginBottom: "var(--space-4)" }}>
          <Link
            to={base || "/"}
            style={{
              color: "var(--text-muted)",
              fontSize: "0.875rem",
              textDecoration: "none",
            }}
          >
            ← Back to home
          </Link>
        </div>
        <ClerkSignIn
          routing="path"
          path="/sign-in"
          signUpUrl={base ? `${base}/sign-up` : "/sign-up"}
          fallbackRedirectUrl={base ? `${base}/` : "/"}
        />
      </main>
      <Footer lang={lang} />
    </>
  );
}
