// i18n scaffolding. Only English is wired up right now, but every UI string
// goes through t(...) so adding Arabic (with RTL) is a configuration change
// rather than a code-rewrite later on.
import i18n from "i18next";
import { initReactI18next } from "react-i18next";
import en from "./en.json";

void i18n.use(initReactI18next).init({
  resources: { en: { translation: en } },
  lng: "en",
  fallbackLng: "en",
  interpolation: { escapeValue: false },
});

export default i18n;
