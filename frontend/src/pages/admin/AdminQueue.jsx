import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { api, STATUSES, CATEGORIES, PRIORITIES } from "../../api";
import { Header, Badge, Empty } from "../../components.jsx";

const POLL_MS = 7000;

export default function AdminQueue() {
  const [tickets, setTickets] = useState(null);
  const [err, setErr] = useState("");
  const [f, setF] = useState({ status: "", category: "", priority: "" });
  const timer = useRef(null);

  const load = async () => {
    const qs = new URLSearchParams(
      Object.fromEntries(Object.entries(f).filter(([, v]) => v))
    ).toString();
    try {
      setTickets(await api.queue(qs ? `?${qs}` : ""));
    } catch (e) {
      setErr(e.message);
    }
  };

  useEffect(() => {
    load();
    timer.current = setInterval(load, POLL_MS);
    return () => clearInterval(timer.current);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [f]);

  const set = (k) => (e) => setF({ ...f, [k]: e.target.value });

  return (
    <>
      <Header title="BookLeaf" subtitle="Admin · Support Queue" />
      <div className="wrap">
        <div className="filters">
          <div>
            <label>Status</label>
            <select value={f.status} onChange={set("status")}>
              <option value="">All</option>
              {STATUSES.map((s) => <option key={s}>{s}</option>)}
            </select>
          </div>
          <div>
            <label>Category</label>
            <select value={f.category} onChange={set("category")}>
              <option value="">All</option>
              {CATEGORIES.map((c) => <option key={c}>{c}</option>)}
            </select>
          </div>
          <div>
            <label>Priority</label>
            <select value={f.priority} onChange={set("priority")}>
              <option value="">All</option>
              {PRIORITIES.map((p) => <option key={p}>{p}</option>)}
            </select>
          </div>
          <button className="btn btn-outline btn-sm" onClick={() => setF({ status: "", category: "", priority: "" })}>
            Clear
          </button>
        </div>

        {err && <div className="err">{err}</div>}
        {!tickets ? (
          <Empty>Loading queue…</Empty>
        ) : tickets.length === 0 ? (
          <Empty>No tickets match these filters.</Empty>
        ) : (
          tickets.map((t) => (
            <Link className="card ticket-item" to={`/admin/tickets/${t.id}`} key={t.id}>
              <div className="ticket-top">
                <div>
                  <div className="ticket-subj">#{t.id} · {t.subject}</div>
                  <div className="meta">
                    {t.author_name} · {t.book_title || "General / Account Level"} ·
                    {new Date(t.created_at).toLocaleString()}
                  </div>
                </div>
                <div className="badges">
                  {t.priority && <Badge kind="priority" value={t.priority} />}
                  <Badge kind="status" value={t.status} />
                </div>
              </div>
              <div className="badges" style={{ marginTop: 8 }}>
                {t.category && <span className="badge badge-cat">{t.category}</span>}
                {(t.category_overridden === 1 || t.priority_overridden === 1) && (
                  <span className="meta">· human-adjusted</span>
                )}
                {t.responses.length > 0 && <span className="meta">· {t.responses.length} reply</span>}
              </div>
            </Link>
          ))
        )}
      </div>
    </>
  );
}
