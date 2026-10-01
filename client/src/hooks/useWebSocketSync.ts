import { useCallback } from 'react'
import { useQueryClient, type InfiniteData } from '@tanstack/react-query'
import { useAuth } from '../hooks/useAuth'
import { useWebSocketEvent } from '../ws/useWebSocket'
import type { ConversationOut, MessageOut, MessagePage, WsEvent } from '../api/types'

type MessagesCache = InfiniteData<MessagePage, number | undefined>

function updateMessagesCache(
  queryClient: ReturnType<typeof useQueryClient>,
  conversationId: number,
  updater: (pages: MessagePage[]) => MessagePage[],
) {
  queryClient.setQueryData<MessagesCache>(['messages', conversationId], (old) => {
    if (!old) return old
    return { ...old, pages: updater(old.pages) }
  })
}

function touchConversation(
  queryClient: ReturnType<typeof useQueryClient>,
  conversationId: number,
  patch: (conversation: ConversationOut) => ConversationOut,
) {
  queryClient.setQueryData<ConversationOut[]>(['conversations'], (old) => {
    if (!old) return old
    if (!old.some((c) => c.id === conversationId)) {
      // Діалог ще не в кеші (перше повідомлення щойно створеного діалогу) — довантажимо список.
      queryClient.invalidateQueries({ queryKey: ['conversations'] })
      return old
    }
    return old.map((c) => (c.id === conversationId ? patch(c) : c))
  })
}

/** Підписує WS-події на кеш React Query — має бути змонтований один раз під час сесії
 * (див. App.tsx), щоб список діалогів і відкриті історії повідомлень лишались живими. */
export function useWebSocketSync() {
  const queryClient = useQueryClient()
  const { user } = useAuth()
  const currentUserId = user?.id

  const handler = useCallback(
    (event: WsEvent) => {
      switch (event.type) {
        case 'message:new': {
          const message = event.message
          updateMessagesCache(queryClient, event.conversation_id, (pages) => {
            if (pages.length === 0) return pages
            const [head, ...rest] = pages
            if (head.items.some((m) => m.id === message.id)) return pages
            return [{ ...head, items: [...head.items, message] }, ...rest]
          })
          touchConversation(queryClient, event.conversation_id, (c) => ({
            ...c,
            last_message: message,
            updated_at: message.created_at,
            unread_count: message.sender_id === currentUserId ? c.unread_count : c.unread_count + 1,
          }))
          break
        }
        case 'message:edit': {
          const message = event.message
          updateMessagesCache(queryClient, event.conversation_id, (pages) =>
            pages.map((page) => ({
              ...page,
              items: page.items.map((m) => (m.id === message.id ? message : m)),
            })),
          )
          touchConversation(queryClient, event.conversation_id, (c) =>
            c.last_message?.id === message.id ? { ...c, last_message: message } : c,
          )
          break
        }
        case 'message:delete': {
          const patchDeleted = (m: MessageOut): MessageOut =>
            m.id === event.message_id ? { ...m, content: '', is_deleted: true } : m
          updateMessagesCache(queryClient, event.conversation_id, (pages) =>
            pages.map((page) => ({ ...page, items: page.items.map(patchDeleted) })),
          )
          touchConversation(queryClient, event.conversation_id, (c) =>
            c.last_message?.id === event.message_id ? { ...c, last_message: patchDeleted(c.last_message) } : c,
          )
          break
        }
        case 'message:read': {
          if (event.user_id === currentUserId) break // я сам прочитав деінде — конфлікту з моєю сесією немає
          updateMessagesCache(queryClient, event.conversation_id, (pages) =>
            pages.map((page) => ({
              ...page,
              items: page.items.map((m) =>
                m.sender_id === currentUserId && m.id <= event.last_read_message_id
                  ? { ...m, is_read: true }
                  : m,
              ),
            })),
          )
          break
        }
        case 'user:online':
        case 'user:offline': {
          const isOnline = event.type === 'user:online'
          queryClient.setQueryData<ConversationOut[]>(['conversations'], (old) =>
            old?.map((c) =>
              c.partner.id === event.user_id
                ? {
                    ...c,
                    partner: {
                      ...c.partner,
                      is_online: isOnline,
                      last_seen_at: isOnline ? c.partner.last_seen_at : (event as { last_seen_at: string }).last_seen_at,
                    },
                  }
                : c,
            ),
          )
          break
        }
        default:
          break
      }
    },
    [queryClient, currentUserId],
  )

  useWebSocketEvent(handler)
}
