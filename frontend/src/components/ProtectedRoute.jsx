import { useContext } from "react";
import { Navigate } from "react-router-dom";
import { AuthContext } from "../context/AuthContext";

function ProtectedRoute({ children, allowedRoles }) {
    const { access, roles } = useContext(AuthContext);

    if (!access) {
        return <Navigate to="/login" />;
    }

    if (allowedRoles && !roles.some(role => allowedRoles.includes(role))) {
        return <Navigate to="/dashboard" />;
    }

    return children;
}

export default ProtectedRoute;
