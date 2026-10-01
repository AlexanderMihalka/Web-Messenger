import type { ReactNode } from 'react'

export function EmptyState({ title, description, action }: { title: string; description: string; action?: ReactNode }) {
  return (
    <div className="flex h-full flex-col items-center justify-center gap-3 px-8 text-center">
      <svg width="56" height="56" viewBox="0 0 32 32" fill="none" className="opacity-40">
        <path
          d="M7 11a3 3 0 0 1 3-3h12a3 3 0 0 1 3 3v7a3 3 0 0 1-3 3H14l-5 4v-4a3 3 0 0 1-2-2.8Z"
          stroke="#6b7690"
          strokeWidth="1.5"
        />
      </svg>
      <p className="font-display text-xl text-ink-200">{title}</p>
      <p className="max-w-xs text-sm text-ink-500">{description}</p>
      {action}
    </div>
  )
}
