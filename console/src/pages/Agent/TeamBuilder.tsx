import { useState, useEffect } from "react";
import {
  Typography,
  Card,
  Row,
  Col,
  Button,
  Select,
  Input,
  Tag,
  List,
  Empty,
  Spin,
  Modal,
  Form,
  message,
} from "antd";
import {
  PlusOutlined,
  DeleteOutlined,
  TeamOutlined,
  ReloadOutlined,
} from "@ant-design/icons";
import { request } from "../../api/request";

interface TeamAgent {
  id: string;
  name: string;
  role: string;
}

interface Team {
  id: string;
  name: string;
  coordination_mode: "sequential" | "parallel" | "consensus";
  agents: TeamAgent[];
}

async function getTeams(): Promise<Team[]> {
  return request<Team[]>("/teams");
}

async function createTeam(team: Partial<Team>): Promise<Team> {
  return request<Team>("/teams", {
    method: "POST",
    body: JSON.stringify(team),
  });
}

async function deleteTeam(teamId: string): Promise<void> {
  return request<void>(`/teams/${teamId}`, { method: "DELETE" });
}

const modeDescriptions: Record<string, string> = {
  sequential: "Agents work one after another, passing results along the chain",
  parallel: "All agents work simultaneously, results are merged",
  consensus:
    "Agents vote on decisions, majority wins (requires 3+ agents)",
};

const modeColors: Record<string, string> = {
  sequential: "blue",
  parallel: "green",
  consensus: "purple",
};

export default function TeamBuilder() {
  const [teams, setTeams] = useState<Team[]>([]);
  const [loading, setLoading] = useState(true);
  const [modalOpen, setModalOpen] = useState(false);
  const [form] = Form.useForm();

  const fetchTeams = async () => {
    setLoading(true);
    try {
      setTeams(await getTeams());
    } catch {
      setTeams([]);
    }
    setLoading(false);
  };

  useEffect(() => {
    fetchTeams();
  }, []);

  const handleCreate = async () => {
    try {
      const values = await form.validateFields();
      await createTeam({
        name: values.name,
        coordination_mode: values.coordination_mode,
        agents: [],
      });
      setModalOpen(false);
      form.resetFields();
      message.success("Team created");
      fetchTeams();
    } catch {
      message.error("Failed to create team");
    }
  };

  const handleDelete = async (teamId: string) => {
    try {
      await deleteTeam(teamId);
      message.success("Team deleted");
      fetchTeams();
    } catch {
      message.error("Failed to delete team");
    }
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
        <Typography.Title level={3} style={{ margin: 0 }}>
          Team Builder
        </Typography.Title>
        <div>
          <Button
            icon={<ReloadOutlined />}
            onClick={fetchTeams}
            style={{ marginRight: 8 }}
          />
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => setModalOpen(true)}
          >
            Create Team
          </Button>
        </div>
      </div>

      <Typography.Paragraph type="secondary">
        Build agent teams with different coordination modes. Teams can work
        sequentially, in parallel, or use consensus voting.
      </Typography.Paragraph>

      {loading ? (
        <Spin size="large" style={{ display: "block", marginTop: 48 }} />
      ) : teams.length === 0 ? (
        <Empty description="No teams configured. Create one to get started." />
      ) : (
        <Row gutter={[16, 16]}>
          {teams.map((team) => (
            <Col key={team.id} xs={24} sm={12} md={8}>
              <Card
                title={
                  <span>
                    <TeamOutlined style={{ marginRight: 8 }} />
                    {team.name}
                  </span>
                }
                extra={
                  <Button
                    type="text"
                    danger
                    size="small"
                    icon={<DeleteOutlined />}
                    onClick={() => handleDelete(team.id)}
                  />
                }
              >
                <Tag color={modeColors[team.coordination_mode] ?? "default"}>
                  {team.coordination_mode.toUpperCase()}
                </Tag>
                <Typography.Text
                  type="secondary"
                  style={{ display: "block", margin: "8px 0", fontSize: 12 }}
                >
                  {modeDescriptions[team.coordination_mode]}
                </Typography.Text>
                {team.agents.length === 0 ? (
                  <Typography.Text type="secondary" italic>
                    No agents assigned yet
                  </Typography.Text>
                ) : (
                  <List
                    size="small"
                    dataSource={team.agents}
                    renderItem={(agent) => (
                      <List.Item>
                        <Typography.Text>{agent.name}</Typography.Text>
                        <Tag>{agent.role}</Tag>
                      </List.Item>
                    )}
                  />
                )}
              </Card>
            </Col>
          ))}
        </Row>
      )}

      <Modal
        title="Create Team"
        open={modalOpen}
        onOk={handleCreate}
        onCancel={() => setModalOpen(false)}
        okText="Create"
      >
        <Form form={form} layout="vertical">
          <Form.Item
            name="name"
            label="Team Name"
            rules={[{ required: true, message: "Name is required" }]}
          >
            <Input placeholder="e.g., Code Review Squad" />
          </Form.Item>
          <Form.Item
            name="coordination_mode"
            label="Coordination Mode"
            initialValue="sequential"
          >
            <Select
              options={[
                { label: "Sequential — agents work in order", value: "sequential" },
                { label: "Parallel — agents work simultaneously", value: "parallel" },
                { label: "Consensus — agents vote on decisions", value: "consensus" },
              ]}
            />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}
