import { createContext, useState } from "react";

export const AuthContext = createContext();

export function AuthProvider({ children }) {
    const [access, setAccess] = useState(localStorage.getItem("access"));
    const [roles, setRoles] = useState(
        JSON.parse(localStorage.getItem("roles")) || []
    );

    const login = (accessToken, userRoles) => {
        setAccess(accessToken);
        setRoles(userRoles);
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
