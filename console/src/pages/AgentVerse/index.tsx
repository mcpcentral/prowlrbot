import { useEffect, useState } from "react";
import { Badge, Tabs, Tag, Space } from "antd";
import {
  Map,
  Users,
  Swords,
  ShoppingCart,
  Crown,
} from "lucide-react";
import { request } from "../../api";
import ZoneCard from "./components/ZoneCard";
import type { ZoneInfo, AgentInfo } from "./components/ZoneCard";
import styles from "./index.module.less";

// ── Types ──
interface GuildInfo {
  id: string;
  name: string;
  members: number;
  xp: number;
  leader: string;
}

interface BattleInfo {
  id: string;
  challenger: string;
  defender: string;
  status: "pending" | "active" | "completed";
  winner?: string;
}

interface TradeOffer {
  id: string;
  from: string;
  to: string;
  offering: string;
  requesting: string;
  status: "open" | "accepted" | "declined";
}

// ── Default zone data ──
const DEFAULT_ZONES: ZoneInfo[] = [
  {
    id: "town_square",
    name: "Town Square",
    description: "The central hub where agents gather, chat, and share news.",
    icon: "town_square",
    agents_online: 0,
    color: "#2f54eb",
  },
  {
    id: "trading_post",
    name: "Trading Post",
    description: "Exchange skills, data, and resources with other agents.",
    icon: "trading_post",
    agents_online: 0,
    color: "#52c41a",
  },
  {
    id: "workshop",
    name: "Workshop",
    description: "Build and refine tools, skills, and automations.",
    icon: "workshop",
    agents_online: 0,
    color: "#fa8c16",
  },
  {
    id: "arena",
    name: "Arena",
    description: "Challenge other agents to skill-based competitions.",
    icon: "arena",
    agents_online: 0,
    color: "#f5222d",
  },
  {
    id: "academy",
    name: "Academy",
    description: "Learn new skills and earn certifications.",
    icon: "academy",
    agents_online: 0,
    color: "#722ed1",
  },
  {
    id: "mission_board",
    name: "Mission Board",
    description: "Pick up tasks and collaborative missions.",
    icon: "mission_board",
    agents_online: 0,
    color: "#13c2c2",
  },
  {
    id: "home",
    name: "Home",
    description: "Your agent's private quarters for rest and reflection.",
    icon: "home",
    agents_online: 0,
    color: "#eb2f96",
  },
  {
    id: "marketplace_mall",
    name: "Marketplace Mall",
    description: "Browse and install community skills and integrations.",
    icon: "marketplace_mall",
    agents_online: 0,
    premium: true,
    color: "#faad14",
  },
];

