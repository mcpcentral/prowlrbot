import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Button, Card, Divider, Form, Input, message, Tabs, Typography } from "antd";
import {
  GithubOutlined,
  GoogleOutlined,
  LockOutlined,
  MailOutlined,
  UserOutlined,
} from "@ant-design/icons";
import { useAuth } from "../../contexts/AuthContext";
import {
  login,
  register,
  fetchOAuthProviders,
  getOAuthStartUrl,
} from "../../api/modules/auth";
import "./style.css";

const { Title, Text } = Typography;

export default function LoginPage() {
  const { onLogin } = useAuth();
  const navigate = useNavigate();
  const [tab, setTab] = useState<"login" | "register">("login");
  const [loading, setLoading] = useState(false);
  const [oauthProviders, setOauthProviders] = useState<string[]>([]);

  useEffect(() => {
    fetchOAuthProviders()
      .then(setOauthProviders)
      .catch(() => {});
  }, []);

  const handleLogin = async (values: { username: string; password: string }) => {
    setLoading(true);
    try {
      const resp = await login(values.username, values.password);
      onLogin(resp.access_token);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Login failed";
      message.error(msg);
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = async (values: {
    username: string;
    password: string;
    email?: string;
  }) => {
    setLoading(true);
    try {
      const resp = await register(values.username, values.password, values.email);
      onLogin(resp.access_token);
      navigate("/credits", { replace: true });
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Registration failed";
      message.error(msg);
    } finally {
      setLoading(false);
    }
  };

  const providerIcon: Record<string, React.ReactNode> = {
    github: <GithubOutlined />,
    google: <GoogleOutlined />,
  };

  return (
    <div className="login-page">
      <Card className="login-card" bordered={false}>
        <div className="login-header">
          <Title level={3} style={{ margin: 0 }}>
            ProwlrBot
          </Title>
          <Text type="secondary">Always watching. Always ready.</Text>
        </div>

        <Tabs
          activeKey={tab}
          onChange={(k) => setTab(k as "login" | "register")}
          centered
          items={[
            {
              key: "login",
              label: "Sign In",
              children: (
                <Form layout="vertical" onFinish={handleLogin} autoComplete="on">
                  <Form.Item
                    name="username"
                    rules={[{ required: true, message: "Enter your username" }]}
                  >
                    <Input prefix={<UserOutlined />} placeholder="Username" size="large" />
                  </Form.Item>
                  <Form.Item
                    name="password"
                    rules={[{ required: true, message: "Enter your password" }]}
                  >
                    <Input.Password
                      prefix={<LockOutlined />}
                      placeholder="Password"
                      size="large"
                    />
                  </Form.Item>
                  <Form.Item>
                    <Button
                      type="primary"
                      htmlType="submit"
                      block
                      size="large"
                      loading={loading}
                    >
                      Sign In
                    </Button>
                  </Form.Item>
                </Form>
              ),
            },
            {
              key: "register",
              label: "Register",
              children: (
                <Form layout="vertical" onFinish={handleRegister} autoComplete="on">
                  <Form.Item
                    name="username"
                    rules={[{ required: true, message: "Choose a username" }]}
                  >
                    <Input prefix={<UserOutlined />} placeholder="Username" size="large" />
                  </Form.Item>
                  <Form.Item name="email">
                    <Input prefix={<MailOutlined />} placeholder="Email (optional)" size="large" />
                  </Form.Item>
                  <Form.Item
                    name="password"
                    rules={[
                      { required: true, message: "Choose a password" },
                      { min: 12, message: "Must be at least 12 characters" },
                    ]}
                  >
                    <Input.Password
                      prefix={<LockOutlined />}
                      placeholder="Password (min 12 chars)"
                      size="large"
                    />
                  </Form.Item>
                  <Form.Item>
                    <Button
                      type="primary"
                      htmlType="submit"
                      block
                      size="large"
                      loading={loading}
                    >
                      Create Account
                    </Button>
                  </Form.Item>
                </Form>
              ),
            },
          ]}
        />

        {oauthProviders.length > 0 && (
          <>
            <Divider plain>or continue with</Divider>
            <div className="oauth-buttons">
              {oauthProviders.map((provider) => (
                <Button
                  key={provider}
                  icon={providerIcon[provider]}
                  size="large"
                  block
                  href={getOAuthStartUrl(provider)}
                  style={{ marginBottom: 8, textTransform: "capitalize" }}
                >
                  {provider}
                </Button>
              ))}
            </div>
          </>
        )}
      </Card>
    </div>
  );
}
