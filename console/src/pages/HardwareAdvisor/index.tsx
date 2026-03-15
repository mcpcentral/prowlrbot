import React, { useCallback, useEffect, useState } from "react";
import { Alert, Select, Spin, Typography, message } from "antd";
import { CheckCircleOutlined, CloseCircleOutlined, CloudDownloadOutlined } from "@ant-design/icons";
import { request } from "../../api/request";
import { api } from "../../api";
import { ModelGradeCard } from "./ModelGradeCard";

const { Title, Text } = Typography;

interface HardwareProfile {
  ram_gb: number;
  cpu_cores?: number;
  cpu_arch?: string;
  gpu_name: string | null;
  gpu_vram_gb: number | null;
  estimated_bandwidth_gbps: number;
  platform: string;
  is_apple_silicon: boolean;
  unified_memory?: boolean;
}

interface ModelGrade {
  model_id: string;
  name: string;
  grade: string;
  label: string;
  score: number;
  best_quant: string | null;
  required_gb: number;
  available_gb?: number;
  tok_per_sec: number;
  capability_tags: string[];
  is_moe: boolean;
  cpu_offload_possible: boolean;
  ollama_tag: string | null;
}

type OllamaStatus = "idle" | "ok" | "unreachable" | "sdk_missing";

const CAPABILITY_OPTIONS = [
  { label: "All capabilities", value: "" },
  { label: "Coding", value: "coding" },
  { label: "Reasoning", value: "reasoning" },
  { label: "General", value: "general" },
  { label: "Fast", value: "fast" },
];

const POLL_INTERVAL_MS = 2000;
const POLL_TIMEOUT_MS = 600_000; // 10 min max

/** Returns true if Ollama model name matches catalog tag (e.g. "llama3.2:3b" matches "llama3.2:3b"). */
function modelNameMatchesTag(installedName: string, tag: string | null): boolean {
  if (!tag) return false;
  return installedName === tag || installedName.startsWith(tag.split(":")[0] + ":");
}

