import { Modal, Typography, Timeline, Empty, Spin } from "antd";
import { useEffect, useState } from "react";
import { getMonitorHistory } from "../../api/monitoring";
import type { MonitorCheck } from "../../api/monitoring";

interface Props {
  monitorId: string | null;
  onClose: () => void;
}

export default function DiffViewer({ monitorId, onClose }: Props) {
  const [history, setHistory] = useState<MonitorCheck[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!monitorId) return;
    setLoading(true);
    getMonitorHistory(monitorId)
      .then(setHistory)
      .catch(() => setHistory([]))
      .finally(() => setLoading(false));
  }, [monitorId]);

  return (
    <Modal
      title="Monitor History"
      open={!!monitorId}
      onCancel={onClose}
      footer={null}
      width={700}
    >
      {loading ? (
        <Spin />
      ) : history.length === 0 ? (
        <Empty description="No check history yet" />
      ) : (
        <Timeline
          items={history.map((check) => ({
            color: check.status === "ok" ? "green" : check.status === "changed" ? "orange" : "red",
            children: (
              <div>
                <Typography.Text strong>
                  {check.status.toUpperCase()}
                </Typography.Text>
                <Typography.Text type="secondary" style={{ marginLeft: 8 }}>
                  {check.checked_at}
                </Typography.Text>
                {check.diff && (
                  <pre
                    style={{
                      marginTop: 8,
                      padding: 8,
                      background: "var(--pb-bg-sunken)",
                      borderRadius: 4,
                      fontSize: 12,
                      maxHeight: 200,
                      overflow: "auto",
                    }}
                  >
                    {check.diff}
                  </pre>
                )}
              </div>
            ),
          }))}
        />
      )}
    </Modal>
  );
}
