import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { RequirePermission } from "./components/RequirePermission";
import { ApplicationUserPage } from "./pages/ApplicationUserPage";
import { IntranetAccessPage } from "./pages/IntranetAccessPage";
import { SolutionCenterPage } from "./pages/SolutionCenterPage";
import { PublicRoute } from "./components/PublicRoute";
import { RequireAuth } from "./components/RequireAuth";
import { AttendancePage } from "./pages/AttendancePage";
import { AppLayout } from "./components/AppLayout";
import { ParameterPage } from "./pages/ParameterPage";
import { ReportPage } from "./pages/ReportPage";
import { LoginPage } from "./pages/LoginPage";
import { EventPage } from "./pages/EventPage";
import { HomePage } from "./pages/HomePage";
import { RolePage } from "./pages/RolePage";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={ <PublicRoute> <LoginPage /> </PublicRoute> }/>
        <Route path="/intranet-access" element={<IntranetAccessPage />} />
        <Route path="/attendance/:tokenEvent" element={<AttendancePage />} />
        <Route element={<RequireAuth />}>
          <Route element={<AppLayout />}>
            <Route path="/" element={<HomePage />} />
            <Route path="/maestros/centro-soluciones" element={ <RequirePermission path="/maestros/centro-soluciones"> <SolutionCenterPage /> </RequirePermission> } />
            <Route path="/maestros/roles" element={ <RequirePermission path="/maestros/roles"> <RolePage /> </RequirePermission> } />
            <Route path="/maestros/usuarios" element={ <RequirePermission path="/maestros/usuarios"> <ApplicationUserPage /> </RequirePermission> } />
            <Route path="/maestros/parametros" element={ <RequirePermission path="/maestros/parametros"> <ParameterPage /> </RequirePermission> } />
            <Route path="/eventos" element={ <RequirePermission path="/eventos"> <EventPage /> </RequirePermission> } />
            <Route path="/reportes" element={ <RequirePermission path="/reportes"> <ReportPage /> </RequirePermission> } />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Route>
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
