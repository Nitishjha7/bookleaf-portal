import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { api, setSession } from "../api";

export default function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);
  const nav = useNavigate();

  const submit = async (e) => {
    e.preventDefault();
    setErr("");
    setBusy(true);
    try {
      const { access_token, role, name } = await api.login(email, password);
      setSession(access_token, role, name);
      nav(role === "admin" ? "/admin" : "/author", { replace: true });
    } catch (e) {
      setErr(e.message);
    } finally {
      setBusy(false);
    }
  };

  const fill = (em, pw) => { setEmail(em); setPassword(pw); };

  return (
    <div className="login-wrap">
      <form className="card login-card" onSubmit={submit}>
        <div className="login-head">
          <div className="leaf">❧</div>
          <h2 style={{ margin: "4px 0 0" }}>BookLeaf</h2>
          <div className="muted">Author Support &amp; Communication Portal</div>
        </div>

        <label>Email</label>
        <input value={email} onChange={(e) => setEmail(e.target.value)}
               placeholder="you@email.com" autoComplete="username" />

        <label>Password</label>
        <input type="password" value={password} onChange={(e) => setPassword(e.target.value)}
               placeholder="••••••••" autoComplete="current-password" />

        {err && <div className="err">{err}</div>}

        <button className="btn" style={{ width: "100%", marginTop: 18 }} disabled={busy}>
          {busy ? "Signing in…" : "Sign in"}
        </button>

        <div className="hint">
          <b>Demo logins</b> (click to fill in):<br />
          <a href="#" onClick={(e) => { e.preventDefault(); fill("priya.sharma@email.com", "author123"); }}>
            Author: priya.sharma@email.com / author123
          </a><br />
          <a href="#" onClick={(e) => { e.preventDefault(); fill("admin@bookleaf.com", "admin123"); }}>
            Admin: admin@bookleaf.com / admin123
          </a>
        </div>
      </form>
    </div>
  );
}
