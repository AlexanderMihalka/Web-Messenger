import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { ArrowLeft, Ban, ShieldCheck, Trash2 } from 'lucide-react'
import { adminApi } from '../api/admin'
import { Avatar } from '../components/Avatar'
import { formatRelativeTime } from '../utils/format'

const STAT_LABELS: Record<string, string> = {
  total_users: 'Користувачів',
  online_users: 'Онлайн зараз',
  admins: 'Адміністраторів',
  blocked_users: 'Заблоковано',
  new_users_24h: 'Нових за 24г',
  total_conversations: 'Діалогів',
  total_messages: 'Повідомлень',
  messages_24h: 'Повідомлень за 24г',
  websocket_connections: 'WS-зʼєднань',
}

export function AdminPage() {
  const [tab, setTab] = useState<'users' | 'logs'>('users')

  return (
    <div className="min-h-dvh bg-ink-950 px-4 py-8">
      <div className="mx-auto max-w-5xl">
        <Link to="/chat" className="mb-6 inline-flex items-center gap-1.5 text-sm text-ink-400 hover:text-ink-100">
          <ArrowLeft size={16} /> До чатів
        </Link>
        <h1 className="font-display text-2xl text-ink-50">Адмін-панель</h1>

        <StatsGrid />

        <div className="mt-8 flex gap-1 border-b border-ink-800">
          {(['users', 'logs'] as const).map((key) => (
            <button
              key={key}
              onClick={() => setTab(key)}
              className={`px-4 py-2.5 text-sm font-medium ${tab === key ? 'border-b-2 border-signal-500 text-ink-50' : 'text-ink-500 hover:text-ink-200'}`}
            >
              {key === 'users' ? 'Користувачі' : 'Журнал подій'}
            </button>
          ))}
        </div>

        {tab === 'users' ? <UsersTable /> : <LogsTable />}
      </div>
    </div>
  )
}

function StatsGrid() {
  const { data } = useQuery({ queryKey: ['admin-stats'], queryFn: adminApi.statistics, refetchInterval: 15_000 })
  if (!data) return <div className="mt-6 h-24 animate-pulse rounded-xl2 bg-ink-900" />
  const keys: (keyof typeof data)[] = ['total_users', 'online_users', 'total_conversations', 'messages_24h', 'blocked_users', 'admins']
  return (
    <div className="mt-6 grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
      {keys.map((key) => (
        <div key={key} className="rounded-xl2 border border-ink-800 bg-ink-900 p-4">
          <p className="text-2xl font-semibold text-ink-50">{data[key]}</p>
          <p className="mt-0.5 text-xs text-ink-500">{STAT_LABELS[key]}</p>
        </div>
      ))}
    </div>
  )
}

