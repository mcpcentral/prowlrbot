import { useState, useEffect, useCallback } from "react";
import {
  Switch,
  Button,
  Slider,
  Modal,
  message,
  Alert,
} from "antd";
import {
  ExportOutlined,
  DeleteOutlined,
  ExclamationCircleOutlined,
} from "@ant-design/icons";
import { request } from "../../../api";
import styles from "./index.module.less";

/* ------------------------------------------------------------------ */
/* Types                                                               */
/* ------------------------------------------------------------------ */

interface PrivacySettings {
  chat_logging: boolean;
  session_recording: boolean;
  log_tool_calls: boolean;
  log_model_requests: boolean;
  anonymize_exports: boolean;
  gdpr_mode: boolean;
  data_retention_days: number;
}

const defaultSettings: PrivacySettings = {
  chat_logging: true,
  session_recording: true,
  log_tool_calls: true,
  log_model_requests: false,
  anonymize_exports: false,
  gdpr_mode: false,
  data_retention_days: 90,
};

/* ------------------------------------------------------------------ */
/* Toggle Definitions                                                  */
/* ------------------------------------------------------------------ */

const toggleDefs: {
  key: keyof PrivacySettings;
  label: string;
  description: string;
}[] = [
  {
    key: "chat_logging",
    label: "Chat Logging",
    description: "Store chat messages for session history and debugging",
  },
  {
    key: "session_recording",
    label: "Session Recording",
    description:
      "Record full session transcripts including tool calls and responses",
  },
  {
    key: "log_tool_calls",
    label: "Log Tool Calls",
    description:
      "Log tool invocations (shell commands, file operations, browser actions)",
  },
  {
    key: "log_model_requests",
    label: "Log Model Requests",
    description:
      "Log full request/response payloads sent to LLM providers (may contain sensitive data)",
  },
  {
    key: "anonymize_exports",
    label: "Anonymize Exports",
    description:
      "Strip personally identifiable information from exported data",
  },
  {
    key: "gdpr_mode",
    label: "GDPR Mode",
    description:
      "Enable GDPR-compliant data handling: automatic anonymization, retention enforcement, and right-to-deletion support",
  },
];

/* ------------------------------------------------------------------ */
/* Main Page                                                           */
/* ------------------------------------------------------------------ */

