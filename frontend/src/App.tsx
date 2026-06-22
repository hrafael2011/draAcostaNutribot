import { Routes, Route, Navigate } from "react-router-dom"
import RequireAuth from "./components/RequireAuth"
import AdminLayout from "./layouts/AdminLayout"
import Login from "./pages/Login"
import AdminLogin from "./pages/AdminLogin"
import ChangePassword from "./pages/ChangePassword"
import ResetPassword from "./pages/ResetPassword"
import AdminUsers from "./pages/AdminUsers"
import AdminAuditLog from "./pages/AdminAuditLog"
import Dashboard from "./pages/Dashboard"
import Patients from "./pages/Patients"
import PatientDetail from "./pages/PatientDetail"
import IntakeLinks from "./pages/IntakeLinks"
import Diets from "./pages/Diets"
import DietDetail from "./pages/DietDetail"
import DietWizard from "./pages/DietWizard"
import PublicIntake from "./pages/PublicIntake"
import NotFound from "./pages/NotFound"
import Trash from "./pages/Trash"
import PwaAutoReload from "./components/PwaAutoReload"

export default function App() {
  return (
    <>
      <PwaAutoReload />
      <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/admin" element={<AdminLogin />} />
      <Route path="/change-password" element={<ChangePassword />} />
      <Route path="/reset-password" element={<ResetPassword />} />
      <Route path="/intake/:token" element={<PublicIntake />} />
      <Route
        path="/"
        element={
          <RequireAuth>
            <AdminLayout />
          </RequireAuth>
        }
      >
        <Route index element={<Navigate to="/dashboard" replace />} />
        <Route path="dashboard" element={<Dashboard />} />
        <Route path="patients" element={<Patients />} />
        <Route path="patients/:patientId" element={<PatientDetail />} />
        <Route path="intake-links" element={<Navigate to="/formularios" replace />} />
        <Route path="formularios" element={<IntakeLinks />} />
        <Route path="diets/new" element={<DietWizard />} />
        <Route path="diets/:dietId/regenerate" element={<DietWizard />} />
        <Route path="diets" element={<Diets />} />
        <Route path="diets/:dietId" element={<DietDetail />} />
        <Route path="trash" element={<Trash />} />
        <Route path="admin/users" element={<AdminUsers />} />
        <Route path="admin/audit-log" element={<AdminAuditLog />} />
      </Route>
      <Route path="*" element={<NotFound />} />
    </Routes>
    </>
  )
}
