import { useContext } from "react";
import { AuthContext } from "../context/AuthContext";

export default function RoleGuard({ allowedRoles, children }) {
  const { roles } = useContext(AuthContext);

  const hasAccess = roles.some(role =>
    allowedRoles.includes(role)
  );

  return hasAccess ? children : <h3>Access Denied</h3>;
}
