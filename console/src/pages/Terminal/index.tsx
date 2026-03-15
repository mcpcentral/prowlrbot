import { useEffect, useRef, useState } from "react";
import { Button, Space, Tag, Typography } from "antd";
import { PoweroffOutlined, ReloadOutlined } from "@ant-design/icons";
import { Terminal as XTerm } from "@xterm/xterm";
import { FitAddon } from "@xterm/addon-fit";
import "@xterm/xterm/css/xterm.css";

declare const BASE_URL: string;

function getWsBase(): string {
  const base = (typeof BASE_URL !== "undefined" ? BASE_URL : "") || window.location.origin;
  return base.replace(/^http/, "ws");
}

function makeSessionId(): string {
  return Math.random().toString(36).slice(2) + Date.now().toString(36);
}

export default function TerminalPage() {
  const containerRef = useRef<HTMLDivElement>(null);
  const termRef = useRef<XTerm | null>(null);
  const fitRef = useRef<FitAddon | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const sessionIdRef = useRef<string>(makeSessionId());
  const [connected, setConnected] = useState(false);

  const connect = () => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.close();
    }
    const ws = new WebSocket(`${getWsBase()}/ws/terminal/${sessionIdRef.current}`);
    ws.binaryType = "arraybuffer";
    ws.onopen = () => setConnected(true);
    ws.onclose = () => setConnected(false);
    ws.onerror = () => setConnected(false);
    ws.onmessage = (e) => {
      if (!termRef.current) return;
      if (e.data instanceof ArrayBuffer) {
        termRef.current.write(new Uint8Array(e.data));
      } else {
        termRef.current.write(e.data as string);
      }
    };
    wsRef.current = ws;
  };

  const disconnect = () => {
    wsRef.current?.close();
    sessionIdRef.current = makeSessionId();
    setConnected(false);
  };

  const reconnect = () => {
    disconnect();
    termRef.current?.clear();
    setTimeout(connect, 150);
  };

  useEffect(() => {
    if (!containerRef.current) return;

    const term = new XTerm({
      cursorBlink: true,
      fontSize: 14,
      fontFamily: '"Cascadia Code", "Fira Code", monospace',
      theme: { background: "#0d1117", foreground: "#e6edf3", cursor: "#58a6ff" },
    });
    const fit = new FitAddon();
    term.loadAddon(fit);
    term.open(containerRef.current);
    fit.fit();

    term.onData((data) => {
      wsRef.current?.send(data);
    });
    term.onResize(({ rows, cols }) => {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({ type: "resize", rows, cols }));
      }
    });

    termRef.current = term;
    fitRef.current = fit;
    connect();

    const ro = new ResizeObserver(() => fitRef.current?.fit());
    ro.observe(containerRef.current);

    return () => {
      ro.disconnect();
      term.dispose();
      wsRef.current?.close();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100%", padding: 16 }}>
      <Space style={{ marginBottom: 10, flexShrink: 0 }}>
        <Typography.Title level={4} style={{ margin: 0 }}>Terminal</Typography.Title>
        <Tag color={connected ? "green" : "red"}>{connected ? "Connected" : "Disconnected"}</Tag>
        <Button size="small" icon={<ReloadOutlined />} onClick={reconnect}>
          Reconnect
        </Button>
        <Button size="small" danger icon={<PoweroffOutlined />} onClick={disconnect}>
          Disconnect
        </Button>
      </Space>
      <div
        ref={containerRef}
        style={{ flex: 1, background: "#0d1117", borderRadius: 8, overflow: "hidden", minHeight: 0 }}
      />
    </div>
  );
}
