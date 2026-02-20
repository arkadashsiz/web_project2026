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
            const response = await axios.post("login/", {
                identifier,
                password,
            });
            
            login(response.data.token, response.data.roles);
            navigate("/dashboard");

        } catch (error) {
            alert("Invalid credentials");
        }
    };

    return (
        <div style={{ padding: 40 }}>
            <h2>Login</h2>
            <form onSubmit={handleSubmit}>
                <input
                    placeholder="Username / Email / Phone / National ID"
                    onChange={(e) => setIdentifier(e.target.value)}
                />
                <br /><br />
                <input
                    type="password"
                    placeholder="Password"
                    onChange={(e) => setPassword(e.target.value)}
                />
                <br /><br />
                <button type="submit">Login</button>
            </form>
        </div>
    );
}

export default Login;
