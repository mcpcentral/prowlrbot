import { useState, useMemo } from "react";
import { Input, Button, Tag, Empty } from "antd";
import {
  SearchOutlined,
  ExperimentOutlined,
  BookOutlined,
} from "@ant-design/icons";

interface ResearchItem {
  id: string;
  title: string;
  summary: string;
  tags: string[];
  source: string;
  date: string;
}

const sampleItems: ResearchItem[] = [
  {
    id: "1",
    title: "Multi-Agent Coordination Patterns",
    summary:
      "Analysis of coordination strategies for autonomous agent systems including leader-follower, consensus-based, and market-based approaches.",
    tags: ["multi-agent", "coordination", "patterns"],
    source: "Internal Research",
    date: "2026-03-10",
  },
  {
    id: "2",
    title: "LLM Tool Use Reliability",
    summary:
      "Benchmark results for tool calling accuracy across different LLM providers and model sizes.",
    tags: ["llm", "tools", "benchmark"],
    source: "Community",
    date: "2026-03-08",
  },
  {
    id: "3",
    title: "Memory Tier Optimization",
    summary:
      "Strategies for efficient memory compaction and tier promotion in long-running agent sessions.",
    tags: ["memory", "optimization", "tiers"],
    source: "Internal Research",
    date: "2026-03-05",
  },
];

export default function ResearchPage() {
  const [search, setSearch] = useState("");

  const filtered = useMemo(() => {
    if (!search.trim()) return sampleItems;
    const q = search.toLowerCase();
    return sampleItems.filter(
      (item) =>
        item.title.toLowerCase().includes(q) ||
        item.summary.toLowerCase().includes(q) ||
        item.tags.some((t) => t.includes(q)),
    );
  }, [search]);

  return (
    <div style={{ padding: 24 }}>
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: 16,
        }}
      >
        <div>
          <h3 style={{ margin: 0 }}>
            <ExperimentOutlined style={{ marginRight: 8 }} />
            Research
          </h3>
          <p style={{ color: "#888", fontSize: 13, marginTop: 4, marginBottom: 0 }}>
            Explore research findings, benchmarks, and knowledge collected by
            your agents.
          </p>
        </div>
        <Button type="primary" icon={<BookOutlined />}>
          New Research
        </Button>
      </div>

      <Input
        placeholder="Search research..."
        prefix={<SearchOutlined />}
        allowClear
        value={search}
        onChange={(e) => setSearch(e.target.value)}
        style={{ marginBottom: 16, maxWidth: 400 }}
      />

      {filtered.length === 0 ? (
        <Empty description="No research items match your search" />
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          {filtered.map((item) => (
            <div
              key={item.id}
              style={{
                border: "1px solid #f0f0f0",
                borderRadius: 8,
                padding: 16,
                cursor: "pointer",
              }}
            >
              <div
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "flex-start",
                }}
              >
                <h4 style={{ margin: 0 }}>{item.title}</h4>
                <span style={{ color: "#999", fontSize: 12 }}>{item.date}</span>
              </div>
              <p style={{ color: "#666", fontSize: 13, margin: "8px 0" }}>
                {item.summary}
              </p>
              <div style={{ display: "flex", gap: 4, flexWrap: "wrap" }}>
                {item.tags.map((tag) => (
                  <Tag key={tag} color="blue">
                    {tag}
                  </Tag>
                ))}
                <Tag>{item.source}</Tag>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
