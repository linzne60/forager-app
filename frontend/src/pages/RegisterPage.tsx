import { useState } from "react"
import { Link, useNavigate } from "react-router"
import { useAuthStore } from "@/stores/authStore"
import { ApiError } from "@/libs/api"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Alert, AlertDescription } from "@/components/ui/alert"


function RegisterPage() {
    const [email, setEmail] = useState("")
    const [password, setPassword] = useState("")
    const [confirmPassword, setConfirmPassword] = useState("")
    const [displayName, setDisplayName] = useState("")
    const [error, setError] = useState<string | null>(null)

    const { register, isLoading } = useAuthStore()
    const navigate = useNavigate()

    async function handleSubmit() {
        setError(null)

        if (password !== confirmPassword) {
            setError("Passwords do not match")
            return
        }

        try {
            await register(email, password, displayName)
            navigate("/journal")
        } catch (error) {
            if (error instanceof ApiError && error.status === 409) {
                setError("Email is already in use. Please use a different email or login.")
            } else {
                setError("Something went wrong. Please try again.")
            }
        }
    }

    return (
        <div className="form-page">
            <div>
                <h1 className="heading-page">Create an account</h1>
                <p className="text-body mt-1">
                    Start building your foraging journal.
                </p>
            </div>

            <form
                onSubmit={(e) => { e.preventDefault(); void handleSubmit() }}
                className="flex flex-col gap-5"
            >
                <div className="card-inset flex flex-col gap-3">
                    <Input
                        type="text"
                        placeholder="Display name"
                        value={displayName}
                        onChange={(e) => setDisplayName(e.target.value)}
                        required
                    />
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
                    <Input
                        type="password"
                        placeholder="Confirm password"
                        value={confirmPassword}
                        onChange={(e) => setConfirmPassword(e.target.value)}
                        required
                    />
                </div>

                {error && (
                    <Alert variant="destructive">
                        <AlertDescription>{error}</AlertDescription>
                    </Alert>
                )}

                <Button type="submit" disabled={isLoading} size="lg" className="w-full">
                    {isLoading ? "Registering..." : "Create account"}
                </Button>

                <p className="form-divider">or</p>

                <div className="flex flex-col gap-2">
                    <Button asChild variant="outline" size="md" className="w-full">
                        <a href="/api/auth/oauth/google">Continue with Google</a>
                    </Button>
                </div>

                <p className="text-body text-center">
                    Already have an account?{" "}
                    <Link to="/login" className="text-link">Sign in here</Link>
                    {" "}or use as guest.
                </p>
            </form>
        </div>
    )
}

export default RegisterPage
