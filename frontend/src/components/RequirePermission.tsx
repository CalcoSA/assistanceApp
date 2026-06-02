import { useAuth } from "../context/AuthContext";
import { Navigate } from "react-router-dom";

interface RequirePermissionProps {
  path: string;
  children: React.ReactNode;
}

export function RequirePermission({ path, children }: RequirePermissionProps) {
  const { hasPermission } = useAuth();

  if (!hasPermission(path)) {
    return <Navigate to="/" replace />;
  }

  return children;
}