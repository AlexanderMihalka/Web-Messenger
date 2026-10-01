import { createContext, useCallback, useEffect, useMemo, useRef, useState, type ReactNode } from 'react'
import { refreshAccessToken } from '../api/client'
import { getAccessToken } from '../api/client'
import { useAuth } from '../hooks/useAuth'
import type { WsEvent } from '../api/types'

type EventHandler = (event: WsEvent) => void

interface WsContextValue {
  connected: boolean
  subscribe: (handler: EventHandler) => () => void
  sendTyping: (conversationId: number, isTyping: boolean) => void
}

export const WsContext = createContext<WsContextValue | null>(null)

const MAX_BACKOFF_MS = 15_000

export function WebSocketProvider({ children }: { children: ReactNode }) {
  const { status } = useAuth()
  const [connected, setConnected] = useState(false)
  const wsRef = useRef<WebSocket | null>(null)
  const handlersRef = useRef(new Set<EventHandler>())
  const attemptRef = useRef(0)
  const timerRef = useRef<number | null>(null)
  const activeRef = useRef(false)

  const subscribe = useCallback((handler: EventHandler) => {
    handlersRef.current.add(handler)
    return () => {
      handlersRef.current.delete(handler)
    }
  }, [])

  const sendTyping = useCallback((conversationId: number, isTyping: boolean) => {
    const ws = wsRef.current
    if (ws?.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ type: isTyping ? 'typing:start' : 'typing:stop', conversation_id: conversationId }))
    }
  }, [])

  useEffect(() => {
    activeRef.current = status === 'authenticated'
    if (!activeRef.current) {
      wsRef.current?.close()
      return
    }

    const connect = () => {
      if (!activeRef.current) return
      const token = getAccessToken()
      if (!token) return
      const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws'
      const socket = new WebSocket(`${protocol}://${window.location.host}/ws?token=${encodeURIComponent(token)}`)
      wsRef.current = socket

      socket.onopen = () => {
        attemptRef.current = 0
        setConnected(true)
      }
      socket.onmessage = (event: MessageEvent<string>) => {
        try {
          const data = JSON.parse(event.data) as WsEvent
          handlersRef.current.forEach((handler) => handler(data))
        } catch {
          // ігноруємо, якщо сервер надішле щось нерозпізнане
        }
      }
      socket.onclose = (event) => {
        setConnected(false)
        wsRef.current = null
        if (!activeRef.current) return
        const delay = Math.min(1000 * 2 ** attemptRef.current, MAX_BACKOFF_MS)
        attemptRef.current += 1
        timerRef.current = window.setTimeout(async () => {
          if (event.code === 4401) {
            // Токен, яким з'єдналися, більше не дійсний — спершу оновлюємо його.
            // Якщо й це не вдасться, AuthContext сам поверне на екран входу.
            try {
              await refreshAccessToken()
            } catch {
              return
            }
          }
          connect()
        }, delay)
      }
      socket.onerror = () => socket.close()
    }

    connect()

    return () => {
      activeRef.current = false
      if (timerRef.current) window.clearTimeout(timerRef.current)
      wsRef.current?.close()
      wsRef.current = null
    }
  }, [status])

  const value = useMemo(() => ({ connected, subscribe, sendTyping }), [connected, subscribe, sendTyping])
  return <WsContext.Provider value={value}>{children}</WsContext.Provider>
}
