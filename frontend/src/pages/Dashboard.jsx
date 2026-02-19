import { useContext } from "react";
import { AuthContext } from "../context/AuthContext";
import { Link } from "react-router-dom";

function Dashboard() {
    const { roles, logout } = useContext(AuthContext);

    return (
        <div style={{ padding: 40 }}>
            <h2>Dashboard</h2>

            <p>Your roles:</p>
            <ul>
                {roles.map((role, index) => (
                    <li key={index}>{role}</li>
                ))}
            </ul>

            {roles.includes("Detective") && (
                <Link to="/detective">Go to Detective Board</Link>
            )}

            <br />

            {roles.includes("Sergeant") && (
                <Link to="/sergeant">Go to Sergeant Panel</Link>
            )}

            <br /><br />

            <button onClick={logout}>Logout</button>
        </div>
    );
}

export default Dashboard;
