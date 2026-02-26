import { useState, useContext } from "react";
import { AuthContext } from "../context/AuthContext";
import { useTheme } from "../context/ThemeContext";
import { useNavigate } from "react-router-dom";
import axios from "../api/axios";

function Login() {
    const [identifier, setIdentifier] = useState("");
    const [password, setPassword] = useState("");
    const { login } = useContext(AuthContext);
    const { isDark, toggleTheme } = useTheme();
    const navigate = useNavigate();

    const handleSubmit = async (e) => {
        e.preventDefault();
        try {
            const response = await axios.post("login/", { identifier, password });
            login(response.data.token, response.data.roles);
            navigate("/dashboard");
        } catch (error) {
            alert("Invalid credentials");
        }
    };

    return (
        <div className="login-wrapper">
            <div className="login-card">
                <div style={{ textAlign: "right", marginBottom: "1rem" }}>
                    <button className="theme-toggle" onClick={toggleTheme}>
                        {isDark ? "☀️ Light" : "🌙 Dark"}
                    </button>
                </div>
                <h2>🔍 Police System</h2>
                <form onSubmit={handleSubmit}>
                    <div className="form-group">
                        <label>Username / Email / Phone / National ID</label>
                        <input
                            placeholder="Enter identifier"
                            value={identifier}
                            onChange={(e) => setIdentifier(e.target.value)}
                        />
                    </div>
                    <div className="form-group">
                        <label>Password</label>
                        <input
                            type="password"
                            placeholder="Enter password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                        />
                    </div>
                    <button type="submit" className="login-btn">Login</button>
                </form>
            </div>
        </div>
    );
}

export default Login;
