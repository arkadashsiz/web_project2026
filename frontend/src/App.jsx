import { Navigate, Route, Routes } from 'react-router-dom'
import Layout from './components/Layout'
import ProtectedRoute from './components/ProtectedRoute'
import HomePage from './pages/HomePage'
import LoginPage from './pages/LoginPage'
import RegisterPage from './pages/RegisterPage'
import DashboardPage from './pages/DashboardPage'
import CasesPage from './pages/CasesPage'
import EvidencePage from './pages/EvidencePage'
import BoardPage from './pages/BoardPage'
import HighAlertPage from './pages/HighAlertPage'
import ReportsPage from './pages/ReportsPage'
import AdminRBACPage from './pages/AdminRBACPage'
import RewardsPage from './pages/RewardsPage'
import JudiciaryPage from './pages/JudiciaryPage'
import PaymentsPage from './pages/PaymentsPage'

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route path="/" element={<Layout><HomePage /></Layout>} />
      <Route path="/dashboard" element={<ProtectedRoute><Layout><DashboardPage /></Layout></ProtectedRoute>} />
      <Route path="/cases" element={<ProtectedRoute><Layout><CasesPage /></Layout></ProtectedRoute>} />
      <Route path="/evidence" element={<ProtectedRoute><Layout><EvidencePage /></Layout></ProtectedRoute>} />
      <Route path="/board" element={<ProtectedRoute><Layout><BoardPage /></Layout></ProtectedRoute>} />
      <Route path="/high-alert" element={<ProtectedRoute><Layout><HighAlertPage /></Layout></ProtectedRoute>} />
      <Route path="/reports" element={<ProtectedRoute><Layout><ReportsPage /></Layout></ProtectedRoute>} />
      <Route path="/rewards" element={<ProtectedRoute><Layout><RewardsPage /></Layout></ProtectedRoute>} />
      <Route path="/judiciary" element={<ProtectedRoute><Layout><JudiciaryPage /></Layout></ProtectedRoute>} />
      <Route path="/payments" element={<ProtectedRoute><Layout><PaymentsPage /></Layout></ProtectedRoute>} />
      <Route path="/admin-rbac" element={<ProtectedRoute><Layout><AdminRBACPage /></Layout></ProtectedRoute>} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
