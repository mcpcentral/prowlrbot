import { useEffect, useState } from "react";
import {
  Typography,
  Table,
  Select,
  Input,
  Tag,
  Space,
  Empty,
  Spin,
  message,
} from "antd";
import { SearchOutlined } from "@ant-design/icons";
import { getAgentMemory, searchMemory } from "../../api/memory";
import type { MemoryEntry } from "../../api/memory";

const tierColors: Record<string, string> = {
  short: "blue",
  medium: "orange",
  long: "green",
};

const columns = [
  {
    title: "Topic",
    dataIndex: "topic",
    key: "topic",
    width: 200,
    ellipsis: true,
  },
  {
    title: "Summary",
    dataIndex: "summary",
    key: "summary",
    ellipsis: true,
  },
  {
    title: "Tier",
    dataIndex: "tier",
    key: "tier",
    width: 90,
    render: (tier: string) => (
      <Tag color={tierColors[tier] ?? "default"}>{tier.toUpperCase()}</Tag>
    ),
  },
  {
    title: "Accessed",
    dataIndex: "access_count",
    key: "access_count",
    width: 90,
    sorter: (a: MemoryEntry, b: MemoryEntry) =>
      a.access_count - b.access_count,
  },
  {
    title: "Importance",
    dataIndex: "importance",
    key: "importance",
    width: 100,
    sorter: (a: MemoryEntry, b: MemoryEntry) => a.importance - b.importance,
  },
  {
    title: "Created",
    dataIndex: "created_at",
    key: "created_at",
    width: 160,
    ellipsis: true,
  },
];

export default function MemoryPage() {
  const [entries, setEntries] = useState<MemoryEntry[]>([]);
  const [loading, setLoading] = useState(false);
  const [agentId, setAgentId] = useState("default");
  const [tier, setTier] = useState<string>("");
  const [query, setQuery] = useState("");

  const fetch = async () => {
    setLoading(true);
    try {
      if (query) {
        setEntries(await searchMemory(agentId, query));
      } else {
        setEntries(await getAgentMemory(agentId, tier || undefined));
      }
    } catch (e) {
      setEntries([]);
      const msg = e instanceof Error ? e.message : "Failed to load memory";
      message.error(msg);
    }
    setLoading(false);
  };

  useEffect(() => {
    fetch();
  }, [agentId, tier]); // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <div style={{ padding: 24 }}>
      <Typography.Title level={3}>Agent Memory</Typography.Title>

      <Space wrap style={{ marginBottom: 16 }}>
        <Select
          value={agentId}
          onChange={setAgentId}
          style={{ width: 180 }}
          options={[
            { label: "Default Agent", value: "default" },
            { label: "All Agents", value: "__all__" },
          ]}
        />
        <Select
          value={tier}
          onChange={setTier}
          style={{ width: 140 }}
          allowClear
          placeholder="All tiers"
          options={[
            { label: "Short-term", value: "short" },
            { label: "Medium-term", value: "medium" },
            { label: "Long-term", value: "long" },
          ]}
        />
        <Input.Search
          placeholder="Search memories..."
          prefix={<SearchOutlined />}
          onSearch={(v) => {
            setQuery(v);
            fetch();
          }}
          onChange={(e) => setQuery(e.target.value)}
          allowClear
          style={{ width: 280 }}
        />
      </Space>

      {loading ? (
        <Spin size="large" style={{ display: "block", marginTop: 48 }} />
      ) : entries.length === 0 ? (
        <Empty description="No memories found" />
      ) : (
        <Table
          dataSource={entries}
          columns={columns}
          rowKey="id"
          size="small"
          pagination={{ pageSize: 20, showSizeChanger: true }}
        />
      )}
    </div>
  );
}
