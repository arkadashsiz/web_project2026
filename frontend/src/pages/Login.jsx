import { useState, useContext } from "react";
import { AuthContext } from "../context/AuthContext";
import { useNavigate } from "react-router-dom";
import axios from "../api/axios";

function Login() {
    const [identifier, setIdentifier] = useState("");
    const [password, setPassword] = useState("");

    const { login } = useContext(AuthContext);
    const navigate = useNavigate();

    const handleSubmit = async (e) => {
        e.preventDefault();

        try {
            const response = await axios.post("users/login/", {
                identifier,
                password,
            });

            const { access, refresh, roles } = response.data;

            localStorage.setItem("access", access);
            localStorage.setItem("refresh", refresh);
            localStorage.setItem("roles", JSON.stringify(roles));

            login(access, roles);

            navigate("/dashboard");

        } catch (error) {
            console.error(error.response?.data || error);
            alert("Invalid credentials");
        }
    };

    return (
        <div style={{ padding: 40 }}>
            <h2>Login</h2>

            <form onSubmit={handleSubmit}>
                <input
                    placeholder="Username / Email / National ID"
                    value={identifier}
                    onChange={(e) => setIdentifier(e.target.value)}
                />

                <br /><br />

                <input
                    type="password"
                    placeholder="Password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                />

                <br /><br />

                <button type="submit">Login</button>
            </form>

            <br />

            <button onClick={() => navigate("/register")}>
                Create Account
            </button>
        </div>
    );
}

export default Login;
