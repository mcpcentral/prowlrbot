import { useEffect, useState } from "react";
import {
  Card,
  Col,
  Row,
  Statistic,
  Tag,
  Button,
  Table,
  Empty,
  Spin,
  Typography,
  Divider,
  Space,
} from "antd";
import { CheckOutlined, CrownOutlined, TeamOutlined, UserOutlined } from "@ant-design/icons";
import { getCreditBalance, getCreditTransactions } from "../../api/modules/credits";

const { Title, Text, Paragraph } = Typography;

const TIERS = [
  {
    name: "Free",
    price: "$0/mo",
    credits: 1_000,
    color: "default" as const,
    icon: <UserOutlined />,
    features: ["1 agent", "1,000 credits/mo", "Basic monitoring", "Community support"],
    cta: "Current Plan",
    ctaDisabled: true,
  },
  {
    name: "Pro",
    price: "$19/mo",
    credits: 10_000,
    color: "blue" as const,
    icon: <CrownOutlined />,
    features: ["5 agents", "10,000 credits/mo", "Advanced monitoring", "Priority support", "API access"],
    cta: "Upgrade to Pro",
    ctaDisabled: false,
  },
  {
    name: "Team",
    price: "$49/mo",
    credits: 50_000,
    color: "purple" as const,
    icon: <TeamOutlined />,
    features: ["Unlimited agents", "50,000 credits/mo", "War Room", "Team collaboration", "SLA support"],
    cta: "Upgrade to Team",
    ctaDisabled: false,
  },
];

const txColumns = [
  { title: "Description", dataIndex: "description", key: "description" },
  {
    title: "Amount",
    dataIndex: "amount",
    key: "amount",
    render: (v: number) => (
      <Text style={{ color: v >= 0 ? "var(--pb-status-success)" : "var(--pb-status-error)" }}>
        {v >= 0 ? `+${v}` : v}
      </Text>
    ),
  },
  {
    title: "Date",
    dataIndex: "created_at",
    key: "created_at",
    render: (v: string) => v ? new Date(v).toLocaleString() : "—",
  },
];

export default function CreditsPage() {
  const [balance, setBalance] = useState<number | null>(null);
  const [tier, setTier] = useState("Free");
  const [transactions, setTransactions] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      try {
        const bal = await getCreditBalance() as any;
        setBalance(bal?.balance ?? 0);
        setTier(bal?.tier ?? "Free");
      } catch {
        setBalance(0);
      }
      try {
        const txs = await getCreditTransactions();
        setTransactions(Array.isArray(txs) ? txs : []);
      } catch {
        setTransactions([]);
      }
      setLoading(false);
    };
    load();
  }, []);

  return (
    <div style={{ padding: 24, maxWidth: 1100, margin: "0 auto" }}>
      <Title level={3}>Credits &amp; Plans</Title>
      <Paragraph type="secondary">
        Credits power marketplace installs, agent runs, and advanced features.
      </Paragraph>

      {loading ? (
        <Spin size="large" style={{ display: "block", margin: "60px auto" }} />
      ) : (
        <>
          <Row gutter={16} style={{ marginBottom: 32 }}>
            <Col span={8}>
              <Card>
                <Statistic
                  title="Available Credits"
                  value={balance ?? 0}
                  prefix="⚡"
                  valueStyle={{ color: "var(--pb-status-info)" }}
                />
              </Card>
            </Col>
            <Col span={8}>
              <Card>
                <Statistic
                  title="Current Plan"
                  value={tier}
                  prefix={<Tag color={tier === "Free" ? "default" : tier === "Pro" ? "blue" : "purple"}>{tier}</Tag>}
                />
              </Card>
            </Col>
          </Row>

          <Divider orientation="left">Plans</Divider>

          <Row gutter={16} style={{ marginBottom: 32 }}>
            {TIERS.map((t) => (
              <Col key={t.name} span={8}>
                <Card
                  style={{ height: "100%", borderColor: t.name === tier ? "var(--pb-brand-primary)" : undefined }}
                  title={
                    <Space>
                      {t.icon}
                      <span>{t.name}</span>
                      {t.name === tier && <Tag color="blue">Current</Tag>}
                    </Space>
                  }
                  extra={<Text strong>{t.price}</Text>}
                >
                  <ul style={{ paddingLeft: 16, marginBottom: 16 }}>
                    {t.features.map((f) => (
                      <li key={f} style={{ marginBottom: 4 }}>
                        <CheckOutlined style={{ color: "var(--pb-status-success)", marginRight: 6 }} />
                        {f}
                      </li>
                    ))}
                  </ul>
                  <Button
                    type={t.ctaDisabled ? "default" : "primary"}
                    disabled={t.ctaDisabled || t.name === tier}
                    block
                    onClick={() => {
                      window.open("https://prowlrbot.com/pricing", "_blank");
                    }}
                  >
                    {t.name === tier ? "Current Plan" : t.cta}
                  </Button>
                </Card>
              </Col>
            ))}
          </Row>

          <Divider orientation="left">Transaction History</Divider>

          {transactions.length === 0 ? (
            <Empty description="No transactions yet. Credits are logged when you install marketplace items or run agents." />
          ) : (
            <Table
              dataSource={transactions}
              columns={txColumns}
              rowKey={(r) => r.id ?? r.created_at}
              pagination={{ pageSize: 10 }}
              size="small"
            />
          )}
        </>
      )}
    </div>
  );
}
