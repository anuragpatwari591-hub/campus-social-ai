/* ============================================================
   Thin fetch wrapper around the FastAPI backend.
   The JWT is kept in localStorage (fine for a B.Tech demo) and
   attached to every request automatically.
   ============================================================ */

const API_BASE = window.location.origin.includes(":8000")
  ? window.location.origin
  : "http://localhost:8000";

const Auth = {
  getToken() { return localStorage.getItem("token"); },
  setSession(token, user) {
    localStorage.setItem("token", token);
    localStorage.setItem("user", JSON.stringify(user));
  },
  getUser() {
    try { return JSON.parse(localStorage.getItem("user")); } catch { return null; }
  },
  logout() {
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    window.location.href = "/login.html";
  },
  isLoggedIn() { return !!this.getToken(); },
  requireLogin() {
    if (!this.isLoggedIn()) window.location.href = "/login.html";
  },
};

async function api(path, { method = "GET", body, headers = {}, isForm = false } = {}) {
  const opts = { method, headers: { ...headers } };
  const token = Auth.getToken();
  if (token) opts.headers["Authorization"] = `Bearer ${token}`;

  if (body !== undefined) {
    if (isForm) {
      opts.body = body;
    } else {
      opts.headers["Content-Type"] = "application/json";
      opts.body = JSON.stringify(body);
    }
  }

  const res = await fetch(`${API_BASE}${path}`, opts);
  let data = null;
  const text = await res.text();
  try { data = text ? JSON.parse(text) : null; } catch { data = text; }

  if (!res.ok) {
    const message = (data && (data.detail || data.message)) || `Request failed (${res.status})`;
    const err = new Error(typeof message === "string" ? message : JSON.stringify(message));
    err.status = res.status;
    err.data = data;
    throw err;
  }
  return data;
}

function showToast(message) {
  const el = document.createElement("div");
  el.className = "toast";
  el.textContent = message;
  document.body.appendChild(el);
  setTimeout(() => el.remove(), 2800);
}

function timeAgo(iso) {
  const utcIso = iso.endsWith("Z") ? iso : iso + "Z";
  const diff = (Date.now() - new Date(utcIso).getTime()) / 1000;
  if (diff < 60) return "just now";
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
  return `${Math.floor(diff / 86400)}d ago`;
}

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str ?? "";
  return div.innerHTML;
}

function initials(name) {
  return (name || "?").trim().split(/\s+/).map(w => w[0]).slice(0, 2).join("").toUpperCase();
}
