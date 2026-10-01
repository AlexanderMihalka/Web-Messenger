import { api } from "./client";
import type { Page, UserMe, UserPublic } from "./types";

export interface UpdateMePayload {
  display_name?: string;
  username?: string;
  bio?: string | null;
}

export const usersApi = {
  list: (limit = 30, offset = 0) =>
    api.get<Page<UserPublic>>("/users", { params: { limit, offset } }).then((r) => r.data),

  search: (q: string) => api.get<UserPublic[]>("/users/search", { params: { q } }).then((r) => r.data),

  get: (userId: number) => api.get<UserPublic>(`/users/${userId}`).then((r) => r.data),

  updateMe: (payload: UpdateMePayload) => api.patch<UserMe>("/users/me", payload).then((r) => r.data),

  uploadAvatar: (file: File) => {
    const form = new FormData();
    form.append("file", file);
    return api.post<UserMe>("/users/me/avatar", form).then((r) => r.data);
  },

  listBlocked: () => api.get<UserPublic[]>("/users/me/blocked").then((r) => r.data),

  block: (userId: number) => api.post<UserPublic>(`/users/${userId}/block`).then((r) => r.data),

  unblock: (userId: number) => api.delete<UserPublic>(`/users/${userId}/block`).then((r) => r.data),
};
