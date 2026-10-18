import { useEffect, useState } from "react";
import { api } from "../../api";
import { Badge, Empty, rupees } from "../../components.jsx";

export default function MyBooks() {
  const [books, setBooks] = useState(null);
  const [err, setErr] = useState("");

  useEffect(() => {
    api.myBooks().then(setBooks).catch((e) => setErr(e.message));
  }, []);

  if (err) return <div className="err">{err}</div>;
  if (!books) return <Empty>Loading your books…</Empty>;
  if (books.length === 0) return <Empty>No books on your account yet.</Empty>;

  return (
    <div className="grid">
      {books.map((b) => (
        <div className="card" key={b.id}>
          <div className="ticket-top">
            <h3>{b.title}</h3>
          </div>
          <div className="meta">{b.genre} · ISBN {b.isbn}</div>
          <div style={{ margin: "10px 0" }}>
            <Badge kind="status" value={b.status} />
          </div>
          <div className="row">
            <div className="kv"><b>MRP</b>{rupees(b.mrp)}</div>
            <div className="kv"><b>Copies sold</b>{b.total_copies_sold}</div>
            <div className="kv"><b>Published</b>{b.publication_date || "—"}</div>
          </div>
          <div className="row" style={{ marginTop: 10 }}>
            <div className="kv"><b>Royalty earned</b>{rupees(b.total_royalty_earned)}</div>
            <div className="kv"><b>Paid</b>{rupees(b.royalty_paid)}</div>
            <div className="kv"><b>Pending</b>{rupees(b.royalty_pending)}</div>
          </div>
          <div className="meta" style={{ marginTop: 10 }}>
            Print partner: {b.print_partner} · Last payout: {b.last_royalty_payout_date || "none yet"}
            <br />
            Available on: {(b.available_on || []).join(", ") || "not listed yet"}
          </div>
        </div>
      ))}
    </div>
  );
}
