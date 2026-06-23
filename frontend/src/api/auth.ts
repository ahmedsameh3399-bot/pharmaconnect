import { api, tokenStore } from "./client";
import type { CurrentUser, TokenPair, UserRole } from "./types";

export interface PharmacyDetails {
  name: string;
  license_number: string;
  address: string;
  phone: string;
}

export interface DistributorDetails {
  company_name: string;
  license_number: string;
  address: string;
  phone: string;
}

export interface RegisterPayload {
  email: string;
  password: string;
  full_name: string;
  role: UserRole;
  pharmacy?: PharmacyDetails;
  distributor?: DistributorDetails;
}

export async function login(email: string, password: string): Promise<TokenPair> {
  // FastAPI's OAuth2PasswordRequestForm expects form-encoded fields.
  const form = new URLSearchParams();
  form.set("username", email);
  form.set("password", password);
  const r = await api.post<TokenPair>("/auth/login", form, {
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
  });
  tokenStore.set(r.data.access_token, r.data.refresh_token);
  return r.data;
}

export async function register(payload: RegisterPayload): Promise<TokenPair> {
  const r = await api.post<TokenPair>("/auth/register", payload);
  tokenStore.set(r.data.access_token, r.data.refresh_token);
  return r.data;
}

export async function fetchMe(): Promise<CurrentUser> {
  const r = await api.get<CurrentUser>("/auth/me");
  return r.data;
}

export function logout() {
  tokenStore.clear();
}
