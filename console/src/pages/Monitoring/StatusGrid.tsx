import { Card, Tag, Row, Col, Typography, Button, Popconfirm } from "antd";
import { DeleteOutlined } from "@ant-design/icons";
import type { Monitor } from "../../api/monitoring";

const statusColors: Record<string, string> = {
  ok: "green",
  changed: "orange",
  error: "red",
  unknown: "default",
};

interface Props {
  monitors: Monitor[];
  onSelect: (id: string) => void;
  onDelete: (id: string) => void;
}

export default function StatusGrid({ monitors, onSelect, onDelete }: Props) {
  return (
    <Row gutter={[16, 16]}>
      {monitors.map((m) => (
        <Col key={m.id} xs={24} sm={12} md={8} lg={6}>
          <Card
            hoverable
            onClick={() => onSelect(m.id)}
            size="small"
            extra={
              <Popconfirm
                title="Delete this monitor?"
                onConfirm={(e) => {
                  e?.stopPropagation();
                  onDelete(m.id);
                }}
                onCancel={(e) => e?.stopPropagation()}
              >
                <Button
                  type="text"
                  size="small"
                  danger
                  icon={<DeleteOutlined />}
                  onClick={(e) => e.stopPropagation()}
                />
              </Popconfirm>
            }
          >
            <Tag color={statusColors[m.status] ?? "default"}>
              {m.status.toUpperCase()}
            </Tag>
            <Typography.Text strong ellipsis style={{ display: "block" }}>
              {m.url}
            </Typography.Text>
            <Typography.Text type="secondary" style={{ fontSize: 12 }}>
              {m.type.toUpperCase()} · Every {m.interval_minutes}m ·{" "}
              {m.last_checked ?? "never checked"}
            </Typography.Text>
          </Card>
        </Col>
      ))}
    </Row>
  );
}
