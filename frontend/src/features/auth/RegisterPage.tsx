import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import toast from "react-hot-toast";
import { useTranslation } from "react-i18next";
import { register } from "@/api/auth";
import { useAuth } from "@/auth/AuthContext";
import type { UserRole } from "@/api/types";

// Single-page registration: pick a role, fill role-specific details inline.
// Keeping it on one page is friendlier than a multi-step wizard at this size.
export default function RegisterPage() {
  const [role, setRole] = useState<UserRole>("PHARMACY");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [orgName, setOrgName] = useState("");
  const [licenseNumber, setLicenseNumber] = useState("");
  const [address, setAddress] = useState("");
  const [phone, setPhone] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const { refresh } = useAuth();
  const nav = useNavigate();
  const { t } = useTranslation();

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      const profile = { name: orgName, license_number: licenseNumber, address, phone };
      const distProfile = { company_name: orgName, license_number: licenseNumber, address, phone };
      await register({
        email,
        password,
        full_name: fullName,
        role,
        pharmacy: role === "PHARMACY" ? profile : undefined,
        distributor: role === "DISTRIBUTOR" ? distProfile : undefined,
      });
      await refresh();
      nav("/");
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
        "Registration failed";
      toast.error(msg);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4 bg-slate-50">
      <form onSubmit={onSubmit} className="card w-full max-w-md space-y-3">
        <h1 className="text-2xl font-bold text-brand-700">{t("auth.register")}</h1>
        <div>
          <label className="label">{t("auth.role")}</label>
          <div className="grid grid-cols-2 gap-2">
            {(["PHARMACY", "DISTRIBUTOR"] as UserRole[]).map((r) => (
              <button
                type="button"
                key={r}
                onClick={() => setRole(r)}
                className={`btn ${
                  role === r ? "bg-brand-600 text-white" : "bg-white ring-1 ring-slate-300"
                }`}
              >
                {r === "PHARMACY" ? t("auth.rolePharmacy") : t("auth.roleDistributor")}
              </button>
            ))}
          </div>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <div>
            <label className="label">{t("auth.fullName")}</label>
            <input className="input" value={fullName} onChange={(e) => setFullName(e.target.value)} required />
          </div>
          <div>
            <label className="label">{t("auth.email")}</label>
            <input
              className="input"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>
          <div className="sm:col-span-2">
            <label className="label">{t("auth.password")}</label>
            <input
              className="input"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              minLength={8}
            />
          </div>
          <div className="sm:col-span-2">
            <label className="label">
              {role === "PHARMACY" ? t("auth.pharmacyName") : t("auth.distributorName")}
            </label>
            <input className="input" value={orgName} onChange={(e) => setOrgName(e.target.value)} required />
          </div>
          <div>
            <label className="label">{t("auth.licenseNumber")}</label>
            <input
              className="input"
              value={licenseNumber}
              onChange={(e) => setLicenseNumber(e.target.value)}
              required
            />
          </div>
          <div>
            <label className="label">{t("auth.phone")}</label>
            <input className="input" value={phone} onChange={(e) => setPhone(e.target.value)} required />
          </div>
          <div className="sm:col-span-2">
            <label className="label">{t("auth.address")}</label>
            <input className="input" value={address} onChange={(e) => setAddress(e.target.value)} required />
          </div>
        </div>
        <button className="btn-primary w-full" disabled={submitting}>
          {submitting ? "…" : t("auth.submit")}
        </button>
        <p className="text-sm text-slate-500 text-center">
          {t("auth.haveAccount")}{" "}
          <Link to="/login" className="text-brand-600 hover:underline">
            {t("auth.login")}
          </Link>
        </p>
      </form>
    </div>
  );
}
