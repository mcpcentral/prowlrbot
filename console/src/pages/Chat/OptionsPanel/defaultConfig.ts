const defaultConfig = {
  theme: {
    colorPrimary: "#615CED",
    darkMode: false,
    prefix: "prowlrbot",
    leftHeader: {
      logo: "",
      title: "ProwlrBot",
    },
  },
  sender: {
    attachments: false,
    maxLength: 10000,
    disclaimer: "Always watching. Always ready.",
  },
  welcome: {
    greeting: "Hey there! What can I help you with?",
    description:
      "Your autonomous AI agent — monitoring, automation, and multi-channel communication.",
    avatar: `${import.meta.env.BASE_URL}prowlrbot-symbol.svg`,
    prompts: [
      {
        label: "Get Started",
        value: "What can you help me with?",
      },
      {
        label: "My Skills",
        value: "What skills and tools do you have available?",
      },
      {
        label: "Run a Task",
        value: "Help me set up a monitoring task",
      },
      {
        label: "Check Status",
        value: "Show me the current system status",
      },
    ],
  },
  api: {
    baseURL: "",
    token: "",
  },
};

export default defaultConfig;

export type DefaultConfig = typeof defaultConfig;
