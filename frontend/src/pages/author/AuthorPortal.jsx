import { useState } from "react";
import { Header } from "../../components.jsx";
import MyBooks from "./MyBooks.jsx";
import SubmitQuery from "./SubmitQuery.jsx";
import MyTickets from "./MyTickets.jsx";

export default function AuthorPortal() {
  const [tab, setTab] = useState("books");
  // bump to make MyTickets refetch after a new ticket
  const [ticketsKey, setTicketsKey] = useState(0);

  return (
    <>
      <Header title="BookLeaf" subtitle="Author Portal" />
      <div className="wrap">
        <div className="tabs">
          <button className={`tab ${tab === "books" ? "active" : ""}`} onClick={() => setTab("books")}>
            My Books
          </button>
          <button className={`tab ${tab === "submit" ? "active" : ""}`} onClick={() => setTab("submit")}>
            Submit a Query
          </button>
          <button className={`tab ${tab === "tickets" ? "active" : ""}`} onClick={() => setTab("tickets")}>
            My Tickets
          </button>
        </div>

        {tab === "books" && <MyBooks />}
        {tab === "submit" && (
          <SubmitQuery
            onCreated={() => { setTicketsKey((k) => k + 1); setTab("tickets"); }}
          />
        )}
        {tab === "tickets" && <MyTickets refreshKey={ticketsKey} />}
      </div>
    </>
  );
}
