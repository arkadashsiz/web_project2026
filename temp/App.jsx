import { BrowserRouter as Router, Routes, Route, useLocation } from "react-router-dom";
import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import DetectiveBoard from "./pages/DetectiveBoard";
import SergeantPanel from "./pages/SergeantPanel";
import ProtectedRoute from "./components/ProtectedRoute";
import Navbar from "./components/Navbar";

function Layout() {
    const location = useLocation();
    const hideNav = location.pathname === "/login";

    return (
        <>
            {!hideNav && <Navbar />}
            <Routes>
                <Route path="/login" element={<Login />} />
                <Route
                    path="/dashboard"
                    element={
                        <ProtectedRoute>
                            <Dashboard />
                        </ProtectedRoute>
                    }
                />
                <Route
                    path="/detective"
                    element={
                        <ProtectedRoute allowedRoles={["Detective"]}>
                            <DetectiveBoard />
                        </ProtectedRoute>
                    }
                />
                <Route
                    path="/sergeant"
                    element={
                        <ProtectedRoute allowedRoles={["Sergeant"]}>
                            <SergeantPanel />
                        </ProtectedRoute>
                    }
                />
            </Routes>
        </>
    );
}

function App() {
    return (
        <Router>
            <Layout />
        </Router>
    );
}

export default App;
