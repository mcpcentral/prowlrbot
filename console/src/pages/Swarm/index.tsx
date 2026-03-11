import { useEffect, useState, useCallback } from "react";
import {
  Typography,
  Card,
  Row,
  Col,
  Tag,
  Badge,
  Spin,
  Empty,
  Statistic,
  Button,
} from "antd";
import { ReloadOutlined } from "@ant-design/icons";
import { request } from "../../api/request";

interface SwarmWorker {
  id: string;
  name: string;
  host: string;
  status: "idle" | "working" | "offline";
  current_task?: string;
  capabilities: string[];
  last_heartbeat: string;
}

const statusColors: Record<string, string> = {
  idle: "green",
  working: "blue",
  offline: "red",
};

function heartbeatAge(ts: string): { color: string; label: string } {
  const age = (Date.now() - new Date(ts).getTime()) / 1000;
  if (age < 60) return { color: "green", label: `${Math.round(age)}s ago` };
  if (age < 120) return { color: "orange", label: `${Math.round(age)}s ago` };
  return { color: "red", label: `${Math.round(age / 60)}m ago` };
}

export default function SwarmPage() {
  const [workers, setWorkers] = useState<SwarmWorker[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchWorkers = useCallback(async () => {
    setLoading(true);
    try {
      setWorkers(await request<SwarmWorker[]>("/swarm/workers"));
    } catch {
      setWorkers([]);
    }
    setLoading(false);
  }, []);

  useEffect(() => {
    fetchWorkers();
    const interval = setInterval(fetchWorkers, 10000);
    return () => clearInterval(interval);
  }, [fetchWorkers]);

  const activeCount = workers.filter((w) => w.status !== "offline").length;
  const workingCount = workers.filter((w) => w.status === "working").length;

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
        <Typography.Title level={3} style={{ margin: 0 }}>
          Swarm Workers
        </Typography.Title>
        <Button icon={<ReloadOutlined />} onClick={fetchWorkers} />
      </div>

      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Card size="small">
            <Statistic title="Total Workers" value={workers.length} />
          </Card>
        </Col>
        <Col span={6}>
          <Card size="small">
            <Statistic
              title="Active"
              value={activeCount}
              valueStyle={{ color: "#52c41a" }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card size="small">
            <Statistic
              title="Working"
              value={workingCount}
              valueStyle={{ color: "#1890ff" }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card size="small">
            <Statistic
              title="Offline"
              value={workers.length - activeCount}
              valueStyle={{ color: "#ff4d4f" }}
            />
          </Card>
        </Col>
      </Row>

      {loading ? (
        <Spin size="large" style={{ display: "block", marginTop: 48 }} />
      ) : workers.length === 0 ? (
        <Empty description="No swarm workers connected. Start workers with 'docker compose up' or 'prowlr swarm worker'." />
      ) : (
        <Row gutter={[16, 16]}>
          {workers.map((w) => {
            const hb = heartbeatAge(w.last_heartbeat);
            return (
              <Col key={w.id} xs={24} sm={12} md={8} lg={6}>
                <Card size="small" hoverable>
                  <div
                    style={{
                      display: "flex",
                      justifyContent: "space-between",
                      marginBottom: 8,
                    }}
                  >
                    <Typography.Text strong>{w.name}</Typography.Text>
                    <Tag color={statusColors[w.status] ?? "default"}>
                      {w.status.toUpperCase()}
                    </Tag>
                  </div>
                  <Typography.Text type="secondary" style={{ fontSize: 12 }}>
                    {w.host}
                  </Typography.Text>
                  <br />
                  {w.current_task && (
                    <Typography.Text style={{ fontSize: 12 }}>
                      Task: {w.current_task}
                    </Typography.Text>
                  )}
                  <div style={{ marginTop: 8 }}>
                    {w.capabilities.map((cap) => (
                      <Tag key={cap} style={{ fontSize: 11, marginBottom: 4 }}>
                        {cap}
                      </Tag>
                    ))}
                  </div>
                  <div style={{ marginTop: 8 }}>
                    <Badge color={hb.color} text={`Heartbeat: ${hb.label}`} />
                  </div>
                </Card>
              </Col>
            );
          })}
        </Row>
      )}
    </div>
  );
}
