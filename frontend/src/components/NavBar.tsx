import { Link, NavLink, useNavigate } from "react-router"
import { Leaf, Plus } from "lucide-react"
import { Button } from "@/components/ui/button"
import { useAuth } from "@/hooks/useAuth"


function NavBar() {
    const { user, logout } = useAuth()
    const navigate = useNavigate()

    async function handleLogout() {
        await logout()
        navigate("/login")
    }

    const linkClass = ({ isActive }: { isActive: boolean }) =>
        isActive ? "nav-link-active" : "nav-link"

    return (
        <>
            {/* mobile: static logo */}
            <header className="md:hidden nav-header px-5">
                <Link to="/" className="logo-text">
                    <Leaf size={22} className="text-primary" />
                    forager
                </Link>
                <Link to="/identify" className="nav-icon-button">
                    <Plus size={18} />
                </Link>
            </header>

            {/* desktop: logo + nav links */}
            <header className="hidden md:flex nav-header px-6">
                <Link to="/" className="logo-text">
                    <Leaf size={22} className="text-primary" />
                    forager
                </Link>

                <nav className="flex items-center gap-6">
                    <NavLink to="/identify" className={linkClass}>Identify</NavLink>
                    <NavLink to="/journal" className={linkClass}>Journal</NavLink>

                    {user ? (
                        <>
                            <NavLink to="/planning" className={linkClass}>Planning</NavLink>
                            <NavLink to="/settings" className={linkClass}>Settings</NavLink>
                            <Button
                                variant="ghost"
                                size="sm"
                                className="link-muted"
                                onClick={() => void handleLogout()}
                            >
                                Sign out
                            </Button>
                        </>
                    ) : (
                        <>
                            <NavLink to="/login" className={linkClass}>Sign in</NavLink>
                            <NavLink to="/register" className={linkClass}>Register</NavLink>
                        </>
                    )}
                </nav>
            </header>
        </>
    )
}

export default NavBar
