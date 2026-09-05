// Mirrors app/schemas/*.py in the backend. Decimal fields are serialized by
// Pydantic as strings (e.g. "300.00"), so they are typed `string` here and
// parsed at the point of display via the formatters in src/lib/format.ts.

export type RiskLevel = "HIGH_RISK" | "MEDIUM_RISK" | "NORMAL";

export type MenuCategory = "ESTRELLA" | "CABALLO_DE_BATALLA" | "PUZZLE" | "PERRO";

export interface Tenant {
  id: string;
  name: string;
  slug: string;
  subscription_plan: string;
  is_active: boolean;
  created_at: string;
}

export interface TenantCreatePayload {
  name: string;
  slug: string;
  subscription_plan?: string;
  is_active?: boolean;
  parrot_api_key?: string;
}

export interface OrderItemPayload {
  external_product_id: string;
  product_name: string;
  category_name?: string;
  quantity: number;
  unit_price: string;
  unit_cost: string;
}

export interface OrderPayload {
  external_order_id: string;
  branch_external_id?: string;
  branch_name?: string;
  staff_external_id?: string;
  staff_name?: string;
  table_name?: string;
  total_amount: string;
  discount_amount: string;
  discount_reason?: string;
  payment_method?: string;
  status: "COMPLETED" | "CANCELLED";
  order_date: string;
  items: OrderItemPayload[];
}

export interface SyncOrdersPayload {
  orders: OrderPayload[];
}

export interface SyncOrdersResult {
  orders_received: number;
  orders_created: number;
  orders_skipped_duplicate: number;
  audit_events_created: number;
  branches_created: number;
  staff_created: number;
}

export interface CashShiftPayload {
  external_shift_id: string;
  staff_external_id?: string;
  staff_name?: string;
  expected_cash: string;
  actual_cash: string;
  shift_start: string;
  shift_end?: string;
}

export interface SyncCashShiftsPayload {
  shifts: CashShiftPayload[];
}

export interface SyncCashShiftsResult {
  shifts_received: number;
  shifts_created: number;
  shifts_skipped_duplicate: number;
  staff_created: number;
}

export interface DemoDataSeedResult {
  orders: SyncOrdersResult;
  cash_shifts: SyncCashShiftsResult;
}

export interface OrdersFileImportResult extends SyncOrdersResult {
  rows_skipped_invalid: number;
}

export interface CashShiftsFileImportResult extends SyncCashShiftsResult {
  rows_skipped_invalid: number;
}

export interface WaiterAnomaly {
  staff_id: string | null;
  staff_name: string;
  total_cancellations_count: number;
  total_cancelled_amount: string;
  total_discount_amount: string;
  zscore: number;
  risk_level: RiskLevel;
}

export interface FugasAuditReport {
  tenant_id: string;
  total_amount_at_risk: string;
  restaurant_mean_cancelled: number;
  restaurant_std_cancelled: number;
  waiters: WaiterAnomaly[];
}

export interface CashierDiscrepancySummary {
  staff_id: string | null;
  staff_name: string;
  shifts_count: number;
  total_expected_cash: string;
  total_actual_cash: string;
  accumulated_discrepancy: string;
  average_discrepancy: string;
}

export interface CajaAuditReport {
  tenant_id: string;
  total_accumulated_discrepancy: string;
  cashiers: CashierDiscrepancySummary[];
}

export interface MenuItemAnalysis {
  external_product_id: string;
  product_name: string;
  category_name: string | null;
  quantity_sold: number;
  avg_price: string;
  avg_cost: string;
  unit_margin: string;
  total_margin: string;
  popularity_index: number;
  menu_category: MenuCategory;
  recommendation: string;
}

export interface MenuEngineeringReport {
  tenant_id: string;
  avg_margin: number;
  avg_quantity_sold: number;
  items: MenuItemAnalysis[];
}

export interface TopWaiterRisk {
  staff_name: string;
  zscore: number;
  total_cancelled_amount: string;
  risk_level: RiskLevel;
}

export interface TopDogProduct {
  product_name: string;
  quantity_sold: number;
  unit_margin: string;
}

export interface DashboardSummary {
  tenant_id: string;
  total_sales: string;
  total_amount_at_risk: string;
  top_risk_waiters: TopWaiterRisk[];
  top_dog_products: TopDogProduct[];
}

export interface HealthStatus {
  status: string;
  project: string;
  environment: string;
}
