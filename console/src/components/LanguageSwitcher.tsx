import { Dropdown, Button } from "antd";
import { GlobalOutlined } from "@ant-design/icons";
import { useTranslation } from "react-i18next";
import type { MenuProps } from "antd";

export default function LanguageSwitcher() {
  const { i18n } = useTranslation();

  const currentLanguage = i18n.language;

  const changeLanguage = (lang: string) => {
    i18n.changeLanguage(lang);
    localStorage.setItem("language", lang);
  };

  const items: MenuProps["items"] = [
    {
      key: "en",
      label: "English",
      onClick: () => changeLanguage("en"),
    },
  ];

  const currentLabel = "English";

  return (
    <Dropdown
      menu={{ items, selectedKeys: [currentLanguage] }}
      placement="bottomRight"
    >
      <Button icon={<GlobalOutlined />} type="text">
        {currentLabel}
      </Button>
    </Dropdown>
  );
}
