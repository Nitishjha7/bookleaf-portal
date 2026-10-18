import { Routes, Route, Navigate } from "react-router-dom";
import { getToken, getRole } from "./api";
import Login from "./pages/Login.jsx";
import AuthorPortal from "./pages/author/AuthorPortal.jsx";
import AdminQueue from "./pages/admin/AdminQueue.jsx";
import AdminTicket from "./pages/admin/AdminTicket.jsx";

// Route guard: requires a token and (optionally) a specific role.
function Protected({ role, children }) {
  if (!getToken()) return <Navigate to="/login" replace />;
  if (role && getRole() !== role) return <Navigate to="/" replace />;
  return children;
}

// Send a logged-in user to their portal; everyone else to login.
function Home() {
  if (!getToken()) return <Navigate to="/login" replace />;
  return <Navigate to={getRole() === "admin" ? "/admin" : "/author"} replace />;
}

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Home />} />
      <Route path="/login" element={<Login />} />
      <Route
        path="/author"
        element={<Protected role="author"><AuthorPortal /></Protected>}
      />
      <Route
        path="/admin"
        element={<Protected role="admin"><AdminQueue /></Protected>}
      />
      <Route
        path="/admin/tickets/:id"
        element={<Protected role="admin"><AdminTicket /></Protected>}
      />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
