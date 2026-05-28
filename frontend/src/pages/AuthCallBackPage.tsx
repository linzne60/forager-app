import { useEffect } from 'react'
import { useAuthStore } from '../stores/authStore'
import { useNavigate } from 'react-router'


function AuthCallBackPage() {

    const navigate = useNavigate()
    const { setAccessToken, fetchCurrentUser } = useAuthStore()

    useEffect(() => {

        async function handleOAuthCallback() {  
            const urlParams = new URLSearchParams(window.location.hash.slice(1))
            const token = urlParams.get('token')

            if (token) {
                setAccessToken(token)
                try {
                    await fetchCurrentUser()
                    navigate('/journal')
                } catch {
                    navigate('/login')
                }               
            } else {
                navigate('/login')
            }
        }

        void handleOAuthCallback()

    }, [navigate, setAccessToken, fetchCurrentUser])
    
    return (
        <div className="flex items-center justify-center pt-20">
            <p className="text-body">Signing you in...</p>
        </div>
    )
}

export default AuthCallBackPage