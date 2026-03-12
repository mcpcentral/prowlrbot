import { useEffect, useRef, useState } from "react";
import {
  Button,
  Card,
  Col,
  Empty,
  Row,
  Slider,
  Space,
  Spin,
  Tag,
  Typography,
  Alert,
  Collapse,
} from "antd";
import {
  PlayCircleOutlined,
  PauseCircleOutlined,
  ExportOutlined,
  HistoryOutlined,
} from "@ant-design/icons";
import {
  listReplaySessions,
  getReplayEvents,
} from "../../api/modules/replay";

const { Title, Text, Paragraph } = Typography;

type EventType =
  | "user_message"
  | "agent_response"
  | "tool_call"
  | "tool_result"
  | "thought"
  | "error";

interface ReplayEvent {
  id: string;
  event_type: EventType;
  timestamp_ms: number;
  data: Record<string, any>;
}

interface ReplaySession {
  id: string;
  title?: string;
  agent_id?: string;
  start_time?: string;
  end_time?: string;
  status?: string;
  event_count?: number;
}

function eventColor(type: EventType): string {
  const map: Record<EventType, string> = {
    user_message: "var(--pb-replay-user)",
    agent_response: "var(--pb-replay-agent)",
    tool_call: "var(--pb-replay-tool)",
    tool_result: "var(--pb-replay-result)",
    thought: "var(--pb-replay-thought)",
    error: "var(--pb-replay-error)",
  };
  return map[type] ?? "var(--pb-replay-result)";
}

function EventBubble({ event, offsetMs, highlighted }: { event: ReplayEvent; offsetMs: number; highlighted: boolean }) {
  const content = event.data?.content ?? event.data?.message ?? event.data?.result ?? JSON.stringify(event.data);
  const offsetSec = (offsetMs / 1000).toFixed(1);

  const style: React.CSSProperties = {
    marginBottom: 12,
    transition: "background 0.3s",
    background: highlighted ? "var(--pb-replay-highlight-bg)" : undefined,
    borderRadius: 8,
    padding: "4px 0",
  };

  if (event.event_type === "thought") {
    return (
      <div style={style}>
        <Text type="secondary" style={{ fontSize: 11 }}>+{offsetSec}s</Text>
        <Paragraph italic style={{ color: "var(--pb-replay-thought)", marginBottom: 0 }}>
          💭 {String(content).slice(0, 400)}
        </Paragraph>
      </div>
    );
  }

  if (event.event_type === "error") {
    return (
      <div style={style}>
        <Text type="secondary" style={{ fontSize: 11 }}>+{offsetSec}s</Text>
        <Alert type="error" message={String(content).slice(0, 300)} style={{ marginTop: 4 }} />
      </div>
    );
  }

  if (event.event_type === "tool_call" || event.event_type === "tool_result") {
    const label = event.event_type === "tool_call"
      ? `🔧 ${event.data?.tool_name ?? "tool"}`
      : `↩ Result`;
    return (
      <div style={style}>
        <Text type="secondary" style={{ fontSize: 11 }}>+{offsetSec}s</Text>
        <Collapse
          size="small"
          style={{ marginTop: 4 }}
          items={[{ key: "1", label: <Tag color={eventColor(event.event_type)}>{label}</Tag>, children: <pre style={{ fontSize: 11, maxHeight: 200, overflow: "auto" }}>{String(content).slice(0, 1000)}</pre> }]}
        />
      </div>
    );
  }

  const isUser = event.event_type === "user_message";
  return (
    <div style={{ ...style, display: "flex", flexDirection: "column", alignItems: isUser ? "flex-start" : "flex-end" }}>
      <Text type="secondary" style={{ fontSize: 11 }}>+{offsetSec}s</Text>
      <div style={{
        background: isUser ? "var(--pb-replay-user-bg)" : "var(--pb-replay-agent-bg)",
        border: `1px solid ${eventColor(event.event_type)}33`,
        borderRadius: 12,
        padding: "8px 14px",
        maxWidth: "85%",
        marginTop: 4,
      }}>
        <Text style={{ color: eventColor(event.event_type), fontSize: 11, display: "block", marginBottom: 2 }}>
          {event.event_type.replace("_", " ")}
        </Text>
        <Text>{String(content).slice(0, 500)}</Text>
      </div>
    </div>
  );
}

