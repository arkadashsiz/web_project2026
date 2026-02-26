import { useContext } from "react";
import { useTheme } from "../context/ThemeContext";
import { AuthContext } from "../context/AuthContext";
import { useNavigate } from "react-router-dom";

function Navbar() {
    const { isDark, toggleTheme } = useTheme();
    const { token, logout } = useContext(AuthContext);
    const navigate = useNavigate();

    return (
        <nav className="navbar">
            <span className="navbar-brand" onClick={() => navigate("/dashboard")}>
                🔍 Police System
            </span>
            <div className="navbar-actions">
                <button className="theme-toggle" onClick={toggleTheme} title="Toggle theme">
                    {isDark ? "☀️ Light" : "🌙 Dark"}
                </button>
                {token && (
                    <button className="logout-btn" onClick={() => { logout(); navigate("/login"); }}>
                        Logout
                    </button>
                )}
            </div>
        </nav>
    );
}

export default Navbar;
