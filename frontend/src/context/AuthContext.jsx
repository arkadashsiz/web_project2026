import { createContext, useState } from "react";

export const AuthContext = createContext();

export function AuthProvider({ children }) {
    const [token, setToken] = useState(localStorage.getItem("token"));
    const [roles, setRoles] = useState(
        JSON.parse(localStorage.getItem("roles")) || []
    );

    const login = (token, roles) => {
        localStorage.setItem("token", token);
        localStorage.setItem("roles", JSON.stringify(roles));
        setToken(token);
        setRoles(roles);
    };

    const logout = () => {
        localStorage.clear();
        setToken(null);
        setRoles([]);
    };

    return (
        <AuthContext.Provider value={{ token, roles, login, logout }}>
            {children}
        </AuthContext.Provider>
    );
}
