import { api } from "./client";
import type { AdminUserOut, LogOut, Page, StatisticsOut } from "./types";

export const adminApi = {
  listUsers: (params: { q?: string; limit?: number; offset?: number } = {}) =>
    api.get<Page<AdminUserOut>>("/admin/users", { params }).then((r) => r.data),

  setBlocked: (userId: number, blocked: boolean) =>
    api.patch<AdminUserOut>(`/admin/users/${userId}/block`, { blocked }).then((r) => r.data),

  deleteUser: (userId: number) => api.delete<void>(`/admin/users/${userId}`),

  statistics: () => api.get<StatisticsOut>("/admin/statistics").then((r) => r.data),

  logs: (params: { level?: string; event?: string; limit?: number; offset?: number } = {}) =>
    api.get<Page<LogOut>>("/admin/logs", { params }).then((r) => r.data),
};
