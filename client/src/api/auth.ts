import { api } from "./client";
import type { TokenResponse, UserMe } from "./types";

export interface RegisterPayload {
  username: string;
  email: string;
  password: string;
  confirm_password: string;
  display_name?: string;
}

export const authApi = {
  register: (payload: RegisterPayload) =>
    api.post<TokenResponse>("/auth/register", payload).then((r) => r.data),

  login: (login: string, password: string) =>
    api.post<TokenResponse>("/auth/login", { login, password }).then((r) => r.data),

  refresh: () => api.post<TokenResponse>("/auth/refresh").then((r) => r.data),

  logout: () => api.post<void>("/auth/logout"),

  me: () => api.get<UserMe>("/auth/me").then((r) => r.data),
};