export default function ReplayPage() {
  const [sessions, setSessions] = useState<ReplaySession[]>([]);
  const [loadingSessions, setLoadingSessions] = useState(true);
  const [selectedSession, setSelectedSession] = useState<ReplaySession | null>(null);
  const [events, setEvents] = useState<ReplayEvent[]>([]);
  const [loadingEvents, setLoadingEvents] = useState(false);
  const [playing, setPlaying] = useState(false);
  const [cursor, setCursor] = useState(0);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    listReplaySessions()
      .then((data: any) => setSessions(Array.isArray(data) ? data : []))
      .catch(() => setSessions([]))
      .finally(() => setLoadingSessions(false));
  }, []);

  const loadSession = async (session: ReplaySession) => {
    setSelectedSession(session);
    setPlaying(false);
    setCursor(0);
    setEvents([]);
    setLoadingEvents(true);
    try {
      const data = await getReplayEvents(session.id);
      setEvents(Array.isArray(data) ? data : []);
    } catch {
      setEvents([]);
    }
    setLoadingEvents(false);
  };

  useEffect(() => {
    if (playing) {
      intervalRef.current = setInterval(() => {
        setCursor((c) => {
          if (c >= events.length - 1) {
            setPlaying(false);
            return c;
          }
          return c + 1;
        });
      }, 1000);
    } else {
      if (intervalRef.current) clearInterval(intervalRef.current);
    }
    return () => { if (intervalRef.current) clearInterval(intervalRef.current); };
  }, [playing, events.length]);

  const handleExport = async () => {
    if (!selectedSession) return;
    const data = await getReplayEvents(selectedSession.id).catch(() => []);
    const blob = new Blob([JSON.stringify({ session: selectedSession, events: data }, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `replay-${selectedSession.id}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div style={{ padding: 24, height: "100%", display: "flex", flexDirection: "column" }}>
      <Title level={3} style={{ marginBottom: 8 }}>
        <HistoryOutlined style={{ marginRight: 8 }} />
        Session Replay
      </Title>
      <Paragraph type="secondary" style={{ marginBottom: 16 }}>
        Replay recorded agent sessions to review decisions and debug behaviour.
      </Paragraph>

      {loadingSessions ? (
        <Spin size="large" style={{ margin: "60px auto", display: "block" }} />
      ) : sessions.length === 0 ? (
        <Empty description="No replay sessions yet. Sessions are recorded automatically when agents run." />
      ) : (
        <Row gutter={16} style={{ flex: 1, overflow: "hidden" }}>
          {/* Session list */}
          <Col span={7} style={{ overflowY: "auto", height: "100%" }}>
            {sessions.map((s) => (
              <Card
                key={s.id}
                size="small"
                hoverable
                style={{
                  marginBottom: 8,
                  borderColor: selectedSession?.id === s.id ? "var(--pb-brand-primary)" : undefined,
                  cursor: "pointer",
                }}
                onClick={() => loadSession(s)}
              >
                <Text strong style={{ display: "block" }}>{s.title || `Session ${s.id.slice(0, 8)}`}</Text>
                <Text type="secondary" style={{ fontSize: 11 }}>
                  {s.agent_id ?? "agent"} · {s.event_count ?? "?"} events
                </Text>
                <br />
                <Tag color={s.status === "recording" ? "processing" : "default"} style={{ marginTop: 4 }}>
                  {s.status ?? "completed"}
                </Tag>
              </Card>
            ))}
          </Col>

          {/* Replay viewer */}
          <Col span={17} style={{ display: "flex", flexDirection: "column", height: "100%", overflow: "hidden" }}>
            {!selectedSession ? (
              <Empty description="Select a session to replay" style={{ marginTop: 60 }} />
            ) : loadingEvents ? (
              <Spin size="large" style={{ margin: "60px auto", display: "block" }} />
            ) : (
              <>
                <Card size="small" style={{ marginBottom: 12, flexShrink: 0 }}>
                  <Space wrap>
                    <Text strong>{selectedSession.title || `Session ${selectedSession.id.slice(0, 8)}`}</Text>
                    <Tag>{selectedSession.agent_id ?? "agent"}</Tag>
                    <Text type="secondary">{events.length} events</Text>
                    <Button
                      size="small"
                      icon={playing ? <PauseCircleOutlined /> : <PlayCircleOutlined />}
                      onClick={() => setPlaying((p) => !p)}
                      disabled={events.length === 0}
                    >
                      {playing ? "Pause" : "Play"}
                    </Button>
                    <Button size="small" icon={<ExportOutlined />} onClick={handleExport}>
                      Export
                    </Button>
                  </Space>
                  {events.length > 0 && (
                    <Slider
                      min={0}
                      max={events.length - 1}
                      value={cursor}
                      onChange={(v) => { setPlaying(false); setCursor(v); }}
                      style={{ marginTop: 8, marginBottom: 0 }}
                    />
                  )}
                </Card>

                {events.length === 0 ? (
                  <Empty description="No events recorded in this session" />
                ) : (
                  <div style={{ flex: 1, overflowY: "auto", padding: "0 4px" }}>
                    {events.slice(0, cursor + 1).map((ev, i) => (
                      <EventBubble
                        key={ev.id ?? i}
                        event={ev}
                        offsetMs={ev.timestamp_ms - (events[0]?.timestamp_ms ?? 0)}
                        highlighted={i === cursor}
                      />
                    ))}
                  </div>
                )}
              </>
            )}
          </Col>
        </Row>
      )}
    </div>
  );
}
