import { useContext, useEffect } from 'react'
import { WsContext } from './WebSocketContext'
import type { WsEvent } from '../api/types'

export function useWebSocket() {
  const ctx = useContext(WsContext)
  if (!ctx) throw new Error('useWebSocket має використовуватись всередині <WebSocketProvider>')
  return ctx
}

export function useWebSocketEvent(handler: (event: WsEvent) => void) {
  const { subscribe } = useWebSocket()
  useEffect(() => subscribe(handler), [subscribe, handler])
}
