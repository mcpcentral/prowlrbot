import React, { useEffect, useState } from "react";
import { Alert, Select, Spin, Typography, message } from "antd";
import { ModelGradeCard } from "./ModelGradeCard";

const { Title, Text } = Typography;

interface HardwareProfile {
  ram_gb: number;
  gpu_name: string | null;
  gpu_vram_gb: number | null;
  estimated_bandwidth_gbps: number;
  platform: string;
  is_apple_silicon: boolean;
}

interface ModelGrade {
  model_id: string;
  name: string;
  grade: string;
  label: string;
  score: number;
  best_quant: string | null;
  required_gb: number;
  tok_per_sec: number;
  capability_tags: string[];
  is_moe: boolean;
  cpu_offload_possible: boolean;
  ollama_tag: string | null;
}

const CAPABILITY_OPTIONS = [
  { label: "All capabilities", value: "" },
  { label: "Coding", value: "coding" },
  { label: "Reasoning", value: "reasoning" },
  { label: "General", value: "general" },
  { label: "Fast", value: "fast" },
];

export const HardwareAdvisor: React.FC = () => {
  const [hardware, setHardware] = useState<HardwareProfile | null>(null);
  const [grades, setGrades] = useState<ModelGrade[]>([]);
  const [loading, setLoading] = useState(true);
  const [capability, setCapability] = useState("");
  const [hideF, setHideF] = useState(false);
  const [installing, setInstalling] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([
      fetch("/api/hardware").then((r) => r.json()),
      fetch("/api/hardware/model-grades").then((r) => r.json()),
    ])
      .then(([hw, g]) => {
        setHardware(hw);
        setGrades(g);
      })
      .finally(() => setLoading(false));
  }, []);

  const filtered = grades.filter((m) => {
    if (capability && !m.capability_tags.includes(capability)) return false;
    if (hideF && m.grade === "F") return false;
    return true;
  });

  const handleInstall = async (ollamaTag: string) => {
    setInstalling(ollamaTag);
    try {
      const resp = await fetch("/api/ollama-models/download", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: ollamaTag }),
      });
      if (resp.ok) {
        message.success(`Installing ${ollamaTag}…`);
      } else {
        message.error("Install failed — is Ollama running?");
      }
    } catch {
      message.error("Could not reach Ollama");
    } finally {
      setInstalling(null);
    }
  };

  if (loading) return <Spin style={{ display: "block", margin: "80px auto" }} />;

  const hwParts = hardware
    ? [
        hardware.gpu_name ?? "No GPU detected",
        hardware.gpu_vram_gb ? `${hardware.gpu_vram_gb} GB VRAM` : null,
        `${hardware.ram_gb.toFixed(0)} GB RAM`,
        hardware.estimated_bandwidth_gbps > 0
          ? `~${hardware.estimated_bandwidth_gbps.toFixed(0)} GB/s bandwidth`
          : null,
        hardware.is_apple_silicon ? "Apple Silicon" : hardware.platform,
      ].filter(Boolean)
    : [];

  return (
    <div style={{ maxWidth: 800, margin: "0 auto", padding: 24 }}>
      <Title level={3}>What can my machine run?</Title>

      {hardware && (
        <Alert
          type="info"
          showIcon
          message={<Text strong>Detected hardware</Text>}
          description={hwParts.join(" · ")}
          style={{ marginBottom: 16 }}
        />
      )}

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
            />
          ))
        )}
      </div>
    </div>
  );
};

export default HardwareAdvisor;
