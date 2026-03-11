import { useState, useEffect } from "react";
import {
  Typography,
  Input,
  Button,
  Card,
  Row,
  Col,
  Tabs,
  message,
  Spin,
  Empty,
} from "antd";
import { SaveOutlined, ReloadOutlined } from "@ant-design/icons";
import { request } from "../../api/request";

interface SoulFile {
  name: string;
  content: string;
}

async function getSoulFiles(): Promise<SoulFile[]> {
  return request<SoulFile[]>("/agent/soul-files");
}

async function saveSoulFile(name: string, content: string): Promise<void> {
  return request<void>("/agent/soul-files", {
    method: "PUT",
    body: JSON.stringify({ name, content }),
  });
}

export default function SoulEditor() {
  const [files, setFiles] = useState<SoulFile[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeKey, setActiveKey] = useState("SOUL.md");
  const [drafts, setDrafts] = useState<Record<string, string>>({});
  const [saving, setSaving] = useState(false);

  const fetchFiles = async () => {
    setLoading(true);
    try {
      const data = await getSoulFiles();
      setFiles(data);
      const d: Record<string, string> = {};
      data.forEach((f) => (d[f.name] = f.content));
      setDrafts(d);
    } catch {
      setFiles([
        { name: "SOUL.md", content: "" },
        { name: "PROFILE.md", content: "" },
        { name: "AGENTS.md", content: "" },
      ]);
      setDrafts({
        "SOUL.md": "",
        "PROFILE.md": "",
        "AGENTS.md": "",
      });
    }
    setLoading(false);
  };

  useEffect(() => {
    fetchFiles();
  }, []);

  const handleSave = async () => {
    setSaving(true);
    try {
      await saveSoulFile(activeKey, drafts[activeKey] ?? "");
      message.success(`${activeKey} saved`);
    } catch {
      message.error("Failed to save");
    }
    setSaving(false);
  };

  if (loading) {
    return <Spin size="large" style={{ display: "block", marginTop: 48 }} />;
  }

  const tabItems = files.map((f) => ({
    key: f.name,
    label: f.name,
    children: (
      <Row gutter={16}>
        <Col span={12}>
          <Card
            title="Editor"
            size="small"
            extra={
              <Button
                type="primary"
                size="small"
                icon={<SaveOutlined />}
                loading={saving}
                onClick={handleSave}
              >
                Save
              </Button>
            }
          >
            <Input.TextArea
              value={drafts[f.name] ?? ""}
              onChange={(e) =>
                setDrafts((prev) => ({ ...prev, [f.name]: e.target.value }))
              }
              rows={20}
              style={{ fontFamily: "monospace", fontSize: 13 }}
            />
          </Card>
        </Col>
        <Col span={12}>
          <Card title="Preview" size="small">
            <pre
              style={{
                whiteSpace: "pre-wrap",
                wordBreak: "break-word",
                fontSize: 13,
                minHeight: 400,
                maxHeight: 500,
                overflow: "auto",
                margin: 0,
              }}
            >
              {drafts[f.name] || "(empty)"}
            </pre>
          </Card>
        </Col>
      </Row>
    ),
  }));

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
          Soul Editor
        </Typography.Title>
        <Button icon={<ReloadOutlined />} onClick={fetchFiles}>
          Reload
        </Button>
      </div>
      <Typography.Paragraph type="secondary">
        Edit your agent's personality files. SOUL.md defines core personality,
        PROFILE.md sets the agent's background, and AGENTS.md configures
        behavioral rules.
      </Typography.Paragraph>
      {files.length === 0 ? (
        <Empty description="No soul files found" />
      ) : (
        <Tabs
          activeKey={activeKey}
          onChange={setActiveKey}
          items={tabItems}
          type="card"
        />
      )}
    </div>
  );
}
