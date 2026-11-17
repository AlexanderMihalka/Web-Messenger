import { useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { LogOut, Settings, ShieldCheck } from 'lucide-react'
import { Avatar } from './Avatar'
import { useAuth } from '../hooks/useAuth'
import { useI18n } from '../i18n/useI18n'

export function UserMenu() {
  const { user, logout } = useAuth()
  const { t } = useI18n()
  const [open, setOpen] = useState(false)
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    function onClickOutside(event: MouseEvent) {
      if (ref.current && !ref.current.contains(event.target as Node)) setOpen(false)
    }
    document.addEventListener('mousedown', onClickOutside)
    return () => document.removeEventListener('mousedown', onClickOutside)
  }, [])

  if (!user) return null

  return (
    <div ref={ref} className="relative border-t border-ink-800 p-3">
      <button
        onClick={() => setOpen((v) => !v)}
        className="flex w-full items-center gap-2.5 rounded-lg px-2 py-2 text-left hover:bg-ink-850"
      >
        <Avatar name={user.display_name} id={user.id} avatarUrl={user.avatar_url} size="sm" />
        <div className="min-w-0 flex-1">
          <p className="truncate text-sm font-medium text-ink-50">{user.display_name}</p>
          <p className="truncate text-xs text-ink-500">@{user.username}</p>
        </div>
      </button>

      {open && (
        <div className="absolute bottom-full left-3 mb-2 w-52 overflow-hidden rounded-lg border border-ink-700 bg-ink-850 shadow-panel">
          <Link
            to="/profile"
            onClick={() => setOpen(false)}
            className="flex items-center gap-2.5 px-3.5 py-2.5 text-sm text-ink-100 hover:bg-ink-800"
          >
            <Settings size={16} /> {t('userMenu.profile')}
          </Link>
          {user.role === 'ADMIN' && (
            <Link
              to="/admin"
              onClick={() => setOpen(false)}
              className="flex items-center gap-2.5 px-3.5 py-2.5 text-sm text-ink-100 hover:bg-ink-800"
            >
              <ShieldCheck size={16} /> {t('userMenu.admin')}
            </Link>
          )}
          <button
            onClick={() => void logout()}
            className="flex w-full items-center gap-2.5 border-t border-ink-800 px-3.5 py-2.5 text-left text-sm text-rose-400 hover:bg-ink-800"
          >
            <LogOut size={16} /> {t('userMenu.logout')}
          </button>
        </div>
      )}
    </div>
  )
}