function UsersTable() {
  const [query, setQuery] = useState('')
  const queryClient = useQueryClient()
  const usersQuery = useQuery({
    queryKey: ['admin-users', query],
    queryFn: () => adminApi.listUsers({ q: query || undefined, limit: 50 }),
  })

  const blockMutation = useMutation({
    mutationFn: ({ id, blocked }: { id: number; blocked: boolean }) => adminApi.setBlocked(id, blocked),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['admin-users'] }),
  })
  const deleteMutation = useMutation({
    mutationFn: (id: number) => adminApi.deleteUser(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['admin-users'] }),
  })

  return (
    <div className="mt-4">
      <input
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="Пошук за username, email або імʼям…"
        className="mb-3 w-full max-w-sm rounded-lg border border-ink-700 bg-ink-900 px-3.5 py-2 text-sm text-ink-50 placeholder:text-ink-500 focus:border-signal-400 focus:outline-none"
      />
      <div className="scrollbar-thin overflow-x-auto rounded-xl2 border border-ink-800">
        <table className="w-full min-w-[640px] text-left text-sm">
          <thead className="bg-ink-900 text-xs text-ink-500">
            <tr>
              <th className="px-4 py-3 font-medium">Користувач</th>
              <th className="px-4 py-3 font-medium">Email</th>
              <th className="px-4 py-3 font-medium">Роль</th>
              <th className="px-4 py-3 font-medium">Статус</th>
              <th className="px-4 py-3 font-medium">Реєстрація</th>
              <th className="px-4 py-3 font-medium" />
            </tr>
          </thead>
          <tbody className="divide-y divide-ink-800">
            {usersQuery.data?.items.map((u) => (
              <tr key={u.id} className="text-ink-100">
                <td className="flex items-center gap-2.5 px-4 py-3">
                  <Avatar name={u.display_name} id={u.id} avatarUrl={u.avatar_url} size="sm" />
                  <div className="min-w-0">
                    <p className="truncate font-medium">{u.display_name}</p>
                    <p className="truncate text-xs text-ink-500">@{u.username}</p>
                  </div>
                </td>
                <td className="px-4 py-3 text-ink-400">{u.email}</td>
                <td className="px-4 py-3">
                  {u.role === 'ADMIN' && (
                    <span className="inline-flex items-center gap-1 rounded-full bg-signal-500/15 px-2 py-0.5 text-xs text-signal-400">
                      <ShieldCheck size={12} /> admin
                    </span>
                  )}
                </td>
                <td className="px-4 py-3">
                  {u.is_blocked ? (
                    <span className="rounded-full bg-rose-500/15 px-2 py-0.5 text-xs text-rose-400">заблокований</span>
                  ) : (
                    <span className="rounded-full bg-moss-500/15 px-2 py-0.5 text-xs text-moss-400">активний</span>
                  )}
                </td>
                <td className="px-4 py-3 text-ink-500">{formatRelativeTime(u.created_at)}</td>
                <td className="px-4 py-3">
                  {u.role !== 'ADMIN' && (
                    <div className="flex items-center justify-end gap-1">
                      <button
                        onClick={() => blockMutation.mutate({ id: u.id, blocked: !u.is_blocked })}
                        className="rounded p-1.5 text-ink-400 hover:bg-ink-800 hover:text-signal-400"
                        aria-label={u.is_blocked ? 'Розблокувати' : 'Заблокувати'}
                        title={u.is_blocked ? 'Розблокувати' : 'Заблокувати'}
                      >
                        <Ban size={15} />
                      </button>
                      <button
                        onClick={() => {
                          if (window.confirm(`Видалити користувача ${u.username}? Дію не можна скасувати.`)) {
                            deleteMutation.mutate(u.id)
                          }
                        }}
                        className="rounded p-1.5 text-ink-400 hover:bg-ink-800 hover:text-rose-400"
                        aria-label="Видалити"
                        title="Видалити"
                      >
                        <Trash2 size={15} />
                      </button>
                    </div>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {usersQuery.data?.items.length === 0 && <p className="px-4 py-6 text-center text-sm text-ink-500">Нікого не знайдено</p>}
      </div>
    </div>
  )
}

function LogsTable() {
  const [level, setLevel] = useState('')
  const logsQuery = useQuery({
    queryKey: ['admin-logs', level],
    queryFn: () => adminApi.logs({ level: level || undefined, limit: 100 }),
    refetchInterval: 10_000,
  })

  return (
    <div className="mt-4">
      <select
        value={level}
        onChange={(e) => setLevel(e.target.value)}
        className="mb-3 rounded-lg border border-ink-700 bg-ink-900 px-3 py-2 text-sm text-ink-50 focus:border-signal-400 focus:outline-none"
      >
        <option value="">Усі рівні</option>
        <option value="INFO">INFO</option>
        <option value="WARNING">WARNING</option>
        <option value="ERROR">ERROR</option>
      </select>
      <div className="scrollbar-thin max-h-[480px] overflow-y-auto rounded-xl2 border border-ink-800">
        <table className="w-full min-w-[640px] text-left text-sm">
          <thead className="sticky top-0 bg-ink-900 text-xs text-ink-500">
            <tr>
              <th className="px-4 py-2.5 font-medium">Час</th>
              <th className="px-4 py-2.5 font-medium">Рівень</th>
              <th className="px-4 py-2.5 font-medium">Подія</th>
              <th className="px-4 py-2.5 font-medium">Хто</th>
              <th className="px-4 py-2.5 font-medium">Деталі</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-ink-800">
            {logsQuery.data?.items.map((log) => (
              <tr key={log.id} className="text-ink-200">
                <td className="px-4 py-2 whitespace-nowrap text-ink-500">{new Date(log.created_at).toLocaleString('uk-UA')}</td>
                <td className="px-4 py-2">
                  <span
                    className={
                      log.level === 'ERROR'
                        ? 'text-rose-400'
                        : log.level === 'WARNING'
                          ? 'text-signal-400'
                          : 'text-ink-400'
                    }
                  >
                    {log.level}
                  </span>
                </td>
                <td className="px-4 py-2 font-mono text-xs">{log.event}</td>
                <td className="px-4 py-2 text-ink-500">{log.actor_id ?? '—'}</td>
                <td className="px-4 py-2 text-ink-500">{log.message || '—'}</td>
              </tr>
            ))}
          </tbody>
        </table>
        {logsQuery.data?.items.length === 0 && <p className="px-4 py-6 text-center text-sm text-ink-500">Записів немає</p>}
      </div>
    </div>
  )
}
