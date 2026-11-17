import { clsx } from 'clsx'
import { LANGS } from '../i18n/core'
import { useI18n } from '../i18n/useI18n'

/** Перемикач мови UK / EN. Вибір зберігається в localStorage під ключем `lang`. */
export function LangSwitch({ className }: { className?: string }) {
  const { lang, setLang, t } = useI18n()
  return (
    <div
      role="group"
      aria-label={t('common.language')}
      className={clsx('inline-flex rounded-lg border border-ink-700 bg-ink-900 p-0.5 text-xs font-semibold', className)}
    >
      {LANGS.map((code) => (
        <button
          key={code}
          type="button"
          onClick={() => setLang(code)}
          aria-pressed={lang === code}
          className={clsx(
            'rounded-md px-2 py-1 uppercase transition-colors',
            lang === code ? 'bg-signal-500 text-ink-950' : 'text-ink-400 hover:text-ink-100',
          )}
        >
          {code}
        </button>
      ))}
    </div>
  )
}
