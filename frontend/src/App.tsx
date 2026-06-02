//import { DeliveryRegistrationPage } from "./pages/DeliveryRegistrationPage";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { RequirePermission } from "./components/RequirePermission";
import { ApplicationUserPage } from "./pages/ApplicationUserPage";
//import { DeliveryReportPage } from "./pages/DeliveryReportPage";
import { IntranetAccessPage } from "./pages/IntranetAccessPage";
import { SolutionCenterPage } from "./pages/SolutionCenterPage";
//import { PointSaleEmailPage } from "./pages/PointSaleEmailPage";
//import { DomiciliaryPage } from "./pages/DomiciliaryPage";
import { PublicRoute } from "./components/PublicRoute";
import { RequireAuth } from "./components/RequireAuth";
//import { ParameterPage } from "./pages/ParameterPage";
import { AttendancePage } from "./pages/AttendancePage";
import { AppLayout } from "./components/AppLayout";
import { ReportPage } from "./pages/ReportPage";
import { LoginPage } from "./pages/LoginPage";
import { EventPage } from "./pages/EventPage";
import { HomePage } from "./pages/HomePage";
import { RolePage } from "./pages/RolePage";

function EmptyPage({ title }: { title: string }) {
  return <h2>{title}</h2>;
}

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
            <Route path="/maestros/domiciliarios" element={<EmptyPage title="Parámetros" />} />
            <Route path="/maestros/parametros" element={<EmptyPage title="Parámetros" />} />
            <Route path="/maestros/roles" element={ <RequirePermission path="/maestros/roles"> <RolePage /> </RequirePermission> } />
            <Route path="/maestros/usuarios" element={ <RequirePermission path="/maestros/usuarios"> <ApplicationUserPage /> </RequirePermission> } />
            <Route path="/maestros/correos-pdv" element={<EmptyPage title="Parámetros" />} />
            <Route path="/eventos" element={ <RequirePermission path="/eventos"> <EventPage /> </RequirePermission> } />
            <Route path="/reportes" element={ <RequirePermission path="/reportes"> <ReportPage /> </RequirePermission> } />
            <Route path="/reporte-domicilios" element={<EmptyPage title="Parámetros" />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Route>
        </Route>
      </Routes>
    </BrowserRouter>
  );
}