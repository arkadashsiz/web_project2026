import { useContext } from "react";
import { AuthContext } from "../context/AuthContext";
import { Link } from "react-router-dom";

function Dashboard() {
    const { roles } = useContext(AuthContext);

    return (
        <div className="page">
            <div className="card">
                <div className="dashboard-header">
                    <h2>Dashboard</h2>
                    <p>Welcome back. Here are your assigned roles:</p>
                </div>

                <div style={{ marginBottom: "1.5rem" }}>
                    {roles.map((role, index) => (
                        <span key={index} className="role-badge">{role}</span>
                    ))}
                </div>

                <div className="nav-links">
                    {roles.includes("Detective") && (
                        <Link to="/detective" className="nav-link-btn">
                            🕵️ Detective Board
                        </Link>
                    )}
                    {roles.includes("Sergeant") && (
                        <Link to="/sergeant" className="nav-link-btn">
                            🎖️ Sergeant Panel
                        </Link>
                    )}
                </div>
            </div>
        </div>
    );
}

export default Dashboard;
