import { useState } from "react"
import { Link, useNavigate } from "react-router"
import { useAuthStore } from "@/stores/authStore"
import { ApiError } from "@/libs/api"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Alert, AlertDescription } from "@/components/ui/alert"


function LoginPage() {
    const [email, setEmail] = useState("")
    const [password, setPassword] = useState("")
    const [error, setError] = useState<string | null>(null)

    const { login, isLoading } = useAuthStore()
    const navigate = useNavigate()

    async function handleSubmit() {
        setError(null)

        try {
            await login(email, password)
            navigate("/journal")
        } catch (error) {
            if (error instanceof ApiError && error.status === 401) {
                setError("Invalid email or password")
            } else {
                setError("Something went wrong. Please try again.")
            }
        }
    }

    return (
        <div className="form-page">
            <div>
                <h1 className="heading-page">Sign in</h1>
                <p className="text-body mt-1">
                    Welcome back to forager.
                </p>
            </div>

            <form
                onSubmit={(e) => { e.preventDefault(); void handleSubmit() }}
                className="flex flex-col gap-5"
            >
                <div className="card-inset flex flex-col gap-3">
                    <Input
                        type="email"
                        placeholder="Email"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        required
                    />
                    <Input
                        type="password"
                        placeholder="Password"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        required
                    />
                </div>

                {error && (
                    <Alert variant="destructive">
                        <AlertDescription>{error}</AlertDescription>
                    </Alert>
                )}

                <Button type="submit" disabled={isLoading} size="lg" className="w-full">
                    {isLoading ? "Signing in..." : "Sign in"}
                </Button>

                <p className="form-divider">or</p>

                <div className="flex flex-col gap-2">
                    <Button asChild variant="outline" size="md" className="w-full">
                        <a href="/api/auth/oauth/google">Continue with Google</a>
                    </Button>
                </div>

                <p className="text-body text-center">
                    Don't have an account?{" "}
                    <Link to="/register" className="text-link">Register here</Link>
                    {" "}or use as guest.
                </p>
            </form>
        </div>
    )
}

export default LoginPage
