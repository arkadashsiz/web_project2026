import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import Register from "./pages/Register";
import DetectiveBoard from "./pages/DetectiveBoard";
import SergeantPanel from "./pages/SergeantPanel";
import ProtectedRoute from "./components/ProtectedRoute";

function App() {
    return (
        <Router>
            <Routes>
            <Route path="/" element={<Login />} />
                <Route path="/login" element={<Login />} />
                <Route path="/register" element={<Register />} />

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
        </Router>
    );
}

export default App;
