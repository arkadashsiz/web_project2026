import { useState } from "react";
import { useNavigate } from "react-router-dom";
import axios from "../api/axios";

function Register() {
    const navigate = useNavigate();

    const [formData, setFormData] = useState({
        username: "",
        password: "",
        email: "",
        phone_number: "",
        national_id: "",
        first_name: "",
        last_name: "",
    });

    const handleChange = (e) => {
        setFormData({
            ...formData,
            [e.target.name]: e.target.value,
        });
    };

    const handleSubmit = async (e) => {
        e.preventDefault();

        try {
            await axios.post("users/register/", formData);
            alert("Registration successful! Please login.");
            navigate("/login");
        } catch (error) {
            console.error(error.response?.data || error);
            alert("Registration failed. Check console.");
        }
    };

    return (
        <div style={{ padding: 40 }}>
            <h2>Register</h2>

            <form onSubmit={handleSubmit}>
                <input
                    name="first_name"
                    placeholder="First Name"
                    value={formData.first_name}
                    onChange={handleChange}
                />
                <br /><br />

                <input
                    name="last_name"
                    placeholder="Last Name"
                    value={formData.last_name}
                    onChange={handleChange}
                />
                <br /><br />

                <input
                    name="username"
                    placeholder="Username"
                    value={formData.username}
                    onChange={handleChange}
                />
                <br /><br />

                <input
                    name="email"
                    type="email"
                    placeholder="Email"
                    value={formData.email}
                    onChange={handleChange}
                />
                <br /><br />

                <input
                    name="phone_number"
                    placeholder="Phone Number"
                    value={formData.phone_number}
                    onChange={handleChange}
                />
                <br /><br />

                <input
                    name="national_id"
                    placeholder="National ID"
                    value={formData.national_id}
                    onChange={handleChange}
                />
                <br /><br />

                <input
                    name="password"
                    type="password"
                    placeholder="Password"
                    value={formData.password}
                    onChange={handleChange}
                />
                <br /><br />

                <button type="submit">Register</button>
            </form>

            <br />

            <button onClick={() => navigate("/login")}>
                Back to Login
            </button>
        </div>
    );
}

export default Register;
