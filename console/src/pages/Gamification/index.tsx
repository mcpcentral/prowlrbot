import { useEffect, useState } from "react";
import { Card, Tag, Table, Tabs, Tooltip, Empty } from "antd";
import {
  Trophy,
  Star,
  Medal,
  Target,
  Zap,
  Crown,
  Award,
  TrendingUp,
} from "lucide-react";
import {
  getLevelInfo,
  getXPHistory,
  getAchievements,
  listAllAchievements,
  getLeaderboard,
} from "../../api/modules/gamification";
import styles from "./index.module.less";

// ── Types ──
interface LevelInfo {
  level: number;
  level_name: string;
  current_xp: number;
  xp_for_next_level: number;
  total_xp: number;
}

interface XPEvent {
  id: string;
  source: string;
  amount: number;
  timestamp: string;
  description?: string;
}

interface Achievement {
  id: string;
  name: string;
  description: string;
  icon: string;
  xp_reward: number;
  unlocked: boolean;
  unlocked_at?: string;
  category?: string;
}

interface LeaderboardEntry {
  rank: number;
  name: string;
  total_xp: number;
  level: number;
  level_name: string;
  is_current: boolean;
}

// ── Helpers ──
function formatDate(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleDateString(undefined, {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

function formatTimestamp(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

const RANK_COLORS: Record<number, string> = {
  1: "#FFD700",
  2: "#C0C0C0",
  3: "#CD7F32",
};

const RANK_ICONS: Record<number, React.ReactNode> = {
  1: <Crown size={16} />,
  2: <Medal size={16} />,
  3: <Award size={16} />,
};

export default function Gamification() {
  const [levelInfo, setLevelInfo] = useState<LevelInfo | null>(null);
  const [xpHistory, setXpHistory] = useState<XPEvent[]>([]);
  const [achievements, setAchievements] = useState<Achievement[]>([]);
  const [leaderboard, setLeaderboard] = useState<LeaderboardEntry[]>([]);
  const [activeTab, setActiveTab] = useState("level");

  useEffect(() => {
    getLevelInfo("default")
      .then((data: any) => {
        if (data) setLevelInfo(data);
      })
      .catch(() => {});

    getXPHistory("default")
      .then((data: any) => {
        if (Array.isArray(data)) setXpHistory(data);
      })
      .catch(() => {});

    Promise.all([getAchievements("default"), listAllAchievements()])
      .then(([unlocked, all]: any) => {
        const unlockedIds = new Set(
          Array.isArray(unlocked) ? unlocked.map((a: any) => a.id) : []
        );
        const allList: Achievement[] = Array.isArray(all)
          ? all.map((a: any) => ({
              ...a,
              unlocked: unlockedIds.has(a.id),
              unlocked_at: Array.isArray(unlocked)
                ? unlocked.find((u: any) => u.id === a.id)?.unlocked_at
                : undefined,
            }))
          : [];
        setAchievements(allList);
      })
      .catch(() => {});

    getLeaderboard(20)
      .then((data: any) => {
        if (Array.isArray(data)) setLeaderboard(data);
      })
      .catch(() => {});
  }, []);

  // ── XP History Columns ──
  const xpColumns = [
    {
      title: "Source",
      dataIndex: "source",
      key: "source",
      render: (text: string) => (
        <Tag color="blue" style={{ borderRadius: 6 }}>
          {text}
        </Tag>
      ),
    },
    {
      title: "XP",
      dataIndex: "amount",
      key: "amount",
      render: (val: number) => (
        <span style={{ fontWeight: 600, color: val > 0 ? "#52c41a" : "#ff4d4f" }}>
          {val > 0 ? "+" : ""}
          {val}
        </span>
      ),
    },
    {
      title: "Description",
      dataIndex: "description",
      key: "description",
      ellipsis: true,
      render: (text: string) => text || "—",
    },
    {
      title: "Time",
      dataIndex: "timestamp",
      key: "timestamp",
      render: (iso: string) => (
        <span style={{ color: "#8c8c8c", fontSize: 12 }}>
          {formatTimestamp(iso)}
        </span>
      ),
    },
  ];

  // ── Leaderboard Columns ──
  const leaderboardColumns = [
    {
      title: "Rank",
      dataIndex: "rank",
      key: "rank",
      width: 80,
      render: (rank: number) => {
        const color = RANK_COLORS[rank];
        const icon = RANK_ICONS[rank];
        return (
          <div
            className={styles.rankBadge}
            style={
              color
                ? { background: color, color: "#fff" }
                : undefined
            }
          >
            {icon || rank}
          </div>
        );
      },
    },
    {
      title: "Name",
      dataIndex: "name",
      key: "name",
      render: (name: string, record: LeaderboardEntry) => (
        <span style={{ fontWeight: record.is_current ? 700 : 500 }}>
          {name}
          {record.is_current && (
            <Tag color="purple" style={{ marginLeft: 8, borderRadius: 6 }}>
              You
            </Tag>
          )}
        </span>
      ),
    },
    {
      title: "XP",
      dataIndex: "total_xp",
      key: "total_xp",
      render: (xp: number) => (
        <span style={{ fontWeight: 600 }}>{xp.toLocaleString()}</span>
      ),
    },
    {
      title: "Level",
      dataIndex: "level",
      key: "level",
      render: (level: number, record: LeaderboardEntry) => (
        <Tooltip title={record.level_name}>
          <Tag color="gold" style={{ borderRadius: 6 }}>
            Lv. {level}
          </Tag>
        </Tooltip>
      ),
    },
  ];

  // ── XP progress percentage ──
  const xpPercent =
    levelInfo && levelInfo.xp_for_next_level > 0
      ? Math.min(
          100,
          Math.round((levelInfo.current_xp / levelInfo.xp_for_next_level) * 100)
        )
      : 0;

  return (
    <div className={styles.gamification}>
      {/* ── Header ── */}
      <div className={styles.header}>
        <Trophy size={22} color="#FFD700" />
        Gamification
      </div>

      {/* ── Tabs ── */}
      <Tabs
        activeKey={activeTab}
        onChange={setActiveTab}
        items={[
          {
            key: "level",
            label: (
              <span style={{ display: "flex", alignItems: "center", gap: 6 }}>
                <Star size={14} /> Level & XP
              </span>
            ),
            children: (
              <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
                {/* Level Card */}
                <div className={styles.levelCard}>
                  <div className="levelNumber">
                    Level {levelInfo?.level ?? "—"}
                  </div>
                  <h2>
                    <Zap size={24} />
                    {levelInfo?.level_name ?? "Loading..."}
                  </h2>

                  <div className={styles.xpBar}>
                    <div
                      className={styles.xpFill}
                      style={{ width: `${xpPercent}%` }}
                    />
                  </div>
                  <div className={styles.xpText}>
                    <span>
                      {levelInfo?.current_xp?.toLocaleString() ?? 0} XP
                    </span>
                    <span>
                      {levelInfo?.xp_for_next_level?.toLocaleString() ?? 0} XP
                      to next level
                    </span>
                  </div>

                  {/* Stat cards row */}
                  <div className={styles.statsGrid} style={{ marginTop: 8 }}>
                    <div className={styles.statCard}>
                      <TrendingUp size={18} color="#6B5CE7" />
                      <div>
                        <div style={{ fontWeight: 700, fontSize: 18, color: "#1a1a2e" }}>
                          {levelInfo?.total_xp?.toLocaleString() ?? 0}
                        </div>
                        <div style={{ fontSize: 12, color: "#8c8c8c" }}>
                          Total XP
                        </div>
                      </div>
                    </div>
                    <div className={styles.statCard}>
                      <Target size={18} color="#52c41a" />
                      <div>
                        <div style={{ fontWeight: 700, fontSize: 18, color: "#1a1a2e" }}>
                          {xpPercent}%
                        </div>
                        <div style={{ fontSize: 12, color: "#8c8c8c" }}>
                          Progress
                        </div>
                      </div>
                    </div>
                    <div className={styles.statCard}>
                      <Award size={18} color="#fa8c16" />
                      <div>
                        <div style={{ fontWeight: 700, fontSize: 18, color: "#1a1a2e" }}>
                          {achievements.filter((a) => a.unlocked).length}
                        </div>
                        <div style={{ fontSize: 12, color: "#8c8c8c" }}>
                          Achievements
                        </div>
                      </div>
                    </div>
                    <div className={styles.statCard}>
                      <Star size={18} color="#FFD700" />
                      <div>
                        <div style={{ fontWeight: 700, fontSize: 18, color: "#1a1a2e" }}>
                          {levelInfo?.level ?? 0}
                        </div>
                        <div style={{ fontSize: 12, color: "#8c8c8c" }}>
                          Level
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                {/* XP History Table */}
                <Card
                  title={
                    <span style={{ display: "flex", alignItems: "center", gap: 8 }}>
                      <Zap size={16} /> Recent XP Gains
                    </span>
                  }
                  style={{ borderRadius: 12 }}
                >
                  {xpHistory.length === 0 ? (
                    <Empty description="No XP events yet" />
                  ) : (
                    <Table
                      dataSource={xpHistory}
                      columns={xpColumns}
                      rowKey="id"
                      pagination={{ pageSize: 10 }}
                      size="small"
                    />
                  )}
                </Card>
              </div>
            ),
          },
          {
            key: "achievements",
            label: (
              <span style={{ display: "flex", alignItems: "center", gap: 6 }}>
                <Award size={14} /> Achievements
              </span>
            ),
            children: (
              <div>
                {achievements.length === 0 ? (
                  <Empty description="No achievements available" />
                ) : (
                  <div className={styles.achievements}>
                    {achievements.map((ach) => (
                      <div
                        key={ach.id}
                        className={`${styles.achievementCard} ${
                          !ach.unlocked ? styles.achievementLocked : ""
                        }`}
                      >
                        <div className={styles.achievementIcon}>
                          {ach.icon || "\u{1F3C6}"}
                        </div>
                        <div style={{ flex: 1, minWidth: 0 }}>
                          <div
                            style={{
                              fontWeight: 600,
                              fontSize: 14,
                              color: "#1a1a2e",
                              marginBottom: 4,
                            }}
                          >
                            {ach.name}
                          </div>
                          <div
                            style={{
                              fontSize: 12,
                              color: "#8c8c8c",
                              lineHeight: 1.4,
                              marginBottom: 8,
                            }}
                          >
                            {ach.description}
                          </div>
                          <div
                            style={{
                              display: "flex",
                              alignItems: "center",
                              gap: 8,
                            }}
                          >
                            <Tag
                              color={ach.unlocked ? "gold" : "default"}
                              style={{ borderRadius: 6 }}
                            >
                              +{ach.xp_reward} XP
                            </Tag>
                            {ach.unlocked && ach.unlocked_at && (
                              <span style={{ fontSize: 11, color: "#bfbfbf" }}>
                                Unlocked {formatDate(ach.unlocked_at)}
                              </span>
                            )}
                            {!ach.unlocked && (
                              <span style={{ fontSize: 11, color: "#bfbfbf" }}>
                                Locked
                              </span>
                            )}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ),
          },
          {
            key: "leaderboard",
            label: (
              <span style={{ display: "flex", alignItems: "center", gap: 6 }}>
                <Trophy size={14} /> Leaderboard
              </span>
            ),
            children: (
              <div className={styles.leaderboard}>
                {leaderboard.length === 0 ? (
                  <Empty description="No leaderboard data" />
                ) : (
                  <Table
                    dataSource={leaderboard}
                    columns={leaderboardColumns}
                    rowKey="rank"
                    pagination={false}
                    size="middle"
                    rowClassName={(record: LeaderboardEntry) =>
                      record.is_current ? "ant-table-row-selected" : ""
                    }
                  />
                )}
              </div>
            ),
          },
        ]}
      />
    </div>
  );
}
