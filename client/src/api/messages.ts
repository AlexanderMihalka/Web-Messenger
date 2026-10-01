import { api } from "./client";
import type { MessageOut, MessagePage, ReadResult } from "./types";

export const messagesApi = {
  list: (conversationId: number, params: { after_id?: number; before_id?: number; limit?: number } = {}) =>
    api
      .get<MessagePage>(`/conversations/${conversationId}/messages`, { params })
      .then((r) => r.data),

  send: (conversationId: number, content: string) =>
    api
      .post<MessageOut>(`/conversations/${conversationId}/messages`, { content })
      .then((r) => r.data),

  edit: (messageId: number, content: string) =>
    api.patch<MessageOut>(`/messages/${messageId}`, { content }).then((r) => r.data),

  remove: (messageId: number) => api.delete<MessageOut>(`/messages/${messageId}`).then((r) => r.data),

  markRead: (messageId: number) =>
    api.post<ReadResult>(`/messages/${messageId}/read`).then((r) => r.data),
};
