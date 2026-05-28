import { Outlet } from "react-router"
import NavBar from "./NavBar"
import BottomNav from "./BottomNav"

function Layout() {
    return (
        <div className="min-h-screen flex flex-col">
            <NavBar />
            <main className="app-main">
                <Outlet />
            </main>
            <footer className="app-footer">
                Forager is for educational purposes only. Always verify with a qualified expert before consuming anything found in the wild.
            </footer>
            <BottomNav />
        </div>
    )
}

export default Layout
