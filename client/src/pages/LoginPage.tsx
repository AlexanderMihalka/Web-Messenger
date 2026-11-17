import { useState, type FormEvent } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { Eye, EyeOff } from 'lucide-react'
import { AuthLayout } from '../components/AuthLayout'
import { Button } from '../components/Button'
import { FormField } from '../components/FormField'
import { useAuth } from '../hooks/useAuth'
import { toApiError } from '../api/client'
import { useI18n } from '../i18n/useI18n'

export function LoginPage() {
  const { login } = useAuth()
  const { t } = useI18n()
  const navigate = useNavigate()
  const location = useLocation()
  const [loginValue, setLoginValue] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    setError(null)
    setSubmitting(true)
    try {
      await login(loginValue, password)
      const redirectTo = (location.state as { from?: Location })?.from?.pathname ?? '/chat'
      navigate(redirectTo, { replace: true })
    } catch (err) {
      setError(toApiError(err).message)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <AuthLayout>
      <h1 className="font-display text-3xl text-ink-50">{t('login.title')}</h1>
      <p className="mt-2 text-sm text-ink-400">{t('login.subtitle')}</p>

      <form className="mt-8 space-y-4" onSubmit={handleSubmit}>
        <FormField
          label={t('login.loginLabel')}
          name="login"
          autoComplete="username"
          value={loginValue}
          onChange={(e) => setLoginValue(e.target.value)}
          required
          autoFocus
        />
        <FormField
          label={t('login.password')}
          name="password"
          type={showPassword ? 'text' : 'password'}
          autoComplete="current-password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
          rightSlot={
            <button
              type="button"
              onClick={() => setShowPassword((v) => !v)}
              className="text-ink-400 hover:text-ink-200"
              aria-label={showPassword ? t('login.hidePassword') : t('login.showPassword')}
              tabIndex={-1}
            >
              {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
            </button>
          }
        />

        {error && (
          <p role="alert" className="rounded-lg bg-rose-500/10 px-3.5 py-2.5 text-sm text-rose-400">
            {error}
          </p>
        )}

        <Button type="submit" className="w-full" disabled={submitting}>
          {submitting ? t('login.submitting') : t('login.submit')}
        </Button>
      </form>

      <p className="mt-6 text-center text-sm text-ink-400">
        {t('login.noAccount')}{' '}
        <Link to="/register" className="font-medium text-signal-400 hover:text-signal-300">
          {t('login.toRegister')}
        </Link>
      </p>
    </AuthLayout>
  )
}
