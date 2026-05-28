import { BrowserRouter, Routes, Route } from 'react-router'
import { useEffect } from 'react'

import { Toaster } from '@/components/ui/sonner'
import './App.css'
import Layout from './components/Layout'
import HomePage from './pages/HomePage'
import IdentifyPage from './pages/IdentifyPage'
import LoginPage from './pages/LoginPage'
import RegisterPage from './pages/RegisterPage'
import AuthCallbackPage from './pages/AuthCallBackPage'
import JournalPage from './pages/JournalPage'
import DiscoveryDetailPage from './pages/DiscoveryDetailPage'
import PlanningPage from './pages/PlanningPage'
import SettingsPage from './pages/SettingsPage'
import NotFoundPage from './pages/NotFoundPage'
import ProtectedRoute from './components/ProtectedRoute'
import { useAuthStore } from './stores/authStore'
import { configureTokenGetter } from './libs/api'


function App() {

  const { initializeAuth, accessToken } = useAuthStore()

  useEffect(() => {
    initializeAuth()
  }, [initializeAuth])

  useEffect(() => {
    configureTokenGetter(() => accessToken)
  }, [accessToken])

  return (
    <BrowserRouter>
      <Toaster position="top-center" richColors />
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<HomePage />} />
          <Route path="identify" element={<IdentifyPage />} />
          <Route path="login" element={<LoginPage />} />
          <Route path="register" element={<RegisterPage />} />
          <Route path="auth/callback" element={<AuthCallbackPage />} />
          <Route path="journal" element={<ProtectedRoute><JournalPage /></ProtectedRoute>} />
          <Route path="discovery/:id" element={<DiscoveryDetailPage />} />
          <Route path="planning" element={<ProtectedRoute><PlanningPage /></ProtectedRoute>} />
          <Route path="settings" element={<ProtectedRoute><SettingsPage /></ProtectedRoute>} />
          <Route path="*" element={<NotFoundPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}

export default App
