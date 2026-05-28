import { useAuthStore } from "@/stores/authStore"


export function useAuth() {
    const user = useAuthStore((state) => state.user)
    const isLoading = useAuthStore((state) => state.isLoading)
    const login = useAuthStore((state) => state.login)
    const logout = useAuthStore((state) => state.logout)
    const register = useAuthStore((state) => state.register)

    return {
        user,
        isLoading,
        isAuthenticated: user !== null,
        login,
        logout,
        register,
    }
}