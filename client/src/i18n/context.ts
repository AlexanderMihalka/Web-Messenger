import { createContext } from 'react'
import type { Lang } from './core'
import type { MessageKey } from './messages'

export interface I18nValue {
  lang: Lang
  setLang: (lang: Lang) => void
  t: (key: MessageKey, params?: Record<string, string | number>) => string
}

// Контекст експортується окремо від компонента-провайдера, щоб файли з компонентами
// лишались сумісними з React Fast Refresh (так само зроблено для AuthContext).
export const I18nContext = createContext<I18nValue | null>(null)