function PrivacyPage() {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [settings, setSettings] = useState<PrivacySettings>(defaultSettings);
  const [dirty, setDirty] = useState(false);

  const fetchSettings = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await request<PrivacySettings>("/privacy/settings").catch(
        () => null,
      );
      if (data && typeof data === "object") {
        setSettings({ ...defaultSettings, ...data });
      }
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to load privacy settings",
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchSettings();
  }, [fetchSettings]);

  /* ---- Toggle handler ---- */

  const handleToggle = (key: keyof PrivacySettings, checked: boolean) => {
    setSettings((prev) => ({ ...prev, [key]: checked }));
    setDirty(true);
  };

  /* ---- Retention handler ---- */

  const handleRetentionChange = (value: number) => {
    setSettings((prev) => ({ ...prev, data_retention_days: value }));
    setDirty(true);
  };

  /* ---- Save ---- */

  const handleSave = async () => {
    setSaving(true);
    try {
      await request("/privacy/settings", {
        method: "PUT",
        body: JSON.stringify(settings),
      });
      message.success("Privacy settings saved");
      setDirty(false);
    } catch (err) {
      const msg =
        err instanceof Error ? err.message : "Failed to save settings";
      message.error(msg);
    } finally {
      setSaving(false);
    }
  };

  /* ---- Export Data ---- */

  const handleExportData = async () => {
    try {
      message.loading({ content: "Preparing export...", key: "export" });
      const blob = await fetch("/api/privacy/export", {
        method: "POST",
      }).then((r) => r.blob());
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `prowlrbot-data-export-${new Date().toISOString().slice(0, 10)}.json`;
      a.click();
      URL.revokeObjectURL(url);
      message.success({ content: "Data exported successfully", key: "export" });
    } catch {
      message.error({
        content: "Export failed — the endpoint may not be available yet",
        key: "export",
      });
    }
  };

  /* ---- Delete Data ---- */

  const handleDeleteData = () => {
    Modal.confirm({
      title: "Delete All Data",
      icon: <ExclamationCircleOutlined />,
      content:
        "This will permanently delete all your chat history, session recordings, and stored data. This action cannot be undone.",
      okText: "Delete Everything",
      okButtonProps: { danger: true },
      cancelText: "Cancel",
      onOk: async () => {
        try {
          await request("/privacy/delete-all-data", { method: "POST" });
          message.success("All data has been deleted");
        } catch {
          message.error(
            "Delete failed — the endpoint may not be available yet",
          );
        }
      },
    });
  };

  /* ---- render ---- */

  return (
    <div className={styles.page}>
      {/* ---- Page header ---- */}
      <div className={styles.section}>
        <h2 className={styles.sectionTitle}>Privacy</h2>
        <p className={styles.sectionDesc}>
          Control how ProwlrBot collects, stores, and handles your data.
        </p>
      </div>

      {loading ? (
        <div className={styles.centerState}>
          <span className={styles.stateText}>Loading privacy settings...</span>
        </div>
      ) : error ? (
        <div className={styles.centerState}>
          <span className={styles.stateTextError}>{error}</span>
          <Button
            size="small"
            onClick={fetchSettings}
            style={{ marginTop: 12 }}
          >
            Retry
          </Button>
        </div>
      ) : (
        <>
          {/* ---- Privacy Toggles ---- */}
          <div className={styles.cardSection}>
            <div className={styles.cardSectionTitle}>Privacy Settings</div>
            {toggleDefs.map((def) => (
              <div className={styles.toggleRow} key={def.key}>
                <div className={styles.toggleInfo}>
                  <span className={styles.toggleLabel}>{def.label}</span>
                  <span className={styles.toggleDesc}>{def.description}</span>
                </div>
                <Switch
                  checked={settings[def.key] as boolean}
                  onChange={(checked) => handleToggle(def.key, checked)}
                />
              </div>
            ))}
          </div>

          {/* ---- Data Retention ---- */}
          <div className={styles.cardSection}>
            <div className={styles.cardSectionTitle}>Data Retention</div>
            <p style={{ color: "#666", fontSize: 13, marginBottom: 16 }}>
              Set how long ProwlrBot retains chat logs, session recordings, and
              audit data. Older data is automatically purged.
            </p>
            <div className={styles.retentionRow}>
              <div className={styles.retentionSlider}>
                <Slider
                  min={1}
                  max={365}
                  value={settings.data_retention_days}
                  onChange={handleRetentionChange}
                  marks={{
                    1: "1d",
                    30: "30d",
                    90: "90d",
                    180: "180d",
                    365: "1y",
                  }}
                />
              </div>
              <span className={styles.retentionValue}>
                {settings.data_retention_days} days
              </span>
            </div>
          </div>

          {/* ---- Save Button ---- */}
          {dirty && (
            <div style={{ marginBottom: 24 }}>
              <Alert
                type="info"
                showIcon
                message="You have unsaved changes"
                action={
                  <Button
                    type="primary"
                    size="small"
                    loading={saving}
                    onClick={handleSave}
                  >
                    Save Changes
                  </Button>
                }
              />
            </div>
          )}

          {/* ---- Data Export & Deletion ---- */}
          <div className={styles.cardSection}>
            <div className={styles.cardSectionTitle}>Data Management</div>
            <p style={{ color: "#666", fontSize: 13, marginBottom: 16 }}>
              Export or delete your data. Exported data includes chat history,
              session recordings, configuration, and audit logs.
            </p>
            <div className={styles.dataActions}>
              <Button icon={<ExportOutlined />} onClick={handleExportData}>
                Export All Data
              </Button>
            </div>
            <div className={styles.dangerZone}>
              <Alert
                type="error"
                showIcon
                message="Danger Zone"
                description="Permanently delete all your data. This action cannot be undone."
                action={
                  <Button
                    danger
                    icon={<DeleteOutlined />}
                    onClick={handleDeleteData}
                  >
                    Delete My Data
                  </Button>
                }
              />
            </div>
          </div>
        </>
      )}
    </div>
  );
}

export default PrivacyPage;
