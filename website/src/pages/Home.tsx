import type { SiteConfig } from "../config";
import { type Lang } from "../i18n";
import { Nav } from "../components/Nav";
import { Hero } from "../components/Hero";
import { Features } from "../components/Features";
import { CompetitorComparison } from "../components/CompetitorComparison";
import { UseCases } from "../components/UseCases";
import { CommunitySection } from "../components/CommunitySection";
import { RoadmapVisual } from "../components/RoadmapVisual";
import { QuickStart } from "../components/QuickStart";
import { TechStack } from "../components/TechStack";
import { BuiltOnRoar } from "../components/BuiltOnRoar";
import { BrandStory } from "../components/BrandStory";
import { Footer } from "../components/Footer";
import { WaitlistCTA } from "../components/WaitlistCTA";

interface HomeProps {
  config: SiteConfig;
  lang: Lang;
  theme: "dark" | "light";
  onThemeToggle: () => void;
}

export function Home({ config, lang, theme, onThemeToggle }: HomeProps) {
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
      {/* Offset for fixed navbar */}
      <div style={{ paddingTop: "3.5rem" }} />
      <main>
        <Hero
          projectName={config.projectName}
          tagline={
            lang === "zh" ? config.projectTaglineZh : config.projectTaglineEn
          }
          lang={lang}
          docsPath={config.docsPath}
          consoleUrl={config.consoleUrl}
        />
        <Features lang={lang} />
        <CompetitorComparison lang={lang} />
        <UseCases lang={lang} />
        <CommunitySection lang={lang} />
        <RoadmapVisual lang={lang} />
        <QuickStart config={config} lang={lang} />
        <TechStack lang={lang} />
        <BuiltOnRoar lang={lang} />
        <BrandStory lang={lang} />
        <WaitlistCTA />
      </main>
      <Footer lang={lang} />
    </>
  );
}
