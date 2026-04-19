import { Routes, Route, Navigate } from "react-router-dom"
import RequireAuth from "./components/RequireAuth"
import AdminLayout from "./layouts/AdminLayout"
import Login from "./pages/Login"
import Dashboard from "./pages/Dashboard"
import Patients from "./pages/Patients"
import PatientDetail from "./pages/PatientDetail"
import IntakeLinks from "./pages/IntakeLinks"
import Diets from "./pages/Diets"
import DietDetail from "./pages/DietDetail"
import Telegram from "./pages/Telegram"
import PublicIntake from "./pages/PublicIntake"
import NotFound from "./pages/NotFound"

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
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
        <Route path="intake-links" element={<IntakeLinks />} />
        <Route path="diets" element={<Diets />} />
        <Route path="diets/:dietId" element={<DietDetail />} />
        <Route path="telegram" element={<Telegram />} />
      </Route>
      <Route path="*" element={<NotFound />} />
    </Routes>
  )
}
