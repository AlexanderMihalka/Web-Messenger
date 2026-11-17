import type { ReactNode } from 'react'
import { useI18n } from '../i18n/useI18n'
import { LangSwitch } from './LangSwitch'

export function AuthLayout({ children }: { children: ReactNode }) {
  const { t } = useI18n()
  return (
    <div className="grid min-h-dvh md:grid-cols-2">
      <div className="relative hidden flex-col justify-between overflow-hidden bg-ink-950 p-12 md:flex">
        <BackgroundMark />
        <div className="relative z-10 flex items-center gap-2.5 text-ink-100">
          <svg width="28" height="28" viewBox="0 0 32 32" fill="none">
            <rect width="32" height="32" rx="8" fill="#C89B3C" />
            <path
              d="M7 11a3 3 0 0 1 3-3h12a3 3 0 0 1 3 3v7a3 3 0 0 1-3 3H14l-5 4v-4a3 3 0 0 1-2-2.8Z"
              fill="#0B0E13"
            />
          </svg>
          <span className="font-display text-lg">Messenger</span>
        </div>

        <div className="relative z-10 max-w-md">
          <p className="font-display text-4xl leading-[1.15] text-ink-50">
            {t('authLayout.tagline')}
          </p>
          <p className="mt-4 text-[15px] leading-relaxed text-ink-400">
            {t('authLayout.description')}
          </p>
        </div>

        <p className="relative z-10 text-xs text-ink-500">
          {t('authLayout.footer')}
        </p>
      </div>

      <div className="relative flex items-center justify-center bg-ink-950 px-6 py-12 md:bg-ink-900">
        <LangSwitch className="absolute top-4 right-4" />
        <div className="w-full max-w-[380px]">{children}</div>
      </div>
    </div>
  )
}

function BackgroundMark() {
  return (
    <svg
      className="pointer-events-none absolute -right-24 -bottom-24 opacity-[0.14]"
      width="520"
      height="520"
      viewBox="0 0 520 520"
      fill="none"
    >
      <rect x="60" y="40" width="300" height="200" rx="28" stroke="#C89B3C" strokeWidth="1.5" />
      <rect x="140" y="150" width="300" height="200" rx="28" stroke="#4FB08C" strokeWidth="1.5" />
      <rect x="100" y="260" width="220" height="150" rx="24" stroke="#6b7690" strokeWidth="1.5" />
    </svg>
  )
}
