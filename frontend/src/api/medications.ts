import { api } from "./client";
import type { Medication, RankedOffer } from "./types";

export async function searchMedications(q?: string): Promise<Medication[]> {
  const r = await api.get<Medication[]>("/medications", { params: { q } });
  return r.data;
}

export async function getMedication(id: number): Promise<Medication> {
  const r = await api.get<Medication>(`/medications/${id}`);
  return r.data;
}

export async function rankForMedication(
  medicationId: number,
  quantity = 1,
): Promise<RankedOffer[]> {
  const r = await api.get<RankedOffer[]>(`/ranking/medication/${medicationId}`, {
    params: { quantity },
  });
  return r.data;
}
