import { api } from "./client";
import type { StockForecast } from "./types";

export async function myForecast(): Promise<StockForecast[]> {
  return (await api.get<StockForecast[]>("/stock-forecast/mine")).data;
}
