import { useState, useEffect, useCallback } from "react";
import { Button, Empty, Tag, Input } from "antd";
import {
  ApiOutlined,
  PlusOutlined,
  ReloadOutlined,
  SearchOutlined,
} from "@ant-design/icons";
import { request } from "../../api/request";

interface ExternalAgent {
  id: string;
  name: string;
  protocol: string;
  endpoint: string;
  status: string;
  capabilities: string[];
  last_seen?: string;
}

export default function ExternalAgentsPage() {
  const [agents, setAgents] = useState<ExternalAgent[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");

  const fetchAgents = useCallback(async () => {
    setLoading(true);
    try {
      const data = await request<ExternalAgent[]>("/external-agents").catch(
        () => null,
      );
      if (Array.isArray(data)) {
        setAgents(data);
      }
    } catch {
      // API not available yet
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchAgents();
  }, [fetchAgents]);

  const filtered = agents.filter((a) => {
    if (!search.trim()) return true;
    const q = search.toLowerCase();
    return (
      a.name.toLowerCase().includes(q) ||
      a.protocol.toLowerCase().includes(q) ||
      a.endpoint.toLowerCase().includes(q)
    );
  });

  const protocolColor: Record<string, string> = {
    ACP: "blue",
    A2A: "purple",
    MCP: "cyan",
    REST: "green",
  };

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
            <ApiOutlined style={{ marginRight: 8 }} />
            External Agents
          </h3>
          <p style={{ color: "#888", fontSize: 13, marginTop: 4, marginBottom: 0 }}>
            Connect to external agents via ACP, A2A, MCP, or REST protocols.
          </p>
        </div>
        <div style={{ display: "flex", gap: 8 }}>
          <Button icon={<ReloadOutlined />} onClick={fetchAgents} loading={loading}>
            Refresh
          </Button>
          <Button type="primary" icon={<PlusOutlined />}>
            Add Agent
          </Button>
        </div>
      </div>

      <Input
        placeholder="Search agents..."
        prefix={<SearchOutlined />}
        allowClear
        value={search}
        onChange={(e) => setSearch(e.target.value)}
        style={{ marginBottom: 16, maxWidth: 400 }}
      />

      {filtered.length === 0 ? (
        <Empty
          image={Empty.PRESENTED_IMAGE_SIMPLE}
          description={
            <span>
              No external agents connected yet.
              <br />
              Add agents using ACP, A2A, MCP, or REST protocols to extend your
              agent network.
            </span>
          }
        />
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          {filtered.map((agent) => (
            <div
              key={agent.id}
              style={{
                border: "1px solid #f0f0f0",
                borderRadius: 8,
                padding: 16,
              }}
            >
              <div
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                }}
              >
                <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                  <span
                    style={{
                      width: 8,
                      height: 8,
                      borderRadius: "50%",
                      background:
                        agent.status === "connected" ? "#52c41a" : "#d9d9d9",
                      display: "inline-block",
                    }}
                  />
                  <span style={{ fontWeight: 500 }}>{agent.name}</span>
                  <Tag color={protocolColor[agent.protocol] || "default"}>
                    {agent.protocol}
                  </Tag>
                </div>
                <Tag
                  color={agent.status === "connected" ? "success" : "default"}
                >
                  {agent.status}
                </Tag>
              </div>
              <div style={{ color: "#888", fontSize: 12, marginTop: 8 }}>
                {agent.endpoint}
              </div>
              {agent.capabilities.length > 0 && (
                <div
                  style={{
                    display: "flex",
                    gap: 4,
                    marginTop: 8,
                    flexWrap: "wrap",
                  }}
                >
                  {agent.capabilities.map((cap) => (
                    <Tag key={cap} style={{ fontSize: 11 }}>
                      {cap}
                    </Tag>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
