import { clsx } from 'clsx'
import type { ButtonHTMLAttributes } from 'react'

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'ghost' | 'danger' | 'outline'
  size?: 'sm' | 'md'
}

export function Button({ variant = 'primary', size = 'md', className, ...props }: ButtonProps) {
  return (
    <button
      className={clsx(
        'inline-flex items-center justify-center gap-2 rounded-lg font-medium transition-colors disabled:cursor-not-allowed disabled:opacity-50',
        size === 'md' ? 'px-4 py-2.5 text-sm' : 'px-3 py-1.5 text-sm',
        variant === 'primary' && 'bg-signal-500 text-ink-950 hover:bg-signal-400',
        variant === 'outline' && 'border border-ink-600 text-ink-100 hover:border-signal-500 hover:text-signal-300',
        variant === 'ghost' && 'text-ink-300 hover:bg-ink-800 hover:text-ink-100',
        variant === 'danger' && 'bg-rose-500/15 text-rose-400 hover:bg-rose-500/25',
        className,
      )}
      {...props}
    />
  )
}
