import { useContext } from "react";
import { Navigate } from "react-router-dom";
import { AuthContext } from "../context/AuthContext";

function ProtectedRoute({ children, allowedRoles }) {
    const { token, roles } = useContext(AuthContext);

    if (!token) {
        return <Navigate to="/login" />;
    }

    // If roles restriction exists
    if (allowedRoles && !roles.some(role => allowedRoles.includes(role))) {
        return <Navigate to="/dashboard" />;
    }

    return children;
}

export default ProtectedRoute;
