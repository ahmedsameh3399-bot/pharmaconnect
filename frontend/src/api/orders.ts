import { api } from "./client";
import type { Order, OrderStatus } from "./types";

export interface PlaceOrderPayload {
  distributor_id: number;
  items: { medication_id: number; quantity: number }[];
  notes?: string;
}

export async function placeOrder(payload: PlaceOrderPayload): Promise<Order> {
  return (await api.post<Order>("/orders", payload)).data;
}

export async function listMyOrders(): Promise<Order[]> {
  return (await api.get<Order[]>("/orders/mine")).data;
}

export async function getOrder(id: number): Promise<Order> {
  return (await api.get<Order>(`/orders/${id}`)).data;
}

export async function changeOrderStatus(
  id: number,
  newStatus: OrderStatus,
  note?: string,
): Promise<Order> {
  return (await api.post<Order>(`/orders/${id}/status`, { new_status: newStatus, note })).data;
}
