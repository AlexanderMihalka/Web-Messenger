import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { conversationsApi } from '../api/conversations'
import type { ConversationOut } from '../api/types'

export function useConversations() {
  return useQuery({
    queryKey: ['conversations'],
    queryFn: conversationsApi.list,
    staleTime: 10_000,
  })
}

export function useStartConversation() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (userId: number) => conversationsApi.create(userId),
    onSuccess: (conversation) => {
      queryClient.setQueryData<ConversationOut[]>(['conversations'], (old) => {
        if (!old) return [conversation]
        if (old.some((c) => c.id === conversation.id)) {
          return old.map((c) => (c.id === conversation.id ? conversation : c))
        }
        return [conversation, ...old]
      })
    },
  })
}

export function useHideConversation() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (conversationId: number) => conversationsApi.remove(conversationId),
    onSuccess: (_data, conversationId) => {
      queryClient.setQueryData<ConversationOut[]>(['conversations'], (old) =>
        old?.filter((c) => c.id !== conversationId),
      )
    },
  })
}
