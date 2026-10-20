// fetch wrapper: adds the token, throws an Error with the backend's `detail` on non-2xx

const BASE = import.meta.env.VITE_API_BASE || "";

export function getToken() {
  return localStorage.getItem("bl_token");
}
export function setSession(token, role, name) {
  localStorage.setItem("bl_token", token);
  localStorage.setItem("bl_role", role);
  localStorage.setItem("bl_name", name);
}
export function clearSession() {
  localStorage.removeItem("bl_token");
  localStorage.removeItem("bl_role");
  localStorage.removeItem("bl_name");
}
export function getRole() {
  return localStorage.getItem("bl_role");
}
export function getName() {
  return localStorage.getItem("bl_name");
}

async function request(method, path, body, { form = false } = {}) {
  const headers = {};
  const token = getToken();
  if (token) headers["Authorization"] = `Bearer ${token}`;

  let payload;
  if (form) {
    headers["Content-Type"] = "application/x-www-form-urlencoded";
    payload = new URLSearchParams(body).toString();
  } else if (body !== undefined) {
    headers["Content-Type"] = "application/json";
    payload = JSON.stringify(body);
  }

  const res = await fetch(BASE + path, { method, headers, body: payload });
  const text = await res.text();
  const data = text ? JSON.parse(text) : null;

  if (!res.ok) {
    if (res.status === 401) clearSession();
    let msg = data?.detail || `Request failed (${res.status})`;
    if (res.status === 422 && Array.isArray(data?.errors)) {
      // show which field failed, e.g. "subject: String should have at least 3 characters"
      msg = data.errors.map((e) => `${e.loc[e.loc.length - 1]}: ${e.msg}`).join("; ");
    }
    throw new Error(typeof msg === "string" ? msg : "Request failed");
  }
  return data;
}

export const api = {
  login: (email, password) =>
    request("POST", "/api/auth/login", { username: email, password }, { form: true }),

  myBooks: () => request("GET", "/api/me/books"),
  myTickets: () => request("GET", "/api/me/tickets"),
  myTicket: (id) => request("GET", `/api/me/tickets/${id}`),
  createTicket: (payload) => request("POST", "/api/me/tickets", payload),

  queue: (qs = "") => request("GET", `/api/admin/tickets${qs}`),
  ticket: (id) => request("GET", `/api/admin/tickets/${id}`),
  aiDraft: (id) => request("POST", `/api/admin/tickets/${id}/ai-draft`),
  respond: (id, body, wasAiDrafted) =>
    request("POST", `/api/admin/tickets/${id}/responses`, { body, was_ai_drafted: wasAiDrafted }),
  setStatus: (id, status) => request("PATCH", `/api/admin/tickets/${id}/status`, { status }),
  setCategory: (id, category) => request("PATCH", `/api/admin/tickets/${id}/category`, { category }),
  setPriority: (id, priority) => request("PATCH", `/api/admin/tickets/${id}/priority`, { priority }),
  addNote: (id, body) => request("POST", `/api/admin/tickets/${id}/notes`, { body }),
  assign: (id) => request("POST", `/api/admin/tickets/${id}/assign`),
};

export const CATEGORIES = [
  "Royalty & Payments",
  "ISBN & Metadata Issues",
  "Printing & Quality",
  "Distribution & Availability",
  "Book Status & Production Updates",
  "General Inquiry",
];
export const PRIORITIES = ["Critical", "High", "Medium", "Low"];
export const STATUSES = ["Open", "In Progress", "Resolved", "Closed"];
