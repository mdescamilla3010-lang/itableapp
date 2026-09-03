import { api } from "./client";
import type {
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
};
