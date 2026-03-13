import { useEffect, useState, useMemo } from "react";
import {
  Card,
  Button,
  Select,
  Typography,
  Space,
  Tag,
  message,
  Empty,
  Spin,
} from "antd";
import { CopyOutlined, LinkOutlined } from "@ant-design/icons";

const { Text, Paragraph } = Typography;

interface GalleryEntry {
  id: string;
  title: string;
  prompt: string;
  aesthetic: string;
  mode: string;
  reference_url?: string;
  screenshot_url: string;
  component_url?: string;
  author: string;
  created: string;
  tags: string[];
}

interface GalleryData {
  version: number;
  entries: GalleryEntry[];
}

const GALLERY_URL: string =
  import.meta.env.VITE_GALLERY_JSON_URL ??
  "https://raw.githubusercontent.com/ProwlrBot/prowlr-marketplace/main/gallery/index.json";

const AESTHETICS = ["terminal-pro", "bold-brand", "data-rich", "minimal-light", "enterprise"];
const MODES = ["ref", "show", "system"];
type SortMode = "newest" | "recent-author";

export default function UIGallery() {
  const [data, setData] = useState<GalleryData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const [filterAesthetic, setFilterAesthetic] = useState<string>("");
  const [filterMode, setFilterMode] = useState<string>("");
  const [filterTag, setFilterTag] = useState<string>("");
  const [sortMode, setSortMode] = useState<SortMode>("newest");
  const [messageApi, contextHolder] = message.useMessage();

  useEffect(() => {
    fetch(GALLERY_URL)
      .then((r) => {
        if (!r.ok) throw new Error("fetch failed");
        return r.json() as Promise<GalleryData>;
      })
      .then(setData)
      .catch(() => setError(true))
      .finally(() => setLoading(false));
  }, []);

  const allTags = useMemo(() => {
    if (!data) return [];
    const set = new Set<string>();
    data.entries.forEach((e) => e.tags.forEach((t) => set.add(t)));
    return Array.from(set).sort();
  }, [data]);

  const entries = useMemo(() => {
    if (!data) return [];
    const filtered = data.entries
      .filter((e) => !filterAesthetic || e.aesthetic === filterAesthetic)
      .filter((e) => !filterMode || e.mode === filterMode)
      .filter((e) => !filterTag || e.tags.includes(filterTag));

    if (sortMode === "newest") {
      return [...filtered].sort((a, b) => b.created.localeCompare(a.created));
    }
    // "recent-author": group by author, sort groups by their most recent entry
    const latestByAuthor: Record<string, string> = {};
    filtered.forEach((e) => {
      if (!latestByAuthor[e.author] || e.created > latestByAuthor[e.author]) {
        latestByAuthor[e.author] = e.created;
      }
    });
    return [...filtered].sort((a, b) => {
      const diff = latestByAuthor[b.author].localeCompare(latestByAuthor[a.author]);
      return diff !== 0 ? diff : b.created.localeCompare(a.created);
    });
  }, [data, filterAesthetic, filterMode, filterTag, sortMode]);

  const handleCopy = async (prompt: string) => {
    try {
      await navigator.clipboard.writeText(prompt);
      messageApi.success("Prompt copied!");
    } catch {
      messageApi.error("Copy failed");
    }
  };

  if (loading) return <Spin style={{ display: "block", marginTop: 80 }} />;

  if (error) {
    return (
      <Empty
        style={{ marginTop: 80 }}
        description="Gallery unavailable — check your connection"
      />
    );
  }

  return (
    <div style={{ padding: 24 }}>
      {contextHolder}
      <Space style={{ marginBottom: 16 }} wrap>
        <Select
          placeholder="Aesthetic"
          allowClear
          style={{ width: 160 }}
          options={AESTHETICS.map((v) => ({ label: v, value: v }))}
          onChange={(v) => setFilterAesthetic(v ?? "")}
        />
        <Select
          placeholder="Mode"
          allowClear
          style={{ width: 120 }}
          options={MODES.map((v) => ({ label: v, value: v }))}
          onChange={(v) => setFilterMode(v ?? "")}
        />
        <Select
          placeholder="Tag"
          allowClear
          style={{ width: 130 }}
          options={allTags.map((v) => ({ label: v, value: v }))}
          onChange={(v) => setFilterTag(v ?? "")}
        />
        <Select
          value={sortMode}
          style={{ width: 160 }}
          options={[
            { label: "Newest first", value: "newest" },
            { label: "Most recent author", value: "recent-author" },
          ]}
          onChange={(v) => setSortMode(v as SortMode)}
        />
        <Text type="secondary">{entries.length} designs</Text>
      </Space>

      {entries.length === 0 && (
        <Empty description="No designs yet — share yours with /ui-share!" />
      )}

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))",
          gap: 16,
        }}
      >
        {entries.map((entry) => (
          <Card
            key={entry.id}
            hoverable
            cover={
              <img
                alt={entry.title}
                src={entry.screenshot_url}
                style={{ height: 160, objectFit: "cover" }}
                crossOrigin="anonymous"
              />
            }
            actions={[
              <Button
                key="copy"
                icon={<CopyOutlined />}
                size="small"
                onClick={() => handleCopy(entry.prompt)}
              >
                Copy prompt
              </Button>,
              ...(entry.component_url
                ? [
                    <Button
                      key="view"
                      icon={<LinkOutlined />}
                      size="small"
                      onClick={() => window.open(entry.component_url, "_blank")}
                    >
                      View component
                    </Button>,
                  ]
                : []),
            ]}
          >
            <Card.Meta
              title={entry.title}
              description={
                <Space direction="vertical" size={4} style={{ width: "100%" }}>
                  <Text type="secondary" style={{ fontSize: 12 }}>
                    by {entry.author}
                  </Text>
                  <Paragraph
                    ellipsis={{ rows: 2 }}
                    style={{ margin: 0, fontSize: 12 }}
                  >
                    {entry.prompt}
                  </Paragraph>
                  <Space wrap size={4}>
                    <Tag color="blue">{entry.aesthetic}</Tag>
                    <Tag>{entry.mode}</Tag>
                    {entry.tags.slice(0, 3).map((t) => (
                      <Tag key={t}>{t}</Tag>
                    ))}
                  </Space>
                </Space>
              }
            />
          </Card>
        ))}
      </div>
    </div>
  );
}
