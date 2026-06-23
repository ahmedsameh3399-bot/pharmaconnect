import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import toast from "react-hot-toast";
import { useTranslation } from "react-i18next";
import { login } from "@/api/auth";
import { useAuth } from "@/auth/AuthContext";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const { refresh } = useAuth();
  const nav = useNavigate();
  const { t } = useTranslation();

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      await login(email, password);
      await refresh();
      nav("/");
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
        "Login failed";
      toast.error(msg);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4 bg-slate-50">
      <form onSubmit={onSubmit} className="card w-full max-w-sm space-y-4">
        <div>
          <h1 className="text-2xl font-bold text-brand-700">{t("app.name")}</h1>
          <p className="text-sm text-slate-500">{t("app.tagline")}</p>
        </div>
        <div>
          <label className="label">{t("auth.email")}</label>
          <input
            className="input"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            autoComplete="email"
          />
        </div>
        <div>
          <label className="label">{t("auth.password")}</label>
          <input
            className="input"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            autoComplete="current-password"
          />
        </div>
        <button className="btn-primary w-full" disabled={submitting}>
          {submitting ? "…" : t("auth.login")}
        </button>
        <p className="text-sm text-slate-500 text-center">
          {t("auth.noAccount")}{" "}
          <Link to="/register" className="text-brand-600 hover:underline">
            {t("auth.register")}
          </Link>
        </p>
      </form>
    </div>
  );
}
