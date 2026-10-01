import { Link } from 'react-router-dom'
import { Button } from '../components/Button'

export function NotFoundPage() {
  return (
    <div className="flex min-h-dvh flex-col items-center justify-center gap-3 bg-ink-950 px-6 text-center">
      <p className="font-display text-5xl text-ink-50">404</p>
      <p className="text-ink-400">Такої сторінки не існує.</p>
      <Link to="/chat">
        <Button className="mt-2">На головну</Button>
      </Link>
    </div>
  )
}
