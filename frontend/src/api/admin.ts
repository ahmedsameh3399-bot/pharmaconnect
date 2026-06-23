import { api } from "./client";
import type { AdminUser } from "./types";

export async function listUsers(): Promise<AdminUser[]> {
  return (await api.get<AdminUser[]>("/admin/users")).data;
}

export async function setSuspension(userId: number, suspended: boolean): Promise<AdminUser> {
  return (await api.post<AdminUser>(`/admin/users/${userId}/suspension`, { suspended })).data;
}

export async function metrics(): Promise<Record<string, number>> {
  return (await api.get<Record<string, number>>("/admin/metrics")).data;
}
