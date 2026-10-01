import { useInfiniteQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { messagesApi } from '../api/messages'
import type { ConversationOut, MessageOut } from '../api/types'

export function useMessages(conversationId: number | undefined) {
  return useInfiniteQuery({
    queryKey: ['messages', conversationId],
    queryFn: ({ pageParam }) => messagesApi.list(conversationId as number, { before_id: pageParam, limit: 40 }),
    initialPageParam: undefined as number | undefined,
    getNextPageParam: (lastPage) => {
      if (!lastPage.has_more || lastPage.items.length === 0) return undefined
      return lastPage.items[0].id
    },
    enabled: conversationId !== undefined,
    staleTime: 5_000,
  })
}

/** Повідомлення в хронологічному порядку: сторінки прийшли від найновішої до найстарішої. */
export function flattenMessages(pages: { items: MessageOut[] }[] | undefined): MessageOut[] {
  if (!pages) return []
  return [...pages].reverse().flatMap((page) => page.items)
}

interface MessagesCachePage {
  items: MessageOut[]
  has_more: boolean
}
interface MessagesCache {
  pages: MessagesCachePage[]
  pageParams: unknown[]
}

export function useSendMessage(conversationId: number) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (content: string) => messagesApi.send(conversationId, content),
    onSuccess: (message) => {
      queryClient.setQueryData<MessagesCache>(['messages', conversationId], (old) => {
        if (!old) return old
        const [head, ...rest] = old.pages
        if (head?.items.some((m) => m.id === message.id)) return old
        return { ...old, pages: [{ ...head, items: [...(head?.items ?? []), message] }, ...rest] }
      })
      queryClient.setQueryData<ConversationOut[]>(['conversations'], (old) =>
        old?.map((c) => (c.id === conversationId ? { ...c, last_message: message, updated_at: message.created_at } : c)),
      )
    },
  })
}

export function useEditMessage(conversationId: number) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ messageId, content }: { messageId: number; content: string }) =>
      messagesApi.edit(messageId, content),
    onSuccess: (message) => {
      patchMessage(queryClient, conversationId, message.id, () => message)
    },
  })
}

export function useDeleteMessage(conversationId: number) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (messageId: number) => messagesApi.remove(messageId),
    onSuccess: (message) => {
      patchMessage(queryClient, conversationId, message.id, () => message)
    },
  })
}

export function useMarkRead() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (messageId: number) => messagesApi.markRead(messageId),
    onSuccess: (result) => {
      queryClient.setQueryData<ConversationOut[]>(['conversations'], (old) =>
        old?.map((c) => (c.id === result.conversation_id ? { ...c, unread_count: result.unread_count } : c)),
      )
    },
  })
}

function patchMessage(
  queryClient: ReturnType<typeof useQueryClient>,
  conversationId: number,
  messageId: number,
  updater: (message: MessageOut) => MessageOut,
) {
  queryClient.setQueryData<MessagesCache>(['messages', conversationId], (old) => {
    if (!old) return old
    return {
      ...old,
      pages: old.pages.map((page) => ({
        ...page,
        items: page.items.map((m) => (m.id === messageId ? updater(m) : m)),
      })),
    }
  })
}
