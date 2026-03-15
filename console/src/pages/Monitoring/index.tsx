import { useEffect, useState, useCallback } from "react";
import {
  Typography,
  Spin,
  Empty,
  Button,
  Modal,
  Form,
  Input,
  Select,
  InputNumber,
  message,
} from "antd";
import { PlusOutlined, ReloadOutlined } from "@ant-design/icons";
import StatusGrid from "./StatusGrid";
import DiffViewer from "./DiffViewer";
import {
  getMonitors,
  createMonitor,
  deleteMonitor,
} from "../../api/monitoring";
import type { Monitor } from "../../api/monitoring";

export default function MonitoringPage() {
  const [monitors, setMonitors] = useState<Monitor[]>([]);
  const [loading, setLoading] = useState(true);
  const [modalOpen, setModalOpen] = useState(false);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [form] = Form.useForm();

  const fetchMonitors = useCallback(async () => {
    setLoading(true);
    try {
      setMonitors(await getMonitors());
    } catch (e) {
      setMonitors([]);
      const msg = e instanceof Error ? e.message : "Failed to load monitors";
      message.error(msg);
    }
    setLoading(false);
  }, []);

  useEffect(() => {
    fetchMonitors();
  }, [fetchMonitors]);

  const handleCreate = async () => {
    try {
      const values = await form.validateFields();
      await createMonitor(values);
      setModalOpen(false);
      form.resetFields();
      message.success("Monitor created");
      fetchMonitors();
    } catch (e) {
      if (e && typeof e === "object" && "errorFields" in e) return;
      const msg = e instanceof Error ? e.message : "Failed to create monitor";
      message.error(msg);
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await deleteMonitor(id);
      message.success("Monitor deleted");
      fetchMonitors();
    } catch (e) {
      const msg = e instanceof Error ? e.message : "Failed to delete monitor";
      message.error(msg);
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
          Monitoring
        </Typography.Title>
        <div>
          <Button
            icon={<ReloadOutlined />}
            onClick={fetchMonitors}
            style={{ marginRight: 8 }}
          />
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => setModalOpen(true)}
          >
            Add Monitor
          </Button>
        </div>
      </div>

      {loading ? (
        <Spin size="large" style={{ display: "block", marginTop: 48 }} />
      ) : monitors.length === 0 ? (
        <Empty description="No monitors configured. Add one to get started." />
      ) : (
        <StatusGrid
          monitors={monitors}
          onSelect={setSelectedId}
          onDelete={handleDelete}
        />
      )}

      <DiffViewer
        monitorId={selectedId}
        onClose={() => setSelectedId(null)}
      />

      <Modal
        title="Add Monitor"
        open={modalOpen}
        onOk={handleCreate}
        onCancel={() => setModalOpen(false)}
        okText="Create"
      >
        <Form form={form} layout="vertical">
          <Form.Item
            name="url"
            label="URL"
            rules={[
              { required: true, message: "URL is required" },
              { type: "url", message: "Must be a valid URL" },
            ]}
          >
            <Input placeholder="https://example.com" />
          </Form.Item>
          <Form.Item name="type" label="Type" initialValue="web">
            <Select
              options={[
                { label: "Web Page", value: "web" },
                { label: "API Endpoint", value: "api" },
              ]}
            />
          </Form.Item>
          <Form.Item
            name="interval_minutes"
            label="Check Interval (minutes)"
            initialValue={60}
          >
            <InputNumber min={1} max={1440} style={{ width: "100%" }} />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}
