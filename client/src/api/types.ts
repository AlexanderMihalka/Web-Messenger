// Типи дзеркалять Pydantic-схеми бекенду (server/app/schemas/*) — тримайте синхронно при змінах.

export type UserRole = "USER" | "ADMIN";

export interface UserPublic {
  id: number;
  username: string;
  display_name: string;
  avatar_url: string | null;
  bio: string | null;
  is_online: boolean;
  last_seen_at: string | null;
  created_at: string;
}

export interface UserMe extends UserPublic {
  email: string;
  role: UserRole;
  is_blocked: boolean;
}

export type AdminUserOut = UserMe;

export interface MessageOut {
  id: number;
  conversation_id: number;
  sender_id: number | null;
  content: string;
  created_at: string;
  updated_at: string;
  is_edited: boolean;
  is_deleted: boolean;
  is_read: boolean;
}

export interface MessagePage {
  items: MessageOut[];
  has_more: boolean;
}

export interface ReadResult {
  conversation_id: number;
  last_read_message_id: number;
  unread_count: number;
}

export interface ConversationOut {
  id: number;
  partner: UserPublic;
  last_message: MessageOut | null;
  unread_count: number;
  updated_at: string;
  blocked_by_me: boolean;
  can_send: boolean;
}

export interface Page<T> {
  items: T[];
  total: number;
  limit: number;
  offset: number;
}

export interface StatisticsOut {
  total_users: number;
  admins: number;
  blocked_users: number;
  online_users: number;
  new_users_24h: number;
  new_users_7d: number;
  total_conversations: number;
  total_messages: number;
  messages_24h: number;
  websocket_connections: number;
}

export interface LogOut {
  id: number;
  level: string;
  event: string;
  actor_id: number | null;
  ip_address: string | null;
  message: string;
  created_at: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
}

export interface ApiErrorField {
  field: string;
  message: string;
}

export interface ApiErrorBody {
  error: {
    code: string;
    message: string;
    fields?: ApiErrorField[];
  };
}

// --- WebSocket-події (див. server/app/websocket/events.py) ---

export type WsServerEvent =
  | { type: "connection"; user_id: number; server_time: string }
  | { type: "user:online"; user_id: number }
  | { type: "user:offline"; user_id: number; last_seen_at: string }
  | { type: "message:new"; conversation_id: number; message: MessageOut }
  | { type: "message:edit"; conversation_id: number; message: MessageOut }
  | { type: "message:delete"; conversation_id: number; message_id: number }
  | { type: "message:read"; conversation_id: number; user_id: number; last_read_message_id: number }
  | { type: "typing:start"; conversation_id: number; user_id: number }
  | { type: "typing:stop"; conversation_id: number; user_id: number }
  | { type: "pong" }
  | { type: "error"; message: string };

export type WsClientEvent =
  | { type: "ping" }
  | { type: "typing:start"; conversation_id: number }
  | { type: "typing:stop"; conversation_id: number };

// Короткий псевдонім, яким користуються ws/ та hooks/useWebSocketSync.ts.
export type WsEvent = WsServerEvent;
