import { api } from "./client";
import type {
  CashShiftsFileImportResult,
  DemoDataSeedResult,
  OrdersFileImportResult,
  SyncCashShiftsPayload,
  SyncCashShiftsResult,
  SyncOrdersPayload,
  SyncOrdersResult,
} from "./types";

export const syncApi = {
  orders: (tenantId: string, payload: SyncOrdersPayload) =>
    api.post<SyncOrdersResult>(`/sync/${tenantId}`, payload),
  cashShifts: (tenantId: string, payload: SyncCashShiftsPayload) =>
    api.post<SyncCashShiftsResult>(`/sync/${tenantId}/cash-shifts`, payload),
  seedDemoData: (tenantId: string) =>
    api.post<DemoDataSeedResult>(`/sync/${tenantId}/demo-data`, {}),
  uploadOrdersFile: (tenantId: string, file: File) =>
    api.postFile<OrdersFileImportResult>(`/sync/${tenantId}/upload/orders`, file),
  uploadCashShiftsFile: (tenantId: string, file: File) =>
    api.postFile<CashShiftsFileImportResult>(`/sync/${tenantId}/upload/cash-shifts`, file),
};
