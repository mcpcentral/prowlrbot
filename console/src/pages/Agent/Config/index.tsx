import { useState, useEffect } from "react";
import {
  Form,
  InputNumber,
  Button,
  Card,
  Divider,
  Segmented,
  Typography,
  message,
} from "antd";
import { useTranslation } from "react-i18next";
import api from "../../../api";
import { getPolicy, setPolicy } from "../../../api/modules/autonomy";
import styles from "./index.module.less";
import type { AgentsRunningConfig } from "../../../api/types";

function AgentConfigPage() {
  const { t } = useTranslation();
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [autonomyLevel, setAutonomyLevel] = useState<string>("guide");
  const [savingAutonomy, setSavingAutonomy] = useState(false);

  useEffect(() => {
    fetchConfig();
    getPolicy("default")
      .then((p: any) => { if (p?.level) setAutonomyLevel(p.level); })
      .catch(() => {});
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const fetchConfig = async () => {
    setLoading(true);
    setError(null);
    try {
      const config = await api.getAgentRunningConfig();
      form.setFieldsValue(config);
    } catch (err) {
      const errMsg =
        err instanceof Error ? err.message : t("agentConfig.loadFailed");
      setError(errMsg);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    try {
      const values = await form.validateFields();
      setSaving(true);
      await api.updateAgentRunningConfig(values as AgentsRunningConfig);
      message.success(t("agentConfig.saveSuccess"));
    } catch (err) {
      if (err instanceof Error && "errorFields" in err) {
        return;
      }
      const errMsg =
        err instanceof Error ? err.message : t("agentConfig.saveFailed");
      message.error(errMsg);
    } finally {
      setSaving(false);
    }
  };

  const handleReset = () => {
    fetchConfig();
  };

  const handleSaveAutonomy = async () => {
    setSavingAutonomy(true);
    try {
      await setPolicy("default", { level: autonomyLevel, agent_id: "default" });
      message.success("Autonomy settings saved");
    } catch {
      message.error("Failed to save autonomy settings");
    } finally {
      setSavingAutonomy(false);
    }
  };

  const autonomyDescriptions: Record<string, string> = {
    watch: "Suggests only. Human approves every action.",
    guide: "Acts on routine tasks, asks before novel ones.",
    delegate: "Handles most tasks, escalates edge cases.",
    autonomous: "Full autonomy. Reports results only.",
  };

  return (
    <div className={styles.page}>
      {loading && (
        <div className={styles.centerState}>
          <span className={styles.stateText}>{t("common.loading")}</span>
        </div>
      )}

      {error && !loading && (
        <div className={styles.centerState}>
          <span className={styles.stateTextError}>{error}</span>
          <Button size="small" onClick={fetchConfig} style={{ marginTop: 12 }}>
            {t("environments.retry")}
          </Button>
        </div>
      )}

      <div style={{ display: loading || error ? "none" : "block" }}>
        <div className={styles.header}>
          <div>
            <h1 className={styles.title}>{t("agentConfig.title")}</h1>
            <p className={styles.description}>{t("agentConfig.description")}</p>
          </div>
        </div>

        <Card className={styles.formCard}>
          <Form form={form} layout="vertical" className={styles.form}>
            <Form.Item
              label={t("agentConfig.maxIters")}
              name="max_iters"
              rules={[
                { required: true, message: t("agentConfig.maxItersRequired") },
                {
                  type: "number",
                  min: 1,
                  message: t("agentConfig.maxItersMin"),
                },
              ]}
              tooltip={t("agentConfig.maxItersTooltip")}
            >
              <InputNumber
                style={{ width: "100%" }}
                min={1}
                placeholder={t("agentConfig.maxItersPlaceholder")}
              />
            </Form.Item>

            <Form.Item
              label={t("agentConfig.maxInputLength")}
              name="max_input_length"
              rules={[
                {
                  required: true,
                  message: t("agentConfig.maxInputLengthRequired"),
                },
                {
                  type: "number",
                  min: 1000,
                  message: t("agentConfig.maxInputLengthMin"),
                },
              ]}
              tooltip={t("agentConfig.maxInputLengthTooltip")}
            >
              <InputNumber
                style={{ width: "100%" }}
                min={1000}
                step={1024}
                placeholder={t("agentConfig.maxInputLengthPlaceholder")}
              />
            </Form.Item>

            <Form.Item className={styles.buttonGroup}>
              <Button
                onClick={handleReset}
                disabled={saving}
                style={{ marginRight: 8 }}
              >
                {t("common.reset")}
              </Button>
              <Button type="primary" onClick={handleSave} loading={saving}>
                {t("common.save")}
              </Button>
            </Form.Item>
          </Form>
        </Card>

        <Divider orientation="left">Autonomy</Divider>

        <Card className={styles.formCard}>
          <Typography.Paragraph type="secondary" style={{ marginBottom: 16 }}>
            Control how independently the agent acts. This applies to the default agent.
          </Typography.Paragraph>
          <Segmented
            options={[
              { label: "Watch", value: "watch" },
              { label: "Guide", value: "guide" },
              { label: "Delegate", value: "delegate" },
              { label: "Autonomous", value: "autonomous" },
            ]}
            value={autonomyLevel}
            onChange={(v) => setAutonomyLevel(v as string)}
            style={{ marginBottom: 12 }}
          />
          <Typography.Paragraph type="secondary" style={{ minHeight: 22, marginBottom: 16 }}>
            {autonomyDescriptions[autonomyLevel]}
          </Typography.Paragraph>
          <Button type="primary" onClick={handleSaveAutonomy} loading={savingAutonomy}>
            Save Autonomy Settings
          </Button>
        </Card>
      </div>
    </div>
  );
}

export default AgentConfigPage;
