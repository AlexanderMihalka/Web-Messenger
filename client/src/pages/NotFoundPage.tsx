import { Link } from 'react-router-dom'
import { Button } from '../components/Button'
import { useI18n } from '../i18n/useI18n'

export function NotFoundPage() {
  const { t } = useI18n()
  return (
    <div className="flex min-h-dvh flex-col items-center justify-center gap-3 bg-ink-950 px-6 text-center">
      <p className="font-display text-5xl text-ink-50">404</p>
      <p className="text-ink-400">{t('notFound.text')}</p>
      <Link to="/chat">
        <Button className="mt-2">{t('notFound.home')}</Button>
      </Link>
    </div>
  )
}
