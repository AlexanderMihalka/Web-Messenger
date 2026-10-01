import { clsx } from 'clsx'
import { Avatar } from './Avatar'
import { formatRelativeTime } from '../utils/format'
import type { ConversationOut } from '../api/types'
import { useTyping } from '../ws/TypingContext'
import { TypingDots } from './TypingDots'

export function ConversationListItem({
  conversation,
  active,
  currentUserId,
  onClick,
}: {
  conversation: ConversationOut
  active: boolean
  currentUserId: number
  onClick: () => void
}) {
  const { partner, last_message, unread_count } = conversation
  const { isTyping } = useTyping()
  const partnerTyping = isTyping(conversation.id, partner.id)

  return (
    <button
      onClick={onClick}
      className={clsx(
        'flex w-full items-center gap-3 border-l-2 px-4 py-3 text-left transition-colors',
        active ? 'border-signal-500 bg-ink-800' : 'border-transparent hover:bg-ink-850',
      )}
    >
      <Avatar name={partner.display_name} id={partner.id} avatarUrl={partner.avatar_url} online={partner.is_online} />
      <div className="min-w-0 flex-1">
        <div className="flex items-center justify-between gap-2">
          <span className="truncate text-[15px] font-medium text-ink-50">{partner.display_name}</span>
          {last_message && (
            <span className="shrink-0 text-xs text-ink-500">{formatRelativeTime(last_message.created_at)}</span>
          )}
        </div>
        <div className="mt-0.5 flex items-center justify-between gap-2">
          {partnerTyping ? (
            <TypingDots />
          ) : (
            <span className="truncate text-sm text-ink-400">{previewText(conversation, currentUserId)}</span>
          )}
          {unread_count > 0 && (
            <span className="flex h-5 min-w-5 shrink-0 items-center justify-center rounded-full bg-signal-500 px-1.5 text-[11px] font-semibold text-ink-950">
              {unread_count > 99 ? '99+' : unread_count}
            </span>
          )}
        </div>
      </div>
    </button>
  )
}

function previewText(conversation: ConversationOut, currentUserId: number): string {
  const { last_message: message } = conversation
  if (!message) return 'Немає повідомлень'
  if (message.is_deleted) return 'Повідомлення видалено'
  const prefix = message.sender_id === currentUserId ? 'Ви: ' : ''
  return `${prefix}${message.content}`
}
