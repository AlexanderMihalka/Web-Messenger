import { getAvatarClass, getInitials } from '../utils/format'
import { clsx } from 'clsx'
import { useI18n } from '../i18n/useI18n'

interface AvatarProps {
  name: string
  id: number
  avatarUrl?: string | null
  online?: boolean
  size?: 'sm' | 'md' | 'lg' | 'xl'
}

const SIZES: Record<NonNullable<AvatarProps['size']>, string> = {
  sm: 'h-8 w-8 text-xs',
  md: 'h-10 w-10 text-sm',
  lg: 'h-12 w-12 text-base',
  xl: 'h-20 w-20 text-2xl',
}

const DOT_SIZES: Record<NonNullable<AvatarProps['size']>, string> = {
  sm: 'h-2 w-2',
  md: 'h-2.5 w-2.5',
  lg: 'h-3 w-3',
  xl: 'h-4 w-4',
}

export function Avatar({ name, id, avatarUrl, online, size = 'md' }: AvatarProps) {
  const { t } = useI18n()
  return (
    <div className="relative shrink-0">
      {avatarUrl ? (
        <img
          src={avatarUrl}
          alt={name}
          className={clsx('rounded-full object-cover', SIZES[size])}
        />
      ) : (
        <div
          className={clsx(
            'flex items-center justify-center rounded-full font-medium',
            SIZES[size],
            getAvatarClass(id),
          )}
        >
          {getInitials(name)}
        </div>
      )}
      {online !== undefined && (
        <span
          className={clsx(
            'absolute right-0 bottom-0 rounded-full ring-2 ring-ink-900',
            DOT_SIZES[size],
            online ? 'bg-moss-500' : 'bg-ink-500',
          )}
          aria-label={online ? t('chat.online') : t('chat.offline')}
        />
      )}
    </div>
  )
}
