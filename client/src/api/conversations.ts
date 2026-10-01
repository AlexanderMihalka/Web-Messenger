import { api } from "./client";
import type { ConversationOut } from "./types";

export const conversationsApi = {
  list: () => api.get<ConversationOut[]>("/conversations").then((r) => r.data),

  create: (userId: number) =>
    api.post<ConversationOut>("/conversations", { user_id: userId }).then((r) => r.data),

  get: (conversationId: number) =>
    api.get<ConversationOut>(`/conversations/${conversationId}`).then((r) => r.data),

  remove: (conversationId: number) => api.delete<void>(`/conversations/${conversationId}`),
};
