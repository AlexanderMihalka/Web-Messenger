// Axios-інстанс: access-токен живе лише в пам'яті (не в localStorage — захист від XSS),
// refresh-токен — в httpOnly cookie, яку браузер сам додає завдяки withCredentials.
import axios, { AxiosError, type InternalAxiosRequestConfig } from "axios";

import type { TokenResponse } from "./types";

let accessToken: string | null = null;
let onUnauthorized: (() => void) | null = null;

export function setAccessToken(token: string | null): void {
  accessToken = token;
}

export function getAccessToken(): string | null {
  return accessToken;
}

export function registerUnauthorizedHandler(handler: () => void): void {
  onUnauthorized = handler;
}

export const api = axios.create({
  baseURL: "/api/v1",
  withCredentials: true,
});

api.interceptors.request.use((config) => {
  if (accessToken) {
    config.headers.set("Authorization", `Bearer ${accessToken}`);
  }
  return config;
});

let refreshPromise: Promise<string> | null = null;

/** Експортується окремо: ws/WebSocketContext.tsx викликає це саме, коли перепідключення
 * отримує код закриття 4401 (токен, яким з'єднались, більше не дійсний). */
export async function refreshAccessToken(): Promise<string> {
  refreshPromise ??= axios
    .post<TokenResponse>("/api/v1/auth/refresh", null, { withCredentials: true })
    .then((response) => {
      accessToken = response.data.access_token;
      return accessToken;
    })
    .finally(() => {
      refreshPromise = null;
    });
  return refreshPromise;
}

interface RetryableConfig extends InternalAxiosRequestConfig {
  _retried?: boolean;
}

const AUTH_ENDPOINTS = ["/auth/login", "/auth/register", "/auth/refresh"];

api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const config = error.config as RetryableConfig | undefined;
    const status = error.response?.status;
    const isAuthEndpoint = AUTH_ENDPOINTS.some((path) => config?.url?.includes(path));

    if (status === 401 && config && !config._retried && !isAuthEndpoint) {
      config._retried = true;
      try {
        const newToken = await refreshAccessToken();
        config.headers.set("Authorization", `Bearer ${newToken}`);
        return api(config);
      } catch (refreshError) {
        accessToken = null;
        onUnauthorized?.();
        return Promise.reject(refreshError);
      }
    }
    return Promise.reject(error);
  },
);

export interface ApiError {
  status: number;
  code: string;
  message: string;
  fields?: { field: string; message: string }[];
}

export function toApiError(error: unknown): ApiError {
  if (axios.isAxiosError(error)) {
    const data = error.response?.data as
      | { error?: { code: string; message: string; fields?: ApiError["fields"] } }
      | undefined;
    if (data?.error) {
      return {
        status: error.response?.status ?? 0,
        code: data.error.code,
        message: data.error.message,
        fields: data.error.fields,
      };
    }
    return { status: error.response?.status ?? 0, code: "network_error", message: error.message };
  }
  return { status: 0, code: "unknown_error", message: "Щось пішло не так" };
}
