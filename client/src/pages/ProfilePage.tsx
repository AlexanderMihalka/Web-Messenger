import { useRef, useState, type ChangeEvent, type FormEvent } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { ArrowLeft, Camera, ShieldOff } from 'lucide-react'
import { useAuth } from '../hooks/useAuth'
import { usersApi } from '../api/users'
import { toApiError } from '../api/client'
import { Avatar } from '../components/Avatar'
import { Button } from '../components/Button'
import { FormField } from '../components/FormField'

export function ProfilePage() {
  const { user, refreshMe } = useAuth()
  const queryClient = useQueryClient()
  const fileInputRef = useRef<HTMLInputElement>(null)

  const [displayName, setDisplayName] = useState(user?.display_name ?? '')
  const [username, setUsername] = useState(user?.username ?? '')
  const [bio, setBio] = useState(user?.bio ?? '')
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({})
  const [formMessage, setFormMessage] = useState<{ kind: 'error' | 'success'; text: string } | null>(null)

  const blockedQuery = useQuery({ queryKey: ['blocked-users'], queryFn: usersApi.listBlocked })

  const updateMutation = useMutation({
    mutationFn: usersApi.updateMe,
    onSuccess: async () => {
      await refreshMe()
      setFormMessage({ kind: 'success', text: 'Зміни збережено' })
      setFieldErrors({})
    },
    onError: (err) => {
      const apiError = toApiError(err)
      if (apiError.fields?.length) {
        setFieldErrors(Object.fromEntries(apiError.fields.map((f) => [f.field, f.message])))
      } else {
        setFormMessage({ kind: 'error', text: apiError.message })
      }
    },
  })

  const avatarMutation = useMutation({
    mutationFn: usersApi.uploadAvatar,
    onSuccess: async () => {
      await refreshMe()
    },
    onError: (err) => setFormMessage({ kind: 'error', text: toApiError(err).message }),
  })

  const unblockMutation = useMutation({
    mutationFn: usersApi.unblock,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['blocked-users'] })
      queryClient.invalidateQueries({ queryKey: ['conversations'] })
    },
  })

  function handleSubmit(event: FormEvent) {
    event.preventDefault()
    setFormMessage(null)
    updateMutation.mutate({
      display_name: displayName.trim(),
      username: username.trim(),
      bio: bio.trim() === '' ? null : bio.trim(),
    })
  }

  function handleFileChange(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0]
    if (file) avatarMutation.mutate(file)
    event.target.value = ''
  }

  if (!user) return null

  return (
    <div className="min-h-dvh bg-ink-950 px-4 py-8">
      <div className="mx-auto max-w-xl">
        <Link to="/chat" className="mb-6 inline-flex items-center gap-1.5 text-sm text-ink-400 hover:text-ink-100">
          <ArrowLeft size={16} /> До чатів
        </Link>

        <div className="rounded-xl2 border border-ink-800 bg-ink-900 p-6">
          <h1 className="font-display text-2xl text-ink-50">Профіль</h1>

          <div className="mt-6 flex items-center gap-4">
            <div className="relative">
              <Avatar name={user.display_name} id={user.id} avatarUrl={user.avatar_url} size="xl" />
              <button
                onClick={() => fileInputRef.current?.click()}
                disabled={avatarMutation.isPending}
                className="absolute right-0 bottom-0 rounded-full border-2 border-ink-900 bg-signal-500 p-1.5 text-ink-950 hover:bg-signal-400 disabled:opacity-50"
                aria-label="Змінити аватар"
              >
                <Camera size={14} />
              </button>
              <input ref={fileInputRef} type="file" accept="image/png,image/jpeg,image/webp,image/gif" className="hidden" onChange={handleFileChange} />
            </div>
            <div>
              <p className="text-sm text-ink-400">{avatarMutation.isPending ? 'Завантаження…' : 'JPEG, PNG, WEBP або GIF, до 2 МБ'}</p>
            </div>
          </div>

          <form className="mt-6 space-y-4" onSubmit={handleSubmit}>
            <FormField label="Імʼя" name="display_name" value={displayName} onChange={(e) => setDisplayName(e.target.value)} error={fieldErrors.display_name} required />
            <FormField label="Username" name="username" value={username} onChange={(e) => setUsername(e.target.value)} error={fieldErrors.username} required />
            <label className="block">
              <span className="mb-1.5 block text-sm font-medium text-ink-200">Про себе</span>
              <textarea
                value={bio}
                onChange={(e) => setBio(e.target.value)}
                rows={3}
                maxLength={500}
                placeholder="Кілька слів про себе…"
                className="w-full resize-none rounded-lg border border-ink-600 bg-ink-950 px-3.5 py-2.5 text-ink-50 placeholder:text-ink-500 focus:border-signal-400 focus:outline-none"
              />
              {fieldErrors.bio && <span className="mt-1.5 block text-xs text-rose-400">{fieldErrors.bio}</span>}
            </label>

            {formMessage && (
              <p role="status" className={`rounded-lg px-3.5 py-2.5 text-sm ${formMessage.kind === 'error' ? 'bg-rose-500/10 text-rose-400' : 'bg-moss-500/10 text-moss-400'}`}>
                {formMessage.text}
              </p>
            )}

            <Button type="submit" disabled={updateMutation.isPending}>
              {updateMutation.isPending ? 'Зберігаємо…' : 'Зберегти зміни'}
            </Button>
          </form>
        </div>

        <div className="mt-6 rounded-xl2 border border-ink-800 bg-ink-900 p-6">
          <h2 className="font-display text-lg text-ink-50">Заблоковані користувачі</h2>
          {blockedQuery.isLoading ? (
            <p className="mt-3 text-sm text-ink-500">Завантаження…</p>
          ) : blockedQuery.data?.length === 0 ? (
            <p className="mt-3 text-sm text-ink-500">Ви ще нікого не заблокували.</p>
          ) : (
            <ul className="mt-3 space-y-2">
              {blockedQuery.data?.map((blocked) => (
                <li key={blocked.id} className="flex items-center justify-between gap-3 rounded-lg border border-ink-800 px-3 py-2">
                  <div className="flex items-center gap-2.5">
                    <Avatar name={blocked.display_name} id={blocked.id} avatarUrl={blocked.avatar_url} size="sm" />
                    <span className="text-sm text-ink-100">{blocked.display_name}</span>
                  </div>
                  <Button variant="outline" size="sm" onClick={() => unblockMutation.mutate(blocked.id)}>
                    <ShieldOff size={14} /> Розблокувати
                  </Button>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </div>
  )
}
