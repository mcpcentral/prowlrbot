import { CATEGORY_LABELS } from "../utils";

interface CategoryPillsProps {
  categories: string[];
  counts: Record<string, number>;
  selected: string;
  onSelect: (category: string) => void;
  totalCount: number;
}

export default function CategoryPills({
  categories,
  counts,
  selected,
  onSelect,
  totalCount,
}: CategoryPillsProps) {
  return (
    <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginBottom: 20 }}>
      <button
        onClick={() => onSelect("")}
        style={{
          padding: "6px 14px",
          borderRadius: 20,
          border: selected === "" ? "2px solid #00e5ff" : "1px solid rgba(255,255,255,0.12)",
          background: selected === "" ? "rgba(0,229,255,0.1)" : "rgba(255,255,255,0.04)",
          cursor: "pointer",
          fontSize: 13,
          color: selected === "" ? "#00e5ff" : "#888",
          fontWeight: selected === "" ? 600 : 400,
          transition: "all 0.2s",
        }}
      >
        All {totalCount}
      </button>
      {categories.map((cat) => (
        <button
          key={cat}
          onClick={() => onSelect(cat)}
          style={{
            padding: "6px 14px",
            borderRadius: 20,
            border: selected === cat ? "2px solid #00e5ff" : "1px solid rgba(255,255,255,0.12)",
            background: selected === cat ? "rgba(0,229,255,0.1)" : "rgba(255,255,255,0.04)",
            cursor: "pointer",
            fontSize: 13,
            color: selected === cat ? "#00e5ff" : "#888",
            fontWeight: selected === cat ? 600 : 400,
            transition: "all 0.2s",
          }}
        >
          {CATEGORY_LABELS[cat] || cat} {counts[cat] ?? 0}
        </button>
      ))}
    </div>
  );
}
