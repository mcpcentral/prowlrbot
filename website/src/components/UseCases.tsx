import {
  Share2,
  Lightbulb,
  CheckSquare,
  BookOpen,
  LayoutDashboard,
  Sparkles,
  type LucideIcon,
} from "lucide-react";
import { t, type Lang } from "../i18n";
import { SectionWrapper } from "./SectionWrapper";

const CATEGORIES: Array<{
  key:
    | "social"
    | "creative"
    | "productivity"
    | "research"
    | "assistant"
    | "explore";
  icon: LucideIcon;
  items: number;
}> = [
  { key: "social", icon: Share2, items: 3 },
  { key: "creative", icon: Lightbulb, items: 2 },
  { key: "productivity", icon: CheckSquare, items: 3 },
  { key: "research", icon: BookOpen, items: 2 },
  { key: "assistant", icon: LayoutDashboard, items: 1 },
  { key: "explore", icon: Sparkles, items: 1 },
];

interface UseCasesProps {
  lang: Lang;
}

export function UseCases({ lang }: UseCasesProps) {
  return (
    <SectionWrapper
      id="usecases"
      label="Use Cases"
      title={t(lang, "usecases.title")}
      description={t(lang, "usecases.sub")}
    >
      <div className="usecases-grid">
        {CATEGORIES.map(({ key, icon: Icon, items }) => (
          <div key={key} className="usecases-card">
            <div className="usecases-card-header">
              <Icon
                size={22}
                strokeWidth={1.5}
                style={{ flexShrink: 0, color: "var(--text)" }}
                aria-hidden
              />
              <span className="usecases-card-title">
                {t(lang, `usecases.category.${key}`)}
              </span>
            </div>
            <ul className="usecases-list">
              {Array.from({ length: items }, (_, i) => i + 1).map((i) => (
                <li key={i}>{t(lang, `usecases.${key}.${i}`)}</li>
              ))}
            </ul>
          </div>
        ))}
      </div>
    </SectionWrapper>
  );
}