export const HardwareAdvisor: React.FC = () => {
  const [hardware, setHardware] = useState<HardwareProfile | null>(null);
  const [grades, setGrades] = useState<ModelGrade[]>([]);
  const [ollamaStatus, setOllamaStatus] = useState<OllamaStatus>("idle");
  const [installedNames, setInstalledNames] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [capability, setCapability] = useState("");
  const [hideF, setHideF] = useState(false);
  const [installing, setInstalling] = useState<string | null>(null);
  const [downloadProgress, setDownloadProgress] = useState<Record<string, string>>({});

  const fetchHardwareAndGrades = useCallback(async () => {
    try {
      const [hw, g] = await Promise.all([
        request<HardwareProfile>("/hardware"),
        request<ModelGrade[]>("/hardware/model-grades"),
      ]);
      setHardware(hw);
      setGrades(Array.isArray(g) ? g : []);
      setLoadError(null);
    } catch (e) {
      setLoadError(e instanceof Error ? e.message : "Failed to load hardware or models");
    }
  }, []);

  const fetchOllamaStatus = useCallback(async () => {
    try {
      const list = await api.listOllamaModels();
      setInstalledNames(Array.isArray(list) ? list.map((m) => m.name) : []);
      setOllamaStatus("ok");
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : String(e);
      if (msg.includes("503") || msg.includes("connect") || msg.includes("Ollama")) {
        setOllamaStatus("unreachable");
      } else if (msg.includes("501") || msg.includes("SDK")) {
        setOllamaStatus("sdk_missing");
      } else {
        setOllamaStatus("unreachable");
      }
      setInstalledNames([]);
    }
  }, []);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      setLoading(true);
      await fetchHardwareAndGrades();
      await fetchOllamaStatus();
      if (!cancelled) setLoading(false);
    })();
    return () => { cancelled = true; };
  }, [fetchHardwareAndGrades, fetchOllamaStatus]);

  const filtered = grades.filter((m) => {
    if (capability && !m.capability_tags.includes(capability)) return false;
    if (hideF && m.grade === "F") return false;
    return true;
  });

  const handleInstall = useCallback(
    async (ollamaTag: string) => {
      setInstalling(ollamaTag);
      setDownloadProgress((p) => ({ ...p, [ollamaTag]: "Starting…" }));
      try {
        await api.downloadOllamaModel({ name: ollamaTag });
        message.success(`Download started: ${ollamaTag}`);
        const deadline = Date.now() + POLL_TIMEOUT_MS;
        while (Date.now() < deadline) {
          await new Promise((r) => setTimeout(r, POLL_INTERVAL_MS));
          const tasks = await api.getOllamaDownloadStatus();
          const task = tasks.find((t) => t.name === ollamaTag);
          if (task) {
            setDownloadProgress((p) => ({ ...p, [ollamaTag]: task.status }));
            if (task.status === "completed") {
              message.success(`${ollamaTag} installed`);
              setInstalledNames((prev) => (prev.includes(ollamaTag) ? prev : [...prev, ollamaTag]));
              break;
            }
            if (task.status === "failed") {
              message.error(task.error || `Install failed: ${ollamaTag}`);
              break;
            }
          }
        }
      } catch (e: unknown) {
        const msg = e instanceof Error ? e.message : String(e);
        if (msg.includes("503") || msg.includes("connect")) {
          message.error("Ollama is not reachable from the server. Ensure Ollama is running on the same machine as ProwlrBot.");
        } else if (msg.includes("501")) {
          message.error("Ollama SDK not installed on the server. Install with: pip install 'prowlrbot[ollama]'");
        } else {
          message.error(msg || "Install failed");
        }
      } finally {
        setInstalling(null);
        setDownloadProgress((p) => {
          const next = { ...p };
          delete next[ollamaTag];
          return next;
        });
        await fetchOllamaStatus();
      }
    },
    [fetchOllamaStatus]
  );

  const isInstalled = useCallback(
    (model: ModelGrade) => {
      if (!model.ollama_tag) return false;
      return installedNames.some((n) => modelNameMatchesTag(n, model.ollama_tag));
    },
    [installedNames]
  );

  if (loading) {
    return <Spin style={{ display: "block", margin: "80px auto" }} tip="Detecting hardware…" />;
  }

  const hwParts = hardware
    ? [
        hardware.gpu_name ?? "No GPU detected",
        hardware.gpu_vram_gb != null ? `${hardware.gpu_vram_gb} GB VRAM` : null,
        `${Number(hardware.ram_gb).toFixed(0)} GB RAM`,
        hardware.estimated_bandwidth_gbps > 0
          ? `~${hardware.estimated_bandwidth_gbps.toFixed(0)} GB/s bandwidth`
          : null,
        hardware.is_apple_silicon ? "Apple Silicon" : hardware.platform,
      ].filter(Boolean)
    : [];

  const isHostedApp =
    typeof window !== "undefined" && window.location.hostname === "app.prowlrbot.com";

  return (
    <div style={{ maxWidth: 800, margin: "0 auto", padding: 24 }}>
      <Title level={3}>What can my machine run?</Title>

      {isHostedApp && (
        <Alert
          type="warning"
          showIcon
          message="Hosted app: server hardware only"
          description="This page shows the server's hardware, not your computer. For local model recommendations, run ProwlrBot on your own machine (e.g. prowlr app)."
          style={{ marginBottom: 16 }}
        />
      )}

      {loadError && (
        <Alert
          type="error"
          showIcon
          icon={<CloseCircleOutlined />}
          message="Could not load data"
          description={loadError}
          style={{ marginBottom: 16 }}
        />
      )}

      {hardware && !loadError && (
        <Alert
          type="info"
          showIcon
          message={<Text strong>Detected hardware</Text>}
          description={hwParts.join(" · ")}
          style={{ marginBottom: 16 }}
        />
      )}

      {/* Ollama status */}
      <Alert
        type={ollamaStatus === "ok" ? "success" : ollamaStatus === "sdk_missing" ? "warning" : "info"}
        showIcon
        icon={
          ollamaStatus === "ok" ? (
            <CheckCircleOutlined />
          ) : ollamaStatus === "unreachable" ? (
            <CloudDownloadOutlined />
          ) : null
        }
        message={
          ollamaStatus === "ok"
            ? `Ollama running — ${installedNames.length} model(s) installed`
            : ollamaStatus === "unreachable"
              ? "Ollama not reachable from the server"
              : ollamaStatus === "sdk_missing"
                ? "Ollama SDK not installed on server"
                : "Checking Ollama…"
        }
        description={
          ollamaStatus === "ok"
            ? "Install models below; they run on the same machine as ProwlrBot."
            : ollamaStatus === "unreachable"
              ? "Start Ollama where ProwlrBot runs (e.g. ollama serve). If ProwlrBot is in Docker, set OLLAMA_HOST=http://host.docker.internal:11434. Install SDK: pip install 'prowlrbot[ollama]'."
              : ollamaStatus === "sdk_missing"
                ? "Install with: pip install 'prowlrbot[ollama]'"
                : null
        }
        style={{ marginBottom: 16 }}
      />

      <div style={{ display: "flex", gap: 12, marginBottom: 16, flexWrap: "wrap" }}>
        <Select
          options={CAPABILITY_OPTIONS}
          value={capability}
          onChange={setCapability}
          style={{ width: 200 }}
        />
        <Select
          value={hideF ? "runnable" : "all"}
          onChange={(v) => setHideF(v === "runnable")}
          options={[
            { label: "All models", value: "all" },
            { label: "Runnable only", value: "runnable" },
          ]}
          style={{ width: 160 }}
        />
      </div>

      <div style={{ border: "1px solid #f0f0f0", borderRadius: 8, overflow: "hidden" }}>
        {filtered.length === 0 ? (
          <div style={{ padding: 40, textAlign: "center", color: "#8c8c8c" }}>
            No models match the current filter.
          </div>
        ) : (
          filtered.map((model) => (
            <ModelGradeCard
              key={model.model_id}
              model={model}
              onInstall={handleInstall}
              installing={installing === model.ollama_tag}
              installed={isInstalled(model)}
              downloadStatus={downloadProgress[model.ollama_tag ?? ""]}
            />
          ))
        )}
      </div>
    </div>
  );
};

export default HardwareAdvisor;
