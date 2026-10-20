import { useEffect, useState } from "react";
import { api } from "../../api";

export default function SubmitQuery({ onCreated }) {
  const [books, setBooks] = useState([]);
  const [bookId, setBookId] = useState("");       // "" => General / Account Level
  const [subject, setSubject] = useState("");
  const [description, setDescription] = useState("");
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    api.myBooks().then(setBooks).catch(() => {});
  }, []);

  const submit = async (e) => {
    e.preventDefault();
    setErr("");
    setBusy(true);
    try {
      await api.createTicket({
        book_id: bookId ? Number(bookId) : null,
        subject,
        description,
      });
      onCreated();
    } catch (e) {
      setErr(e.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <form className="card" style={{ maxWidth: 640 }} onSubmit={submit}>
      <h3>Raise a support query</h3>
      <p className="muted" style={{ marginTop: 0 }}>
        Our team will respond here. Urgent issues (royalties, ISBN errors) are prioritised automatically.
      </p>

      <label>Which book is this about?</label>
      <select value={bookId} onChange={(e) => setBookId(e.target.value)}>
        <option value="">General / Account Level</option>
        {books.map((b) => (
          <option key={b.id} value={b.id}>{b.title}</option>
        ))}
      </select>

      <label>Subject</label>
      <input value={subject} onChange={(e) => setSubject(e.target.value)} minLength={3} maxLength={200}
             placeholder="e.g. Royalty for last quarter not received" />

      <label>Describe your query</label>
      <textarea value={description} onChange={(e) => setDescription(e.target.value)} minLength={5} maxLength={5000}
                placeholder="Give us the details so we can help quickly…" />

      <label>Attachment (optional)</label>
      <input type="file" disabled title="UI only in this version" />
      <div className="muted" style={{ fontSize: 12, marginTop: 4 }}>
        Attachment UI is shown for completeness; file upload is a planned enhancement.
      </div>

      {err && <div className="err">{err}</div>}

      <button className="btn" style={{ marginTop: 18 }} disabled={busy}>
        {busy ? "Submitting…" : "Submit query"}
      </button>
    </form>
  );
}
