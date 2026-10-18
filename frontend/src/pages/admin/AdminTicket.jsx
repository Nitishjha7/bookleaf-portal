import { useEffect, useState, useCallback } from "react";
import { useParams, Link } from "react-router-dom";
import { api, STATUSES, CATEGORIES, PRIORITIES } from "../../api";
import { Header, Badge, Empty } from "../../components.jsx";

// The admin's workbench for a single ticket: read the query, generate/edit an
// AI draft, send the reply, and manage status / category / priority / notes.
export default function AdminTicket() {
  const { id } = useParams();
  const [t, setT] = useState(null);
  const [err, setErr] = useState("");
  const [flash, setFlash] = useState("");

  const [reply, setReply] = useState("");
  const [replyFromAI, setReplyFromAI] = useState(false);
  const [draftSource, setDraftSource] = useState("");
  const [drafting, setDrafting] = useState(false);
  const [note, setNote] = useState("");

  const load = useCallback(async () => {
    try { setT(await api.ticket(id)); }
    catch (e) { setErr(e.message); }
  }, [id]);

  useEffect(() => { load(); }, [load]);

  const flashMsg = (m) => { setFlash(m); setTimeout(() => setFlash(""), 2500); };

  const genDraft = async () => {
    setDrafting(true);
    try {
      const { draft, source } = await api.aiDraft(id);
      setReply(draft);
      setReplyFromAI(true);
      setDraftSource(source);
    } catch (e) { setErr(e.message); }
    finally { setDrafting(false); }
  };

  const sendReply = async () => {
    if (!reply.trim()) return;
    try {
      await api.respond(id, reply, replyFromAI);
      setReply(""); setReplyFromAI(false); setDraftSource("");
      await load();
      flashMsg("Reply sent to the author.");
    } catch (e) { setErr(e.message); }
  };

  const changeStatus = async (e) => { await api.setStatus(id, e.target.value); await load(); flashMsg("Status updated."); };
  const changeCategory = async (e) => { await api.setCategory(id, e.target.value); await load(); flashMsg("Category overridden."); };
  const changePriority = async (e) => { await api.setPriority(id, e.target.value); await load(); flashMsg("Priority overridden."); };
  const assign = async () => { await api.assign(id); await load(); flashMsg("Assigned to you."); };
  const addNote = async () => {
    if (!note.trim()) return;
    await api.addNote(id, note); setNote(""); await load(); flashMsg("Internal note added.");
  };

  if (err) return (<><Header title="BookLeaf" subtitle="Admin" /><div className="wrap"><div className="err">{err}</div></div></>);
  if (!t) return (<><Header title="BookLeaf" subtitle="Admin" /><div className="wrap"><Empty>Loading ticket…</Empty></div></>);

  return (
    <>
      <Header title="BookLeaf" subtitle="Admin · Ticket" />
      <div className="wrap">
        <Link className="back" to="/admin">← Back to queue</Link>
        {flash && <div className="flash">{flash}</div>}

        <div className="split">
          {/* LEFT: the conversation + reply box */}
          <div>
            <div className="card">
              <div className="ticket-top">
                <div>
                  <div className="ticket-subj">#{t.id} · {t.subject}</div>
                  <div className="meta">
                    {t.author_name} ({t.author_email}) ·
                    {t.book_title ? ` ${t.book_title}` : " General / Account Level"} ·
                    {new Date(t.created_at).toLocaleString()}
                  </div>
                </div>
                <div className="badges">
                  {t.priority && <Badge kind="priority" value={t.priority} />}
                  <Badge kind="status" value={t.status} />
                </div>
              </div>

              <div className="bubble" style={{ marginTop: 12 }}>
                <div className="bubble-head">Author’s query</div>
                {t.description}
              </div>

              {t.responses.length > 0 && (
                <div className="thread">
                  {t.responses.map((r) => (
                    <div className="bubble admin" key={r.id}>
                      <div className="bubble-head">
                        {r.admin_name} · {new Date(r.created_at).toLocaleString()}
                        {r.was_ai_drafted === 1 && " · AI-assisted"}
                      </div>
                      {r.body}
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Reply composer with the AI draft */}
            <div className="card">
              <h3 style={{ marginTop: 0 }}>Reply to the author</h3>
              <button className="btn btn-outline btn-sm" onClick={genDraft} disabled={drafting}>
                {drafting ? "Drafting with AI…" : "✦ Generate AI draft"}
              </button>
              {draftSource && (
                <span className={`ai-tag ${draftSource}`} style={{ marginLeft: 10 }}>
                  {draftSource === "ai" ? "AI draft ready — edit before sending" : "AI unavailable — safe template, write manually"}
                </span>
              )}
              <textarea
                style={{ marginTop: 10 }}
                value={reply}
                onChange={(e) => { setReply(e.target.value); setReplyFromAI(false); }}
                placeholder="Write your reply, or generate an AI draft and edit it…"
              />
              <button className="btn" style={{ marginTop: 10 }} onClick={sendReply}>Send reply</button>
            </div>
          </div>

          {/* RIGHT: AI triage + management controls */}
          <div>
            <div className="card ai-box">
              <h3 style={{ marginTop: 0 }}>AI triage</h3>
              <div className="kv" style={{ marginBottom: 8 }}>
                <b>AI category</b>{t.ai_category || "—"}
                {t.category_overridden === 1 && <span className="meta"> (overridden)</span>}
              </div>
              <div className="kv" style={{ marginBottom: 8 }}>
                <b>AI priority</b>{t.ai_priority || "—"}
                {t.priority_overridden === 1 && <span className="meta"> (overridden)</span>}
              </div>
              {t.ai_classification_note && (
                <div className="meta" style={{ marginTop: 4 }}>{t.ai_classification_note}</div>
              )}
            </div>

            <div className="card">
              <h3 style={{ marginTop: 0 }}>Manage</h3>

              <label>Status</label>
              <select value={t.status} onChange={changeStatus}>
                {STATUSES.map((s) => <option key={s}>{s}</option>)}
              </select>

              <label>Category (override AI)</label>
              <select value={t.category || ""} onChange={changeCategory}>
                {CATEGORIES.map((c) => <option key={c}>{c}</option>)}
              </select>

              <label>Priority (override AI)</label>
              <select value={t.priority || ""} onChange={changePriority}>
                {PRIORITIES.map((p) => <option key={p}>{p}</option>)}
              </select>

              <label>Assignment</label>
              <div className="meta" style={{ marginBottom: 6 }}>
                {t.assigned_admin_name ? `Assigned to ${t.assigned_admin_name}` : "Unassigned"}
              </div>
              <button className="btn btn-outline btn-sm" onClick={assign}>Assign to me</button>
            </div>

            <div className="card">
              <h3 style={{ marginTop: 0 }}>Internal notes</h3>
              <div className="meta" style={{ marginBottom: 8 }}>Only visible to the ops team — never to the author.</div>
              {t.notes.map((n) => (
                <div className="note" key={n.id}>
                  <div className="bubble-head">{n.admin_name} · {new Date(n.created_at).toLocaleString()}</div>
                  {n.body}
                </div>
              ))}
              <textarea style={{ minHeight: 70, marginTop: 6 }} value={note}
                        onChange={(e) => setNote(e.target.value)} placeholder="Add an internal note…" />
              <button className="btn btn-outline btn-sm" style={{ marginTop: 8 }} onClick={addNote}>Add note</button>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
