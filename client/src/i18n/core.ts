import { enUS, uk as ukLocale } from 'date-fns/locale'
import type { Locale } from 'date-fns'
import { messages, serverMessagesEn, serverPatternsEn, type MessageKey } from './messages'

export const LANGS = ['uk', 'en'] as const
export type Lang = (typeof LANGS)[number]

const STORAGE_KEY = 'lang'
const DEFAULT_LANG: Lang = 'uk'

function readSavedLang(): Lang {
  try {
    const saved = window.localStorage.getItem(STORAGE_KEY)
    if (saved && (LANGS as readonly string[]).includes(saved)) return saved as Lang
  } catch {
    // localStorage може бути недоступний (приватний режим) — тоді мова за замовчуванням
  }
  return DEFAULT_LANG
}

// Поточна мова дублюється в змінній модуля, щоб її могли читати й не-компоненти
// (api/client.ts, utils/format.ts), де хуків немає. Компоненти перемальовуються через контекст.
let currentLang: Lang = readSavedLang()

export function getLang(): Lang {
  return currentLang
}

export function setCurrentLang(lang: Lang): void {
  currentLang = lang
  try {
    window.localStorage.setItem(STORAGE_KEY, lang)
  } catch {
    // не вдалося зберегти — мова все одно працює до перезавантаження сторінки
  }
}

export function translate(key: MessageKey, params?: Record<string, string | number>): string {
  let text: string = messages[currentLang][key] ?? messages[DEFAULT_LANG][key] ?? key
  if (params) {
    for (const [name, value] of Object.entries(params)) {
      text = text.replaceAll(`{${name}}`, String(value))
    }
  }
  return text
}

export function getDateLocale(): Locale {
  return currentLang === 'en' ? enUS : ukLocale
}

/** Тег локалі для toLocaleString / Intl. */
export function getLocaleTag(): string {
  return currentLang === 'en' ? 'en-GB' : 'uk-UA'
}

/** Текст помилки від бекенду (він пише українською) → на поточну мову, якщо переклад відомий. */
export function translateServerMessage(text: string): string {
  if (currentLang === 'uk') return text
  const exact = serverMessagesEn[text]
  if (exact) return exact
  for (const [pattern, template] of serverPatternsEn) {
    const match = pattern.exec(text)
    if (match) return template.replace('{0}', match[1])
  }
  return text
}
