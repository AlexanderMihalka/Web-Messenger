export function TypingDots({ label }: { label?: string }) {
  return (
    <div className="flex items-center gap-1.5 text-sm text-ink-400">
      <span className="flex items-center gap-0.5">
        {[0, 1, 2].map((i) => (
          <span
            key={i}
            className="animate-typing-dot h-1.5 w-1.5 rounded-full bg-signal-400"
            style={{ animationDelay: `${i * 0.15}s` }}
          />
        ))}
      </span>
      {label && <span>{label}</span>}
    </div>
  )
}
