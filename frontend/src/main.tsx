import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'
import { configureTokenGetter, configureRefreshHandler } from './libs/api'
import { useAuthStore } from './stores/authStore'

configureTokenGetter(() => useAuthStore.getState().accessToken)
configureRefreshHandler(() => useAuthStore.getState().refreshAccessToken())

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
