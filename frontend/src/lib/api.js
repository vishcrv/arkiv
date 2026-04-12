// Thin wrapper around fetch. Throws ApiError on non-2xx so callers can use try/catch.
// The backend's SF exception handlers return JSON like { detail: "...", code: "..." }
// for SalesforceMalformedRequest (400) — we surface that as the error message.

export class ApiError extends Error {
  constructor(status, payload) {
    super(payload?.detail || `HTTP ${status}`);
    this.status = status;
    this.code = payload?.code;
    this.payload = payload;
  }
}

async function request(path, opts = {}) {
  const res = await fetch(path, {
    headers: { "Content-Type": "application/json", ...(opts.headers || {}) },
    ...opts,
  });

  if (res.status === 204) return null;

  let body = null;
  try { body = await res.json(); } catch { /* non-JSON response */ }

  if (!res.ok) throw new ApiError(res.status, body);
  return body;
}

// ── books ──────────────────────────────────────────────────────────────
export const booksApi = {
  list:   (params = {}) => request(`/api/books?${new URLSearchParams(params)}`),
  get:    (isbn)        => request(`/api/books/${isbn}`),
  create: (body)        => request(`/api/books`, { method: "POST", body: JSON.stringify(body) }),
  update: (isbn, body)  => request(`/api/books/${isbn}`, { method: "PUT", body: JSON.stringify(body) }),
  remove: (isbn)        => request(`/api/books/${isbn}`, { method: "DELETE" }),
  lend:   (isbn, body)  => request(`/api/books/${isbn}/lend`, { method: "POST", body: JSON.stringify(body) }),
  return: (isbn)        => request(`/api/books/${isbn}/return`, { method: "POST" }),
};

// ── authors ────────────────────────────────────────────────────────────
export const authorsApi = {
  list:   ()         => request(`/api/authors`),
  get:    (id)       => request(`/api/authors/${id}`),
  create: (body)     => request(`/api/authors`, { method: "POST", body: JSON.stringify(body) }),
  update: (id, body) => request(`/api/authors/${id}`, { method: "PUT", body: JSON.stringify(body) }),
  remove: (id)       => request(`/api/authors/${id}`, { method: "DELETE" }),
};

// ── wishlist ───────────────────────────────────────────────────────────
export const wishlistApi = {
  list:   ()     => request(`/api/wishlist`),
  add:    (body) => request(`/api/wishlist`, { method: "POST", body: JSON.stringify(body) }),
  remove: (isbn) => request(`/api/wishlist/${isbn}`, { method: "DELETE" }),
};

// ── profile / activity / stats ─────────────────────────────────────────
export const profileApi  = {
  get:    ()     => request(`/api/profile`),
  update: (body) => request(`/api/profile`, { method: "PUT", body: JSON.stringify(body) }),
};
export const statsApi    = { get: () => request(`/api/stats`) };
export const activityApi = { get: (limit = 50) => request(`/api/activity?limit=${limit}`) };
