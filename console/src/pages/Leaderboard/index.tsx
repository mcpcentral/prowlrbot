import React, { useState } from "react";
import { Badge, Button, Table, Tag, Typography } from "antd";
import { ReloadOutlined, TrophyOutlined } from "@ant-design/icons";
import { useLeaderboard, LeaderboardEntry } from "../../hooks/useLeaderboard";

const { Title, Text } = Typography;

const LEVEL_COLORS = ["default", "green", "blue", "purple", "gold", "red"];

export const Leaderboard: React.FC = () => {
  const [entityType, setEntityType] = useState<"agent" | "user">("agent");
  const { entries, lastUpdate, refresh } = useLeaderboard(entityType);

  const columns = [
    {
      title: "#",
      key: "rank",
      render: (_: unknown, __: LeaderboardEntry, index: number) => (
        <span style={{ fontWeight: 700, color: index < 3 ? "#faad14" : undefined }}>
          {index + 1}
        </span>
      ),
      width: 48,
    },
    {
      title: "Name",
      dataIndex: "entity_id",
      key: "entity_id",
      render: (id: string) => <Text strong>{id}</Text>,
    },
    {
      title: "Level",
      dataIndex: "level",
      key: "level",
      render: (level: number) => (
        <Tag color={LEVEL_COLORS[Math.min(level - 1, LEVEL_COLORS.length - 1)]}>
          Lv {level}
        </Tag>
      ),
      width: 80,
    },
    {
      title: "XP",
      dataIndex: "total_xp",
      key: "total_xp",
      render: (xp: number) => <>{xp.toLocaleString()} XP</>,
      sorter: (a: LeaderboardEntry, b: LeaderboardEntry) => b.total_xp - a.total_xp,
      width: 130,
    },
  ];

  return (
    <div style={{ maxWidth: 700, margin: "0 auto", padding: 24 }}>
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: 16,
        }}
      >
        <Title level={3} style={{ margin: 0 }}>
          <TrophyOutlined style={{ marginRight: 8, color: "#faad14" }} />
          Leaderboard
        </Title>
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          {lastUpdate && (
            <Badge
              status="processing"
              text={
                <Text type="secondary" style={{ fontSize: 12 }}>
                  Live &middot; {lastUpdate.toLocaleTimeString()}
                </Text>
              }
            />
          )}
          <Button
            icon={<ReloadOutlined />}
            size="small"
            onClick={refresh}
          />
          <Button
            size="small"
            type={entityType === "agent" ? "primary" : "default"}
            onClick={() => setEntityType("agent")}
          >
            Agents
          </Button>
          <Button
            size="small"
            type={entityType === "user" ? "primary" : "default"}
            onClick={() => setEntityType("user")}
          >
            Users
          </Button>
        </div>
      </div>

      {entries.length === 0 ? (
        <div style={{ textAlign: "center", color: "#8c8c8c", padding: 48 }}>
          No activity yet. Run an agent task to earn XP.
        </div>
      ) : (
        <Table
          dataSource={entries}
          columns={columns}
          rowKey="entity_id"
          pagination={false}
          size="small"
        />
      )}
    </div>
  );
};

export default Leaderboard;
