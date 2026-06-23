import { api } from "./client";
import type { Offer } from "./types";

export async function listMyOffers(): Promise<Offer[]> {
  return (await api.get<Offer[]>("/offers/mine")).data;
}

export async function upsertMyOffer(payload: {
  medication_id: number;
  unit_price: number;
  discount_percent: number;
  stock: number;
}): Promise<Offer> {
  return (await api.put<Offer>("/offers/mine", payload)).data;
}

export async function deleteMyOffer(id: number): Promise<void> {
  await api.delete(`/offers/mine/${id}`);
}
