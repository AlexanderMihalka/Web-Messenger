import { useState } from 'react'
import { clsx } from 'clsx'
import { Check, CheckCheck, Pencil, Trash2, X } from 'lucide-react'
import type { MessageOut } from '../api/types'
import { formatMessageTime } from '../utils/format'
import { Button } from './Button'

interface MessageBubbleProps {
  message: MessageOut
  mine: boolean
  onEdit: (content: string) => void
  onDelete: () => void
}

export function MessageBubble({ message, mine, onEdit, onDelete }: MessageBubbleProps) {
  const [editing, setEditing] = useState(false)
  const [draft, setDraft] = useState(message.content)
  const [hovering, setHovering] = useState(false)

  function submitEdit() {
    const trimmed = draft.trim()
    if (trimmed && trimmed !== message.content) onEdit(trimmed)
    setEditing(false)
  }

  return (
    <div
      className={clsx('group flex', mine ? 'justify-end' : 'justify-start')}
      onMouseEnter={() => setHovering(true)}
      onMouseLeave={() => setHovering(false)}
    >
      <div className={clsx('flex max-w-[70%] items-end gap-1.5', mine && 'flex-row-reverse')}>
        {mine && !message.is_deleted && (
          <div
            className={clsx(
              'flex items-center gap-0.5 pb-1 transition-opacity',
              hovering ? 'opacity-100' : 'opacity-0',
            )}
          >
            <button
              onClick={() => setEditing(true)}
              className="rounded p-1 text-ink-500 hover:bg-ink-800 hover:text-ink-200"
              aria-label="Редагувати"
            >
              <Pencil size={13} />
            </button>
            <button
              onClick={onDelete}
              className="rounded p-1 text-ink-500 hover:bg-ink-800 hover:text-rose-400"
              aria-label="Видалити"
            >
              <Trash2 size={13} />
            </button>
          </div>
        )}

        <div
          className={clsx(
            'animate-bubble-in px-3.5 py-2.5 text-[14.5px] leading-relaxed break-words',
            mine
              ? 'rounded-2xl rounded-br-md bg-signal-500 text-ink-950'
              : 'rounded-2xl rounded-bl-md bg-ink-800 text-ink-50',
          )}
        >
          {editing ? (
            <div className="flex min-w-[180px] flex-col gap-2">
              <textarea
                autoFocus
                value={draft}
                onChange={(e) => setDraft(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault()
                    submitEdit()
                  }
                  if (e.key === 'Escape') setEditing(false)
                }}
                className="min-h-[44px] w-full resize-none rounded-md bg-ink-950/20 px-2 py-1 text-ink-950 outline-none"
                rows={2}
              />
              <div className="flex items-center justify-end gap-2 text-ink-950">
                <button onClick={() => setEditing(false)} className="rounded p-1 hover:bg-ink-950/10" aria-label="Скасувати">
                  <X size={14} />
                </button>
                <button onClick={submitEdit} className="rounded p-1 hover:bg-ink-950/10" aria-label="Зберегти">
                  <Check size={14} />
                </button>
              </div>
            </div>
          ) : message.is_deleted ? (
            <span className={clsx('italic', mine ? 'text-ink-950/60' : 'text-ink-400')}>Повідомлення видалено</span>
          ) : (
            <span className="whitespace-pre-wrap">{message.content}</span>
          )}

          {!editing && (
            <div
              className={clsx(
                'mt-1 flex items-center gap-1 text-[11px]',
                mine ? 'justify-end text-ink-950/60' : 'justify-start text-ink-500',
              )}
            >
              {message.is_edited && !message.is_deleted && <span>ред.</span>}
              <span>{formatMessageTime(message.created_at)}</span>
              {mine && !message.is_deleted && (message.is_read ? <CheckCheck size={13} /> : <Check size={13} />)}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export function DayDivider({ label }: { label: string }) {
  return (
    <div className="my-4 flex items-center gap-3 px-2">
      <div className="h-px flex-1 bg-ink-800" />
      <span className="text-xs text-ink-500">{label}</span>
      <div className="h-px flex-1 bg-ink-800" />
    </div>
  )
}

export function BlockBanner({ blockedByMe, onUnblock }: { blockedByMe: boolean; onUnblock: () => void }) {
  return (
    <div className="flex items-center justify-between gap-3 border-t border-ink-800 bg-ink-900 px-5 py-3 text-sm">
      <span className="text-ink-400">
        {blockedByMe
          ? 'Ви заблокували цього користувача — повідомлення надсилати не можна.'
          : 'Цей користувач заблокував вас — повідомлення надсилати не можна.'}
      </span>
      {blockedByMe && (
        <Button variant="outline" size="sm" onClick={onUnblock}>
          Розблокувати
        </Button>
      )}
    </div>
  )
}
