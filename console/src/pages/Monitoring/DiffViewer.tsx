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
            color: "blue",
            children: (
              <div>
                <Typography.Text type="secondary">
                  Checked at {check.checked_at}
                </Typography.Text>
                {check.content_length != null && (
                  <Typography.Text type="secondary" style={{ display: "block", marginTop: 4 }}>
                    Content length: {check.content_length} chars
                  </Typography.Text>
                )}
              </div>
            ),
          }))}
        />
      )}
    </Modal>
  );
}
