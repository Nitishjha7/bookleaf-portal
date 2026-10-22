import { useNavigate } from "react-router-dom";
import { api, clearSession, getName } from "./api";

// pill for status / priority / category
export function Badge({ kind, value }) {
  const slug = (value || "").toLowerCase().replace(/[^a-z]+/g, "-");
  return <span className={`badge badge-${kind} badge-${kind}-${slug}`}>{value}</span>;
}

export function Header({ title, subtitle, right }) {
  const nav = useNavigate();
  const logout = async () => {
    try {
      await api.logout();
    } catch {
      // the cookie is gone or the API is unreachable, either way we leave
    }
    clearSession();
    nav("/login", { replace: true });
  };
  return (
    <header className="appbar">
      <div className="appbar-brand">
        <span className="leaf">❧</span>
        <div>
          <div className="appbar-title">{title}</div>
          {subtitle && <div className="appbar-sub">{subtitle}</div>}
        </div>
      </div>
      <div className="appbar-right">
        {right}
        <span className="who">{getName()}</span>
        <button className="btn btn-ghost" onClick={logout}>Log out</button>
      </div>
    </header>
  );
}

export function Empty({ children }) {
  return <div className="empty">{children}</div>;
}

export function rupees(n) {
  if (n === null || n === undefined) return "—";
  return "₹" + Number(n).toLocaleString("en-IN");
}
