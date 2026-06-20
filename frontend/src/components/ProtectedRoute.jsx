import { Navigate } from "react-router-dom";

function ProtectedRoute({ currentUser, children }) {
  if (!currentUser) return <Navigate to="/login" replace />;
  return children;
}

export default ProtectedRoute;
