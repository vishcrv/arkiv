export class ApiError extends Error {
  constructor(status, payload) {
    super(payload?.detail || `HTTP ${status}`);
    this.status = status;
    this.code = payload?.code;
    this.payload = payload;
  }
}

function getToken() {
  return localStorage.getItem("arkiv_token");
}

const API_BASE = (import.meta.env.VITE_API_URL || "").replace(/\/$/, "");

async function request(path, opts = {}) {
  const token = getToken();
  const headers = { "Content-Type": "application/json", ...(opts.headers || {}) };
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(`${API_BASE}${path}`, { ...opts, headers });
  if (res.status === 204) return null;

  let body = null;
  try { body = await res.json(); } catch { /* non-JSON */ }

  if (!res.ok) throw new ApiError(res.status, body);
  return body;
}

// ── auth ───────────────────────────────────────────────────────────────
export const authApi = {
  register:  (body)    => request("/api/auth/register", { method: "POST", body: JSON.stringify(body) }),
  login:     (body)    => request("/api/auth/login",    { method: "POST", body: JSON.stringify(body) }),
  google:    (body)    => request("/api/auth/google",   { method: "POST", body: JSON.stringify(body) }),
  me:        ()        => request("/api/auth/me"),
};

// ── books ──────────────────────────────────────────────────────────────
export const booksApi = {
  list:   (params = {}) => request(`/api/books?${new URLSearchParams(params)}`),
  get:    (isbn)         => request(`/api/books/${isbn}`),
  create: (body)         => request("/api/books",       { method: "POST",   body: JSON.stringify(body) }),
  update: (isbn, body)   => request(`/api/books/${isbn}`, { method: "PUT",  body: JSON.stringify(body) }),
  remove: (isbn)         => request(`/api/books/${isbn}`, { method: "DELETE" }),
  lend:   (isbn, body)   => request(`/api/books/${isbn}/lend`,   { method: "POST", body: JSON.stringify(body) }),
  return: (isbn)         => request(`/api/books/${isbn}/return`, { method: "POST" }),
};

// ── authors ────────────────────────────────────────────────────────────
export const authorsApi = {
  list:   ()          => request("/api/authors"),
  get:    (id)        => request(`/api/authors/${id}`),
  create: (body)      => request("/api/authors",      { method: "POST",   body: JSON.stringify(body) }),
  update: (id, body)  => request(`/api/authors/${id}`, { method: "PUT",   body: JSON.stringify(body) }),
  remove: (id)        => request(`/api/authors/${id}`, { method: "DELETE" }),
};

// ── wishlist ───────────────────────────────────────────────────────────
export const wishlistApi = {
  list:   (params = {}) => request(`/api/wishlist?${new URLSearchParams(params)}`),
  add:    (body)         => request("/api/wishlist",      { method: "POST",   body: JSON.stringify(body) }),
  remove: (isbn)         => request(`/api/wishlist/${isbn}`, { method: "DELETE" }),
};

// ── genres ─────────────────────────────────────────────────────────────
export const genresApi = {
  list: () => request("/api/genres"),
};

// ── profile / activity / stats ─────────────────────────────────────────
export const profileApi = {
  get:    ()     => request("/api/profile"),
  update: (body) => request("/api/profile", { method: "PUT", body: JSON.stringify(body) }),
};
export const statsApi    = { get: () => request("/api/stats") };
export const activityApi = { get: (limit = 50) => request(`/api/activity?limit=${limit}`) };
