// Hand-typed mirror of the backend's Pydantic schemas. We could generate these
// from OpenAPI, but writing them by hand keeps the surface explicit and gives
// the student something to point at in the defense.

export type UserRole = "PHARMACY" | "DISTRIBUTOR" | "ADMIN";

export interface CurrentUser {
  id: number;
  email: string;
  full_name: string;
  role: UserRole;
  pharmacy_id: number | null;
  distributor_id: number | null;
}

export interface TokenPair {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface Medication {
  id: number;
  name: string;
  active_ingredient: string;
  atc_code: string | null;
  form: string;
  strength: string;
  manufacturer: string;
  description: string;
}

export interface DistributorBrief {
  id: number;
  company_name: string;
  reliability_score: number;
}

export interface RankedOffer {
  offer_id: number;
  distributor: DistributorBrief;
  unit_price: number;
  discount_percent: number;
  final_unit_price: number;
  stock: number;
  price_score: number;
  stock_score: number;
  reliability_score: number;
  total_score: number;
}

export interface Offer {
  id: number;
  distributor_id: number;
  medication_id: number;
  unit_price: number;
  discount_percent: number;
  stock: number;
  final_unit_price: number;
  medication: Medication;
}

export type OrderStatus =
  | "PENDING"
  | "ACCEPTED"
  | "REJECTED"
  | "PREPARING"
  | "SHIPPED"
  | "COMPLETED"
  | "CANCELLED";

export interface OrderItem {
  id: number;
  medication: Medication;
  quantity: number;
  unit_price: number;
  discount_percent: number;
  line_total: number;
}

export interface OrderEvent {
  id: number;
  from_status: string | null;
  to_status: string;
  note: string | null;
  created_at: string;
}

export interface Order {
  id: number;
  pharmacy_id: number;
  distributor_id: number;
  status: OrderStatus;
  total_amount: number;
  notes: string | null;
  created_at: string;
  updated_at: string;
  items: OrderItem[];
  events: OrderEvent[];
}

export interface StockForecast {
  offer_id: number;
  medication_id: number;
  medication_name: string;
  current_stock: number;
  avg_daily_units: number;
  predicted_days_until_stockout: number | null;
  at_risk: boolean;
}

export interface AdminUser {
  id: number;
  email: string;
  full_name: string;
  role: string;
  is_suspended: boolean;
}

export interface ChatMessage {
  id: number;
  role: "user" | "assistant";
  content: string;
  citations: string | null;
  created_at: string;
}

export interface ChatSession {
  id: number;
  title: string;
  created_at: string;
}
