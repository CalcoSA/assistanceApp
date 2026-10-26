import { useAuth } from "../context/AuthContext";
import { Navigate } from "react-router-dom";

interface RequirePermissionProps {
  path: string;
  children: React.ReactNode;
  administrative?: boolean;
}

export function RequirePermission({ path, children, administrative = false }: RequirePermissionProps) {
  const { hasPermission, isAdministrator } = useAuth();

  if (!hasPermission(path) || (administrative && !isAdministrator)) {
    return <Navigate to="/" replace />;
  }

  return children;
}
