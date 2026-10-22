import { Routes, Route, Navigate } from "react-router-dom";
import { isLoggedIn, getRole } from "./api";
import Login from "./pages/Login.jsx";
import AuthorPortal from "./pages/author/AuthorPortal.jsx";
import AdminQueue from "./pages/admin/AdminQueue.jsx";
import AdminTicket from "./pages/admin/AdminTicket.jsx";

// needs a session, and a specific role if one is passed
function Protected({ role, children }) {
  if (!isLoggedIn()) return <Navigate to="/login" replace />;
  if (role && getRole() !== role) return <Navigate to="/" replace />;
  return children;
}

// logged in users go to their own portal
function Home() {
  if (!isLoggedIn()) return <Navigate to="/login" replace />;
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
