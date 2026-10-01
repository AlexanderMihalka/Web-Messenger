import { useMemo, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { Search, SquarePen } from 'lucide-react'
import { useConversations, useStartConversation } from '../../hooks/useConversations'
import { useAuth } from '../../hooks/useAuth'
import { ConversationListItem } from '../ConversationListItem'
import { UserSearchResults } from '../UserSearchResults'
import { UserMenu } from '../UserMenu'

export function Sidebar() {
  const { user } = useAuth()
  const navigate = useNavigate()
  const { conversationId } = useParams()
  const { data: conversations, isLoading } = useConversations()
  const startConversation = useStartConversation()
  const [query, setQuery] = useState('')
  const [searching, setSearching] = useState(false)

  const activeId = conversationId ? Number(conversationId) : undefined

  const totalUnread = useMemo(
    () => conversations?.reduce((sum, c) => sum + (c.unread_count > 0 ? 1 : 0), 0) ?? 0,
    [conversations],
  )

  async function pickUser(userId: number) {
    const conversation = await startConversation.mutateAsync(userId)
    setQuery('')
    setSearching(false)
    navigate(`/chat/${conversation.id}`)
  }

  return (
    <aside className="flex h-dvh w-full max-w-[360px] shrink-0 flex-col border-r border-ink-800 bg-ink-900">
      <div className="flex items-center justify-between gap-2 px-4 pt-5 pb-3">
        <div className="flex items-center gap-2">
          <Logo />
          <span className="font-display text-lg text-ink-50">Messenger</span>
        </div>
        {totalUnread > 0 && (
          <span className="rounded-full bg-signal-500/15 px-2 py-0.5 text-xs font-medium text-signal-400">
            {totalUnread} нових
          </span>
        )}
      </div>

      <div className="px-4 pb-3">
        <div className="relative">
          <Search size={16} className="pointer-events-none absolute top-1/2 left-3 -translate-y-1/2 text-ink-500" />
          <input
            value={query}
            onChange={(e) => {
              setQuery(e.target.value)
              setSearching(e.target.value.trim().length > 0)
            }}
            onFocus={() => setSearching(query.trim().length > 0)}
            placeholder="Знайти людей за іменем…"
            className="w-full rounded-lg border border-ink-700 bg-ink-950 py-2.5 pr-3 pl-9 text-sm text-ink-50 placeholder:text-ink-500 focus:border-signal-400 focus:outline-none"
          />
        </div>
      </div>

      <div className="scrollbar-thin flex-1 overflow-y-auto">
        {searching ? (
          <UserSearchResults query={query} onPick={pickUser} />
        ) : isLoading ? (
          <div className="px-4 py-6 text-sm text-ink-500">Завантаження…</div>
        ) : conversations && conversations.length > 0 ? (
          conversations.map((conversation) => (
            <ConversationListItem
              key={conversation.id}
              conversation={conversation}
              active={conversation.id === activeId}
              currentUserId={user!.id}
              onClick={() => navigate(`/chat/${conversation.id}`)}
            />
          ))
        ) : (
          <div className="flex flex-col items-center gap-2 px-6 py-10 text-center">
            <SquarePen size={28} className="text-ink-600" />
            <p className="text-sm text-ink-500">
              Ще немає діалогів. Знайдіть когось у пошуку вище, щоб почати розмову.
            </p>
          </div>
        )}
      </div>

      <UserMenu />
    </aside>
  )
}

function Logo() {
  return (
    <svg width="26" height="26" viewBox="0 0 32 32" fill="none">
      <rect width="32" height="32" rx="8" fill="#C89B3C" />
      <path
        d="M7 11a3 3 0 0 1 3-3h12a3 3 0 0 1 3 3v7a3 3 0 0 1-3 3H14l-5 4v-4a3 3 0 0 1-2-2.8Z"
        fill="#0B0E13"
      />
    </svg>
  )
}
