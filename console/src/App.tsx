import { createGlobalStyle } from "antd-style";
import { ConfigProvider } from "antd";
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
      prefixCls="prowlrbot"
      theme={{
        algorithm: antAlgorithm,
        token: antTokenOverrides,
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
