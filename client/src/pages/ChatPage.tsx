import { useParams } from 'react-router-dom'
import { Sidebar } from '../components/layout/Sidebar'
import { ChatWindow } from '../components/layout/ChatWindow'
import { EmptyState } from '../components/EmptyState'

export function ChatPage() {
  const { conversationId } = useParams()
  const id = conversationId ? Number(conversationId) : undefined

  // На мобільному екрані видно або список діалогів, або відкритий чат — ніколи обидва,
  // і саме тому ChatWindow монтується рівно один раз (не дублюємо WS-підписки та запити).
  return (
    <div className="flex h-dvh overflow-hidden">
      <div className={id ? 'hidden md:flex' : 'flex'}>
        <Sidebar />
      </div>
      <main className={id ? 'flex flex-1' : 'hidden flex-1 md:flex'}>
        {id ? (
          <ChatWindow key={id} conversationId={id} />
        ) : (
          <EmptyState
            title="Оберіть діалог"
            description="Виберіть існуючу розмову зліва або знайдіть людину, щоб почати нову."
          />
        )}
      </main>
    </div>
  )
}
