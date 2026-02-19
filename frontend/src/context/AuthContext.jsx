import { createContext, useState } from "react";

export const AuthContext = createContext();

export function AuthProvider({ children }) {
  const [roles, setRoles] = useState(
    JSON.parse(localStorage.getItem("roles")) || []
  );

  return (
    <AuthContext.Provider value={{ roles, setRoles }}>
      {children}
    </AuthContext.Provider>
  );
}
