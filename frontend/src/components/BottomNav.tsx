import { NavLink } from "react-router"
import { Home, Camera, BookOpen, CloudSun, Settings, LogIn } from "lucide-react"
import { useAuth } from "@/hooks/useAuth"


const guestTabs = [
    { to: "/", icon: Home, label: "Home" },
    { to: "/identify", icon: Camera, label: "Identify" },
    { to: "/login", icon: LogIn, label: "Sign in" },
]

const authTabs = [
    { to: "/", icon: Home, label: "Home" },
    { to: "/journal", icon: BookOpen, label: "Journal" },
    { to: "/identify", icon: Camera, label: "Identify" },
    { to: "/planning", icon: CloudSun, label: "Planning" },
    { to: "/settings", icon: Settings, label: "Settings" },
]


function BottomNav() {
    const { isAuthenticated } = useAuth()
    const tabs = isAuthenticated ? authTabs : guestTabs

    return (
        <nav className="bottom-nav">
            <div className="flex items-end justify-around px-2 pb-[env(safe-area-inset-bottom)]">
                {tabs.map((tab) => {
                    const isCenter = tab.to === "/identify"

                    return (
                        <NavLink
                            key={tab.to}
                            to={tab.to}
                            end={tab.to === "/"}
                            className={({ isActive }) =>
                                `nav-tab ${isCenter ? "-mt-5" : ""} ${
                                    isActive ? "text-primary" : "text-muted-foreground"
                                }`
                            }
                        >
                            {({ isActive }) => {
                                const Icon = tab.icon

                                if (isCenter) {
                                    return (
                                        <>
                                            <div className={`nav-tab-center ${
                                                isActive
                                                    ? "bg-primary text-primary-foreground"
                                                    : "bg-muted text-primary"
                                            }`}>
                                                <Icon size={26} />
                                            </div>
                                            <span className="nav-tab-label">{tab.label}</span>
                                        </>
                                    )
                                }

                                return (
                                    <>
                                        <Icon size={20} />
                                        <span className="nav-tab-label">{tab.label}</span>
                                    </>
                                )
                            }}
                        </NavLink>
                    )
                })}
            </div>
        </nav>
    )
}

export default BottomNav
