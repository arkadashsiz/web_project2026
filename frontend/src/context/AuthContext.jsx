import { createContext, useState } from "react";

export const AuthContext = createContext();

export function AuthProvider({ children }) {
    // Access token from localStorage
    const [access, setAccess] = useState(localStorage.getItem("access"));

    // Roles from localStorage, safely parsed
    const [roles, setRoles] = useState(() => {
        try {
            const storedRoles = localStorage.getItem("roles");
            return storedRoles ? JSON.parse(storedRoles) : [];
        } catch (e) {
            console.warn("Failed to parse roles from localStorage:", e);
            return [];
        }
    });

    const login = (accessToken, userRoles) => {
        setAccess(accessToken);
        setRoles(userRoles);

        // Save to localStorage
        localStorage.setItem("access", accessToken);
        localStorage.setItem("roles", JSON.stringify(userRoles));
    };

    const logout = () => {
        localStorage.clear();
        setAccess(null);
        setRoles([]);
    };

    return (
        <AuthContext.Provider value={{ access, roles, login, logout }}>
            {children}
        </AuthContext.Provider>
    );
}
