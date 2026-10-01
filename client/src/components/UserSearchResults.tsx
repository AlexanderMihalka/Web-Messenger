import { useQuery } from '@tanstack/react-query'
import { usersApi } from '../api/users'
import { useDebouncedValue } from '../hooks/useDebouncedValue'
import { Avatar } from './Avatar'

export function UserSearchResults({ query, onPick }: { query: string; onPick: (userId: number) => void }) {
  const debounced = useDebouncedValue(query.trim(), 300)
  const { data, isFetching } = useQuery({
    queryKey: ['user-search', debounced],
    queryFn: () => usersApi.search(debounced),
    enabled: debounced.length > 0,
  })

  if (debounced.length === 0) return null

  return (
    <div className="border-b border-ink-800 py-2">
      <p className="px-4 pb-1 text-xs text-ink-500">{isFetching ? 'Шукаємо…' : 'Люди'}</p>
      {data?.length === 0 && !isFetching && (
        <p className="px-4 py-3 text-sm text-ink-500">Нікого не знайдено за «{debounced}»</p>
      )}
      {data?.map((user) => (
        <button
          key={user.id}
          onClick={() => onPick(user.id)}
          className="flex w-full items-center gap-3 px-4 py-2.5 text-left hover:bg-ink-850"
        >
          <Avatar name={user.display_name} id={user.id} avatarUrl={user.avatar_url} size="sm" />
          <div className="min-w-0">
            <p className="truncate text-sm font-medium text-ink-50">{user.display_name}</p>
            <p className="truncate text-xs text-ink-500">@{user.username}</p>
          </div>
        </button>
      ))}
    </div>
  )
}
