import { useEffect, useState } from "react"
import { useNavigate } from "react-router"
import { Sun, Moon, Monitor, LogOut } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { api } from "@/libs/api"
import { useAuthStore } from "@/stores/authStore"
import { useAuth } from "@/hooks/useAuth"


type Theme = "light" | "dark" | "system"


function applyTheme(theme: Theme) {
    const root = document.documentElement
    if (theme === "dark") {
        root.classList.add("dark")
    } else if (theme === "light") {
        root.classList.remove("dark")
    } else {
        const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches
        root.classList.toggle("dark", prefersDark)
    }
}


function SettingsPage() {
    const { user, setUser } = useAuthStore()
    const { logout } = useAuth()
    const navigate = useNavigate()

    const [displayName, setDisplayName] = useState(user?.display_name ?? "")
    const [city, setCity] = useState(user?.default_location?.city ?? "")
    const [state, setState] = useState(user?.default_location?.state ?? "")
    const [theme, setTheme] = useState<Theme>(() => {
        return (localStorage.getItem("forager-theme") as Theme) ?? "system"
    })

    const [isSaving, setIsSaving] = useState(false)
    const [saved, setSaved] = useState(false)
    const [error, setError] = useState<string | null>(null)

    useEffect(() => {
        applyTheme(theme)
        localStorage.setItem("forager-theme", theme)
    }, [theme])

    async function handleSave() {
        setIsSaving(true)
        setError(null)

        try {
            const updated = await api.updateProfile({
                display_name: displayName,
                default_location: { city, state },
            })
            setUser(updated)
            setSaved(true)
            setTimeout(() => setSaved(false), 2000)
        } catch (e) {
            const message = e instanceof Error ? e.message : "Failed to save"
            setError(message)
        } finally {
            setIsSaving(false)
        }
    }

    async function handleLogout() {
        await logout()
        navigate("/login")
    }

    const themeOptions: { value: Theme; label: string; icon: typeof Sun }[] = [
        { value: "light", label: "Light", icon: Sun },
        { value: "dark", label: "Dark", icon: Moon },
        { value: "system", label: "System", icon: Monitor },
    ]

    return (
        <div className="form-page">
            <div>
                <h1 className="heading-page">Settings</h1>
                <p className="text-body mt-1">
                    Manage your profile and preferences.
                </p>
            </div>

            {/* profile */}
            <div className="flex flex-col gap-5">
                <div className="card-inset flex flex-col gap-3">
                    <Input
                        id="display-name"
                        placeholder="Display name"
                        value={displayName}
                        onChange={(e) => setDisplayName(e.target.value)}
                    />
                    <div className="flex gap-2">
                        <Input
                            id="city"
                            placeholder="Default city"
                            className="flex-1"
                            value={city}
                            onChange={(e) => setCity(e.target.value)}
                        />
                        <Input
                            id="state"
                            placeholder="Default state"
                            className="w-20"
                            value={state}
                            onChange={(e) => setState(e.target.value)}
                        />
                    </div>
                </div>

                {error && (
                    <p className="text-error">{error}</p>
                )}

                <Button
                    onClick={handleSave}
                    disabled={isSaving}
                    size="lg" className="w-full"
                >
                    {saved ? "Saved!" : isSaving ? "Saving..." : "Save Changes"}
                </Button>
            </div>

            <p className="form-divider">appearance</p>

            {/* appearance */}
            <div className="card-inset flex gap-2">
                {themeOptions.map(({ value, label, icon: Icon }) => (
                    <Button
                        key={value}
                        variant={theme === value ? "default" : "ghost"}
                        className="flex-1"
                        onClick={() => setTheme(value)}
                    >
                        <Icon size={16} />
                        {label}
                    </Button>
                ))}
            </div>

            <p className="form-divider">account</p>

            {/* account */}
            <Button
                variant="ghost"
                className="justify-start text-muted-foreground hover:text-destructive"
                onClick={() => void handleLogout()}
            >
                <LogOut size={16} />
                Sign out
            </Button>

            <p className="text-center text-label pt-4">
                Forager is for entertainment purposes only. Do not consume plants based on AI identification.
            </p>
        </div>
    )
}

export default SettingsPage
