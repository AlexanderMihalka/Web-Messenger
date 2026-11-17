import { useState, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { AuthLayout } from '../components/AuthLayout'
import { Button } from '../components/Button'
import { FormField } from '../components/FormField'
import { useAuth } from '../hooks/useAuth'
import { toApiError } from '../api/client'
import { useI18n } from '../i18n/useI18n'

export function RegisterPage() {
  const { register } = useAuth()
  const { t } = useI18n()
  const navigate = useNavigate()
  const [form, setForm] = useState({
    username: '',
    email: '',
    password: '',
    confirm_password: '',
    display_name: '',
  })
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({})
  const [formError, setFormError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  function update<K extends keyof typeof form>(key: K, value: string) {
    setForm((prev) => ({ ...prev, [key]: value }))
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    setFormError(null)
    setFieldErrors({})

    if (form.password !== form.confirm_password) {
      setFieldErrors({ confirm_password: t('register.mismatch') })
      return
    }

    setSubmitting(true)
    try {
      await register({
        username: form.username,
        email: form.email,
        password: form.password,
        confirm_password: form.confirm_password,
        display_name: form.display_name || undefined,
      })
      navigate('/chat', { replace: true })
    } catch (err) {
      const apiError = toApiError(err)
      if (apiError.fields && apiError.fields.length > 0) {
        setFieldErrors(Object.fromEntries(apiError.fields.map((f) => [f.field, f.message])))
      } else {
        setFormError(apiError.message)
      }
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <AuthLayout>
      <h1 className="font-display text-3xl text-ink-50">{t('register.title')}</h1>
      <p className="mt-2 text-sm text-ink-400">{t('register.subtitle')}</p>

      <form className="mt-8 space-y-4" onSubmit={handleSubmit}>
        <FormField
          label={t('register.username')}
          name="username"
          autoComplete="username"
          value={form.username}
          onChange={(e) => update('username', e.target.value)}
          error={fieldErrors.username}
          hint={!fieldErrors.username ? t('register.usernameHint') : undefined}
          required
          autoFocus
        />
        <FormField
          label={t('register.displayName')}
          name="display_name"
          value={form.display_name}
          onChange={(e) => update('display_name', e.target.value)}
          placeholder={form.username || t('register.displayNamePlaceholder')}
        />
        <FormField
          label={t('register.email')}
          name="email"
          type="email"
          autoComplete="email"
          value={form.email}
          onChange={(e) => update('email', e.target.value)}
          error={fieldErrors.email}
          required
        />
        <FormField
          label={t('register.password')}
          name="password"
          type="password"
          autoComplete="new-password"
          value={form.password}
          onChange={(e) => update('password', e.target.value)}
          error={fieldErrors.password}
          hint={!fieldErrors.password ? t('register.passwordHint') : undefined}
          required
        />
        <FormField
          label={t('register.confirmPassword')}
          name="confirm_password"
          type="password"
          autoComplete="new-password"
          value={form.confirm_password}
          onChange={(e) => update('confirm_password', e.target.value)}
          error={fieldErrors.confirm_password}
          required
        />

        {formError && (
          <p role="alert" className="rounded-lg bg-rose-500/10 px-3.5 py-2.5 text-sm text-rose-400">
            {formError}
          </p>
        )}

        <Button type="submit" className="w-full" disabled={submitting}>
          {submitting ? t('register.submitting') : t('register.submit')}
        </Button>
      </form>

      <p className="mt-6 text-center text-sm text-ink-400">
        {t('register.haveAccount')}{' '}
        <Link to="/login" className="font-medium text-signal-400 hover:text-signal-300">
          {t('register.toLogin')}
        </Link>
      </p>
    </AuthLayout>
  )
}
