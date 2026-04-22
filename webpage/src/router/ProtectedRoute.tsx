import { Navigate, useLocation } from "react-router-dom";
import { useAuthStore } from "../store/auth";

type ProtectedRouteProps = {
  children: JSX.Element;
};

export function ProtectedRoute({ children }: ProtectedRouteProps) {
  const location = useLocation();
  const token = useAuthStore((s) => s.accessToken || s.refreshToken);
  if (!token) {
    const redirect = encodeURIComponent(location.pathname);
    return <Navigate to={`/login?redirect=${redirect}`} replace />;
  }
  return children;
}
