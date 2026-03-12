const defaultConfig = {
  theme: {
    colorPrimary: "#615CED",
    darkMode: false,
    prefix: "prowlrbot",
    leftHeader: {
      logo: "",
      title: "Work with ProwlrBot",
    },
  },
  sender: {
    attachments: false,
    maxLength: 10000,
    disclaimer: "Works for you, grows with you",
  },
  welcome: {
    greeting: "Hello, how can I help you today?",
    description:
      "I am a helpful assistant that can help you with your questions.",
    avatar: `${import.meta.env.BASE_URL}prowlrbot-symbol.svg`,
    prompts: [
      {
        value: "Let's get started — what can you help me with?",
      },
      {
        value: "What skills do you have?",
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
