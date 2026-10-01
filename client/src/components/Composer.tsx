import { useRef, useState, type KeyboardEvent } from 'react'
import { Send } from 'lucide-react'
import { useWebSocket } from '../ws/useWebSocket'

const TYPING_STOP_DELAY_MS = 2000

export function Composer({
  conversationId,
  disabled,
  onSend,
}: {
  conversationId: number
  disabled: boolean
  onSend: (content: string) => void
}) {
  const [value, setValue] = useState('')
  const { sendTyping } = useWebSocket()
  const stopTimerRef = useRef<number | null>(null)
  const typingRef = useRef(false)

  function notifyTyping(hasContent: boolean) {
    if (hasContent && !typingRef.current) {
      typingRef.current = true
      sendTyping(conversationId, true)
    }
    if (stopTimerRef.current) window.clearTimeout(stopTimerRef.current)
    stopTimerRef.current = window.setTimeout(() => {
      typingRef.current = false
      sendTyping(conversationId, false)
    }, TYPING_STOP_DELAY_MS)
  }

  function submit() {
    const trimmed = value.trim()
    if (!trimmed) return
    onSend(trimmed)
    setValue('')
    if (stopTimerRef.current) window.clearTimeout(stopTimerRef.current)
    if (typingRef.current) {
      typingRef.current = false
      sendTyping(conversationId, false)
    }
  }

  function handleKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault()
      submit()
    }
  }

  return (
    <div className="flex items-end gap-3 border-t border-ink-800 bg-ink-900 px-5 py-4">
      <textarea
        value={value}
        onChange={(e) => {
          setValue(e.target.value)
          notifyTyping(e.target.value.trim().length > 0)
        }}
        onKeyDown={handleKeyDown}
        disabled={disabled}
        placeholder={disabled ? 'Надсилання недоступне' : 'Напишіть повідомлення…'}
        rows={1}
        className="max-h-32 min-h-[42px] flex-1 resize-none rounded-xl border border-ink-600 bg-ink-950 px-4 py-2.5 text-[14.5px] text-ink-50 placeholder:text-ink-500 focus:border-signal-400 focus:outline-none disabled:opacity-50"
      />
      <button
        onClick={submit}
        disabled={disabled || !value.trim()}
        aria-label="Надіслати"
        className="flex h-[42px] w-[42px] shrink-0 items-center justify-center rounded-xl bg-signal-500 text-ink-950 transition-colors hover:bg-signal-400 disabled:cursor-not-allowed disabled:opacity-40"
      >
        <Send size={18} />
      </button>
    </div>
  )
}
