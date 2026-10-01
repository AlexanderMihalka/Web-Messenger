import { Navigate, Route, Routes } from 'react-router-dom'

import { useAuth } from './hooks/useAuth'
import { useWebSocketSync } from './hooks/useWebSocketSync'
import { AdminRoute } from './routes/AdminRoute'
import { ProtectedRoute } from './routes/ProtectedRoute'
import { WebSocketProvider } from './ws/WebSocketContext'
import { TypingProvider } from './ws/TypingContext'

import { AdminPage } from './pages/AdminPage'
import { ChatPage } from './pages/ChatPage'
import { LoginPage } from './pages/LoginPage'
import { NotFoundPage } from './pages/NotFoundPage'
import { ProfilePage } from './pages/ProfilePage'
import { RegisterPage } from './pages/RegisterPage'

export default function App() {
  return (
    <WebSocketProvider>
      <TypingProvider>
        <AppRoutes />
      </TypingProvider>
    </WebSocketProvider>
  )
}

function AppRoutes() {
  // Підписує WS-події на кеш React Query протягом усієї сесії — один раз тут, вище роутів.
  useWebSocketSync()
  const { status } = useAuth()

  return (
    <Routes>
      <Route path="/login" element={status === 'authenticated' ? <Navigate to="/chat" replace /> : <LoginPage />} />
      <Route path="/register" element={status === 'authenticated' ? <Navigate to="/chat" replace /> : <RegisterPage />} />
      <Route
        path="/chat/:conversationId?"
        element={
          <ProtectedRoute>
            <ChatPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/profile"
        element={
          <ProtectedRoute>
            <ProfilePage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/admin"
        element={
          <ProtectedRoute>
            <AdminRoute>
              <AdminPage />
            </AdminRoute>
          </ProtectedRoute>
        }
      />
      <Route path="/" element={<Navigate to="/chat" replace />} />
      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  )
}