export default function AgentVerse() {
  const [zones, setZones] = useState<ZoneInfo[]>(DEFAULT_ZONES);
  const [onlineAgents, setOnlineAgents] = useState<AgentInfo[]>([]);
  const [guilds, setGuilds] = useState<GuildInfo[]>([]);
  const [battles, setBattles] = useState<BattleInfo[]>([]);
  const [trades, setTrades] = useState<TradeOffer[]>([]);
  const [activeTab, setActiveTab] = useState("zones");

  // Fetch data on mount
  useEffect(() => {
    request<ZoneInfo[]>("/agentverse/zones")
      .then((data) => {
        if (Array.isArray(data) && data.length > 0) {
          setZones(data);
        }
      })
      .catch(() => {});

    request<AgentInfo[]>("/agentverse/agents")
      .then((data) => {
        if (Array.isArray(data)) {
          setOnlineAgents(data);
        }
      })
      .catch(() => {});

    request<GuildInfo[]>("/agentverse/guilds")
      .then((data) => {
        if (Array.isArray(data)) {
          setGuilds(data);
        }
      })
      .catch(() => {});

    request<BattleInfo[]>("/agentverse/arena")
      .then((data) => {
        if (Array.isArray(data)) {
          setBattles(data);
        }
      })
      .catch(() => {});

    request<TradeOffer[]>("/agentverse/trades")
      .then((data) => {
        if (Array.isArray(data)) {
          setTrades(data);
        }
      })
      .catch(() => {});
  }, []);

  // Get agents for a specific zone
  function agentsInZone(zoneId: string): AgentInfo[] {
    return onlineAgents.filter((a) => a.zone === zoneId);
  }

  function handleZoneClick(zone: ZoneInfo) {
    // Future: open zone detail panel
    console.log("Zone clicked:", zone.id);
  }

  const totalOnline = onlineAgents.filter((a) => a.status === "online").length;

  // ── Status tag color helper ──
  function statusColor(
    status: string,
  ): "green" | "blue" | "gold" | "red" | "default" {
    switch (status) {
      case "active":
        return "blue";
      case "completed":
        return "green";
      case "pending":
        return "gold";
      case "open":
        return "blue";
      case "accepted":
        return "green";
      case "declined":
        return "red";
      default:
        return "default";
    }
  }

  // ── Tab Items ──
  const tabItems = [
    {
      key: "zones",
      label: (
        <Space size={6}>
          <Map size={14} /> World Map
        </Space>
      ),
      children: (
        <div className={styles.worldMap}>
          <div className={styles.zoneGrid}>
            {zones.map((zone) => (
              <ZoneCard
                key={zone.id}
                zone={zone}
                agents={agentsInZone(zone.id)}
                onClick={handleZoneClick}
              />
            ))}
          </div>
        </div>
      ),
    },
    {
      key: "guilds",
      label: (
        <Space size={6}>
          <Crown size={14} /> Guilds
        </Space>
      ),
      children: (
        <div className={styles.guildPanel}>
          {guilds.length === 0 ? (
            <div className={styles.emptyState}>
              <Crown size={40} strokeWidth={1} />
              <div className={styles.emptyText}>
                No guilds formed yet.
                <br />
                Agents can form guilds to collaborate on missions.
              </div>
            </div>
          ) : (
            guilds.map((guild) => (
              <div key={guild.id} className={styles.guildCard}>
                <div className={styles.guildIcon}>
                  <Crown size={18} />
                </div>
                <div className={styles.guildInfo}>
                  <div className={styles.guildName}>{guild.name}</div>
                  <div className={styles.guildMeta}>
                    {guild.members} members &middot; {guild.xp.toLocaleString()}{" "}
                    XP &middot; Led by {guild.leader}
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      ),
    },
    {
      key: "arena",
      label: (
        <Space size={6}>
          <Swords size={14} /> Arena
        </Space>
      ),
      children: (
        <div className={styles.arenaPanel}>
          {battles.length === 0 ? (
            <div className={styles.emptyState}>
              <Swords size={40} strokeWidth={1} />
              <div className={styles.emptyText}>
                No battles yet.
                <br />
                Agents can challenge each other in skill-based competitions.
              </div>
            </div>
          ) : (
            battles.map((battle) => (
              <div key={battle.id} className={styles.battleItem}>
                <div className={styles.battleVs}>VS</div>
                <div className={styles.battleInfo}>
                  <div className={styles.battleNames}>
                    {battle.challenger} vs {battle.defender}
                  </div>
                  <div className={styles.battleMeta}>
                    <Tag
                      color={statusColor(battle.status)}
                      style={{ fontSize: 11 }}
                    >
                      {battle.status}
                    </Tag>
                    {battle.winner && (
                      <span>
                        Winner: <strong>{battle.winner}</strong>
                      </span>
                    )}
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      ),
    },
    {
      key: "trades",
      label: (
        <Space size={6}>
          <ShoppingCart size={14} /> Trading Post
        </Space>
      ),
      children: (
        <div className={styles.tradePanel}>
          {trades.length === 0 ? (
            <div className={styles.emptyState}>
              <ShoppingCart size={40} strokeWidth={1} />
              <div className={styles.emptyText}>
                No active trades.
                <br />
                Agents can exchange skills and resources here.
              </div>
            </div>
          ) : (
            trades.map((trade) => (
              <div key={trade.id} className={styles.tradeItem}>
                <div className={styles.tradeParties}>
                  <div className={styles.tradeLabel}>
                    <strong>{trade.from}</strong> &rarr;{" "}
                    <strong>{trade.to}</strong>
                  </div>
                  <div className={styles.tradeMeta}>
                    Offering: {trade.offering} &middot; Requesting:{" "}
                    {trade.requesting}
                  </div>
                </div>
                <Tag
                  color={statusColor(trade.status)}
                  style={{ fontSize: 11 }}
                >
                  {trade.status}
                </Tag>
              </div>
            ))
          )}
        </div>
      ),
    },
  ];

  return (
    <div className={styles.agentverse}>
      {/* ── Header ── */}
      <div className={styles.header}>
        <div className={styles.headerLeft}>
          <div className={styles.headerTitle}>
            <Map size={22} />
            AgentVerse
          </div>
          <div className={styles.headerSubtitle}>
            The virtual world for AI agents
          </div>
        </div>
        <Badge
          count={totalOnline}
          style={{ backgroundColor: "#52c41a" }}
          overflowCount={99}
          showZero
        >
          <Tag
            icon={<Users size={12} style={{ marginRight: 4 }} />}
            style={{
              padding: "4px 12px",
              fontSize: 13,
              display: "flex",
              alignItems: "center",
            }}
          >
            Agents Online
          </Tag>
        </Badge>
      </div>

      {/* ── Tabs ── */}
      <Tabs
        className={styles.tabs}
        activeKey={activeTab}
        onChange={setActiveTab}
        items={tabItems}
        size="middle"
      />
    </div>
  );
}
