import { useCallback, useEffect, useMemo, useState, type ReactNode } from 'react'
import { I18nContext, type I18nValue } from './context'
import { LANGS, getLang, setCurrentLang, translate, type Lang } from './core'

export function I18nProvider({ children }: { children: ReactNode }) {
  const [lang, setLangState] = useState<Lang>(getLang)

  useEffect(() => {
    document.documentElement.lang = lang
  }, [lang])

  const setLang = useCallback((next: Lang) => {
    if (!LANGS.includes(next)) return
    setCurrentLang(next)
    setLangState(next)
  }, [])

  // Об'єкт змінюється разом із мовою, тож усі споживачі контексту перемальовуються.
  const value = useMemo<I18nValue>(
    () => ({ lang, setLang, t: (key, params) => translate(key, params) }),
    [lang, setLang],
  )

  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>
}
