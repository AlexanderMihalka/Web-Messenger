import { createContext, useCallback, useContext, useEffect, useRef, useState, type ReactNode } from 'react'
import { useWebSocketEvent } from './useWebSocket'

const TYPING_TIMEOUT_MS = 4000

interface TypingContextValue {
  isTyping: (conversationId: number, userId: number) => boolean
}

const TypingContext = createContext<TypingContextValue | null>(null)

export function TypingProvider({ children }: { children: ReactNode }) {
  // conversationId -> Set<userId>, тримаємо в стейті лише для перерендеру, а не для логіки
  const [typingMap, setTypingMap] = useState<Record<number, number[]>>({})
  const timers = useRef(new Map<string, number>())

  const setUserTyping = useCallback((conversationId: number, userId: number, typing: boolean) => {
    const key = `${conversationId}:${userId}`
    const existing = timers.current.get(key)
    if (existing) window.clearTimeout(existing)

    if (typing) {
      timers.current.set(
        key,
        window.setTimeout(() => setUserTyping(conversationId, userId, false), TYPING_TIMEOUT_MS),
      )
    } else {
      timers.current.delete(key)
    }

    setTypingMap((prev) => {
      const current = new Set(prev[conversationId] ?? [])
      if (typing) current.add(userId)
      else current.delete(userId)
      return { ...prev, [conversationId]: [...current] }
    })
  }, [])

  useWebSocketEvent(
    useCallback(
      (event) => {
        if (event.type === 'typing:start') setUserTyping(event.conversation_id, event.user_id, true)
        if (event.type === 'typing:stop') setUserTyping(event.conversation_id, event.user_id, false)
        if (event.type === 'message:new') setUserTyping(event.conversation_id, event.message.sender_id ?? -1, false)
      },
      [setUserTyping],
    ),
  )

  useEffect(() => {
    const timerMap = timers.current
    return () => timerMap.forEach((id) => window.clearTimeout(id))
  }, [])

  const isTyping = useCallback(
    (conversationId: number, userId: number) => (typingMap[conversationId] ?? []).includes(userId),
    [typingMap],
  )

  return <TypingContext.Provider value={{ isTyping }}>{children}</TypingContext.Provider>
}

export function useTyping() {
  const ctx = useContext(TypingContext)
  if (!ctx) throw new Error('useTyping має використовуватись всередині <TypingProvider>')
  return ctx
}
