import { useEffect, useMemo, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ArrowLeft, MoreVertical, ShieldOff, Trash2, UserRoundX } from 'lucide-react'
import { useConversations, useHideConversation } from '../../hooks/useConversations'
import { flattenMessages, useDeleteMessage, useEditMessage, useMarkRead, useMessages, useSendMessage } from '../../hooks/useMessages'
import { useAuth } from '../../hooks/useAuth'
import { useTyping } from '../../ws/TypingContext'
import { usersApi } from '../../api/users'
import { useQueryClient } from '@tanstack/react-query'
import { Avatar } from '../Avatar'
import { Composer } from '../Composer'
import { BlockBanner, DayDivider, MessageBubble } from '../MessageBubble'
import { TypingDots } from '../TypingDots'
import { EmptyState } from '../EmptyState'
import { formatDayDivider, formatLastSeen } from '../../utils/format'
import { useI18n } from '../../i18n/useI18n'

export function ChatWindow({ conversationId }: { conversationId: number }) {
  const { user } = useAuth()
  const { t } = useI18n()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { data: conversations } = useConversations()
  const conversation = conversations?.find((c) => c.id === conversationId)

  const messagesQuery = useMessages(conversationId)
  const sendMessage = useSendMessage(conversationId)
  const editMessage = useEditMessage(conversationId)
  const deleteMessage = useDeleteMessage(conversationId)
  const markRead = useMarkRead()
  const hideConversation = useHideConversation()
  const { isTyping } = useTyping()

  const [menuOpen, setMenuOpen] = useState(false)
  const scrollRef = useRef<HTMLDivElement>(null)
  const prevHeightRef = useRef<number>(0)
  const isFetchingOlderRef = useRef(false)
  const lastMessageCountRef = useRef(0)

  const messages = useMemo(() => flattenMessages(messagesQuery.data?.pages), [messagesQuery.data])
  const partnerTyping = conversation ? isTyping(conversation.id, conversation.partner.id) : false

  // Позначаємо останнє непрочитане чуже повідомлення прочитаним, коли вікно з ним відкрите.
  useEffect(() => {
    if (!conversation || conversation.unread_count === 0) return
    const lastUnreadIncoming = [...messages].reverse().find((m) => m.sender_id !== user?.id && !m.is_read)
    if (lastUnreadIncoming) markRead.mutate(lastUnreadIncoming.id)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [conversation?.id, messages.length, conversation?.unread_count])

  // Автопрокрутка донизу при відкритті діалогу й появі нових повідомлень (не при довантаженні історії вгору).
  useEffect(() => {
    const el = scrollRef.current
    if (!el) return
    if (isFetchingOlderRef.current) {
      el.scrollTop = el.scrollHeight - prevHeightRef.current
      isFetchingOlderRef.current = false
      return
    }
    const grew = messages.length > lastMessageCountRef.current
    const nearBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 200
    if (grew && (nearBottom || lastMessageCountRef.current === 0)) {
      el.scrollTop = el.scrollHeight
    }
    lastMessageCountRef.current = messages.length
  }, [messages.length])

  useEffect(() => {
    lastMessageCountRef.current = 0
    requestAnimationFrame(() => {
      if (scrollRef.current) scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    })
  }, [conversationId])

  function handleScroll() {
    const el = scrollRef.current
    if (!el || !messagesQuery.hasNextPage || messagesQuery.isFetchingNextPage) return
    if (el.scrollTop < 120) {
      prevHeightRef.current = el.scrollHeight
      isFetchingOlderRef.current = true
      messagesQuery.fetchNextPage()
    }
  }

  async function handleUnblock() {
    if (!conversation) return
    await usersApi.unblock(conversation.partner.id)
    queryClient.invalidateQueries({ queryKey: ['conversations'] })
  }

  if (!conversation) {
    return (
      <div className="flex flex-1 items-center justify-center text-sm text-ink-500">
        {t('chat.loadingConversation')}
      </div>
    )
  }

  const { partner } = conversation
  const blocked = !conversation.can_send

  return (
    <div className="flex h-dvh flex-1 flex-col bg-ink-950">
      <header className="flex items-center gap-3 border-b border-ink-800 bg-ink-900 px-4 py-3">
        <button onClick={() => navigate('/chat')} className="text-ink-400 hover:text-ink-100 md:hidden" aria-label={t('common.back')}>
          <ArrowLeft size={20} />
        </button>
        <Avatar name={partner.display_name} id={partner.id} avatarUrl={partner.avatar_url} online={partner.is_online} />
        <div className="min-w-0 flex-1">
          <p className="truncate text-[15px] font-medium text-ink-50">{partner.display_name}</p>
          {partnerTyping ? (
            <TypingDots label={t('chat.typing')} />
          ) : (
            <p className="truncate text-xs text-ink-500">
              {partner.is_online ? t('chat.online') : formatLastSeen(partner.last_seen_at)}
            </p>
          )}
        </div>
        <div className="relative">
          <button
            onClick={() => setMenuOpen((v) => !v)}
            className="rounded-lg p-2 text-ink-400 hover:bg-ink-800 hover:text-ink-100"
            aria-label={t('chat.actions')}
          >
            <MoreVertical size={18} />
          </button>
          {menuOpen && (
            <div className="absolute top-full right-0 z-10 mt-1 w-56 overflow-hidden rounded-lg border border-ink-700 bg-ink-850 shadow-panel">
              <button
                onClick={() => {
                  setMenuOpen(false)
                  if (conversation.blocked_by_me) void handleUnblock()
                  else void usersApi.block(partner.id).then(() => queryClient.invalidateQueries({ queryKey: ['conversations'] }))
                }}
                className="flex w-full items-center gap-2.5 px-3.5 py-2.5 text-left text-sm text-ink-100 hover:bg-ink-800"
              >
                {conversation.blocked_by_me ? <ShieldOff size={16} /> : <UserRoundX size={16} />}
                {conversation.blocked_by_me ? t('common.unblock') : t('common.block')}
              </button>
              <button
                onClick={() => {
                  setMenuOpen(false)
                  hideConversation.mutate(conversation.id)
                  navigate('/chat')
                }}
                className="flex w-full items-center gap-2.5 border-t border-ink-800 px-3.5 py-2.5 text-left text-sm text-rose-400 hover:bg-ink-800"
              >
                <Trash2 size={16} /> {t('chat.deleteConversation')}
              </button>
            </div>
          )}
        </div>
      </header>

      <div ref={scrollRef} onScroll={handleScroll} className="scrollbar-thin flex-1 overflow-y-auto px-5 py-4">
        {messagesQuery.isLoading ? (
          <div className="flex h-full items-center justify-center text-sm text-ink-500">{t('common.loading')}</div>
        ) : messages.length === 0 ? (
          <EmptyState
            title={t('chat.startTitle', { name: partner.display_name })}
            description={t('chat.startDescription')}
          />
        ) : (
          <MessageList messages={messages} currentUserId={user!.id} onEdit={(id, content) => editMessage.mutate({ messageId: id, content })} onDelete={(id) => deleteMessage.mutate(id)} />
        )}
      </div>

      {blocked ? (
        <BlockBanner blockedByMe={conversation.blocked_by_me} onUnblock={handleUnblock} />
      ) : (
        <Composer conversationId={conversation.id} disabled={sendMessage.isPending} onSend={(content) => sendMessage.mutate(content)} />
      )}
    </div>
  )
}

function MessageList({
  messages,
  currentUserId,
  onEdit,
  onDelete,
}: {
  messages: ReturnType<typeof flattenMessages>
  currentUserId: number
  onEdit: (id: number, content: string) => void
  onDelete: (id: number) => void
}) {
  let lastDay: string | null = null
  return (
    <div className="flex flex-col gap-1.5">
      {messages.map((message) => {
        const day = message.created_at.slice(0, 10)
        const showDivider = day !== lastDay
        lastDay = day
        return (
          <div key={message.id}>
            {showDivider && <DayDivider label={formatDayDivider(message.created_at)} />}
            <MessageBubble
              message={message}
              mine={message.sender_id === currentUserId}
              onEdit={(content) => onEdit(message.id, content)}
              onDelete={() => onDelete(message.id)}
            />
          </div>
        )
      })}
    </div>
  )
}
