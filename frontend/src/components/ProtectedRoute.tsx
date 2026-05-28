import { Navigate } from "react-router"
import type { ReactNode } from 'react'
import { useAuthStore } from "../stores/authStore"
import LoadingSpinner from "./LoadingSpinner"


function ProtectedRoute({ children }: { children: ReactNode }) {

    const isAuthenticated = useAuthStore(state => !!state.user && !!state.accessToken)
    const isLoading = useAuthStore(state => state.isLoading)

    if (isLoading) {
        return <LoadingSpinner /> 
    } else if (!isAuthenticated) { 
        return <Navigate to="/login" replace/>
    } else {
        return (<>{children}</>)
    }
}

export default ProtectedRoute
