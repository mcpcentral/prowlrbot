import { useEffect, useState, useCallback } from "react";
import {
  Typography,
  Card,
  Row,
  Col,
  Tag,
  Badge,
  Spin,
  Statistic,
  Button,
  Alert,
  Steps,
} from "antd";
import { ReloadOutlined, CheckCircleOutlined, CloseCircleOutlined } from "@ant-design/icons";
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

interface SwarmStatus {
  available: boolean;
  docker: boolean;
  redis: boolean;
  workers: SwarmWorker[] | null;
}

const statusColors: Record<string, string> = {
  idle: "green",
  working: "blue",
  offline: "red",
};

function heartbeatAge(ts: string): { color: string; label: string } {
  if (!ts) return { color: "default", label: "N/A" };
  const age = (Date.now() - new Date(ts).getTime()) / 1000;
  if (age < 60) return { color: "green", label: `${Math.round(age)}s ago` };
  if (age < 120) return { color: "orange", label: `${Math.round(age)}s ago` };
  return { color: "red", label: `${Math.round(age / 60)}m ago` };
}

export default function SwarmPage() {
  const [status, setStatus] = useState<SwarmStatus | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchStatus = useCallback(async () => {
    setLoading(true);
    try {
      const data = await request<SwarmStatus>("/swarm/status");
      setStatus(data);
    } catch {
      setStatus(null);
    }
    setLoading(false);
  }, []);

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, 10000);
    return () => clearInterval(interval);
  }, [fetchStatus]);

  if (loading && !status) {
    return (
      <div style={{ padding: 24 }}>
        <Spin size="large" style={{ display: "block", marginTop: 48 }} />
      </div>
    );
  }

  const workers = status?.workers ?? [];
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
        <Button icon={<ReloadOutlined />} onClick={fetchStatus} loading={loading} />
      </div>

      {/* Dependency status */}
      {status && !status.available ? (
        <div style={{ maxWidth: 600, margin: "24px auto" }}>
          <Alert
            type="info"
            showIcon
            message="Swarm Dependencies Required"
            description="The swarm requires Docker and Redis to manage distributed workers."
            style={{ marginBottom: 24 }}
          />
          <Card title="Setup Guide" style={{ marginBottom: 24 }}>
            <Steps
              direction="vertical"
              current={-1}
              items={[
                {
                  title: "Docker",
                  description: status.docker
                    ? "Docker is running"
                    : "Install Docker Desktop or run: brew install docker",
                  status: status.docker ? "finish" : "wait",
                  icon: status.docker ? <CheckCircleOutlined /> : <CloseCircleOutlined />,
                },
                {
                  title: "Redis",
                  description: status.redis
                    ? "Redis is running"
                    : "Run: brew install redis && brew services start redis",
                  status: status.redis ? "finish" : "wait",
                  icon: status.redis ? <CheckCircleOutlined /> : <CloseCircleOutlined />,
                },
                {
                  title: "Start Workers",
                  description:
                    "Run: docker compose -f docker-compose.swarm.yml up -d",
                  status: "wait",
                },
              ]}
            />
          </Card>
          <Button type="primary" onClick={fetchStatus}>
            Check Again
          </Button>
        </div>
      ) : (
        <>
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

          {workers.length === 0 ? (
            <Alert
              type="info"
              showIcon
              message="No workers running"
              description="Start workers with: docker compose -f docker-compose.swarm.yml up -d"
            />
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
        </>
      )}
    </div>
  );
}
