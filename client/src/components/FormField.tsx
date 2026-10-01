import type { InputHTMLAttributes, ReactNode } from 'react'
import { clsx } from 'clsx'

interface FormFieldProps extends InputHTMLAttributes<HTMLInputElement> {
  label: string
  error?: string
  hint?: string
  rightSlot?: ReactNode
}

export function FormField({ label, error, hint, rightSlot, id, className, ...props }: FormFieldProps) {
  const fieldId = id ?? props.name
  return (
    <label htmlFor={fieldId} className="block">
      <span className="mb-1.5 block text-sm font-medium text-ink-200">{label}</span>
      <div className="relative">
        <input
          id={fieldId}
          className={clsx(
            'w-full rounded-lg border bg-ink-900 px-3.5 py-2.5 text-ink-50 placeholder:text-ink-500',
            'transition-colors focus:outline-none',
            error ? 'border-rose-500/60 focus:border-rose-400' : 'border-ink-600 focus:border-signal-400',
            rightSlot && 'pr-10',
            className,
          )}
          {...props}
        />
        {rightSlot && <div className="absolute inset-y-0 right-2 flex items-center">{rightSlot}</div>}
      </div>
      {error ? (
        <span className="mt-1.5 block text-xs text-rose-400">{error}</span>
      ) : hint ? (
        <span className="mt-1.5 block text-xs text-ink-400">{hint}</span>
      ) : null}
    </label>
  )
}
