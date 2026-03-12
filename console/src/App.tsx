import { createGlobalStyle } from "antd-style";
import { ConfigProvider, bailianTheme } from "@agentscope-ai/design";
import { BrowserRouter } from "react-router-dom";
import { ThemeProvider, useTheme } from "./contexts/ThemeContext";
import MainLayout from "./layouts/MainLayout";
import "./styles/theme.css";
import "./styles/layout.css";
import "./styles/form-override.css";

const GlobalStyle = createGlobalStyle`
* {
  margin: 0;
  box-sizing: border-box;
}
`;

function ThemedApp() {
  const { antAlgorithm, antTokenOverrides } = useTheme();

  return (
    <ConfigProvider
      {...bailianTheme}
      prefix="prowlrbot"
      prefixCls="prowlrbot"
      theme={{
        ...bailianTheme.theme,
        algorithm: antAlgorithm,
        token: {
          ...bailianTheme.theme?.token,
          ...antTokenOverrides,
        },
      }}
    >
      <MainLayout />
    </ConfigProvider>
  );
}

function App() {
  return (
    <BrowserRouter>
      <GlobalStyle />
      <ThemeProvider>
        <ThemedApp />
      </ThemeProvider>
    </BrowserRouter>
  );
}

export default App;
