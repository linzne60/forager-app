import { create } from "zustand"
import { persist } from "zustand/middleware"
import type { User, AuthResponse } from "../types"
import { api } from "../libs/api"
import { getSessionId } from "../libs/session"

interface AuthState {
    // state
    user: User | null
    accessToken: string | null
    isLoading: boolean

    // actions
    login: (email: string, password: string) => Promise<void>
    register: (email: string, password: string, displayName: string) => Promise<void>
    logout: () => Promise<void>
    fetchCurrentUser: () => Promise<void>
    refreshAccessToken: () => Promise<void>
    setAccessToken: (token: string | null) => void
    setUser: (user: User) => void
    initializeAuth: () => Promise<void>
}

export const useAuthStore = create<AuthState>()(                                                                                                        
    persist(                                                                                                                                            
        (set, get) => ({                                                                                                                                
            // initial state                                                                                                                            
            user: null,                                                                                                                                 
            accessToken: null,
            isLoading: true,
            setAccessToken: (token) => set({ accessToken: token }),
            setUser: (user) => set({ user }),

            // actions
            initializeAuth: async () => {
                // if no persist token, return early
                if (!get().accessToken) {
                    set({ isLoading: false })
                    return
                }
                try {
                    await get().fetchCurrentUser()
                } catch {
                    await get().refreshAccessToken()
                }
                set({ isLoading: false })
            },

            login: async (email, password) => {
                set({ isLoading: true })
                try {
                    const data = await api.post<AuthResponse>('/auth/login', { email, password, session_id: getSessionId() })
                    set({ user: data.user, accessToken: data.access_token, isLoading: false })
                } catch (err) {
                    set({ isLoading: false })
                    throw err
                }
            },

            register: async (email, password, displayName) => {
                set({ isLoading: true })
                try {
                    const data = await api.post<AuthResponse>('/auth/register', { email, password, display_name: displayName, session_id: getSessionId() })
                    set({ user: data.user, accessToken: data.access_token, isLoading: false })
                } catch (err) {
                    set({ isLoading: false })
                    throw err
                }
            },

            logout: async () => {
                await api.post('/auth/logout').catch(() => {})
                set({ user: null, accessToken: null })
            },

            fetchCurrentUser: async () => {
                const user = await api.get<User>('/auth/me')
                set({ user })
            },

            refreshAccessToken: async () => {
                try {
                    const data = await api.post<AuthResponse>('/auth/refresh')
                    set({ accessToken: data.access_token, user: data.user })
                } catch {
                    set({ user: null, accessToken: null })
                }
            },
        }),
        {
            name: 'auth-storage',
            partialize: (state) => ({ accessToken: state.accessToken }),
        }
    )
)