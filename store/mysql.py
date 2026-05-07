"""Arkiv data layer — MySQL backend (multi-user)."""
import json
import os
import uuid
from datetime import datetime, timezone
from typing import Optional

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

load_dotenv()

_engine: Optional[Engine] = None


def _conn() -> Engine:
    global _engine
    if _engine is None:
        url = os.environ["MYSQL_URL"]
        _engine = create_engine(url, pool_pre_ping=True, future=True)
    return _engine


# ── load/save shims ──────────────────────────────────────────────────────────

def load():
    return _conn()


def save(store) -> None:
    pass


# ── helpers ──────────────────────────────────────────────────────────────────

def _parse_genres(raw) -> list[str]:
    if not raw:
        return []
    return [g.strip() for g in raw.split(",") if g.strip()]


def _row_to_book(r) -> dict:
    lending = None
    if r.borrower:
        lending = {"borrower": r.borrower, "due_date": r.due_date or ""}
    return {
        "title": r.title or "",
        "author_id": r.author_id or "",
        "pages": int(r.pages or 0),
        "year": int(r.year or 0),
        "genres": _parse_genres(getattr(r, "genres", None)),
        "publisher": r.publisher or "",
        "status": r.status or "available",
        "lending": lending,
        "description": r.description,
        "rating": int(r.rating) if r.rating is not None else None,
        "thoughts": r.thoughts,
        "format": r.format or "paperback",
        "date_added": r.date_added or "",
        "date_read": r.date_read,
        "sale_price": float(r.sale_price) if r.sale_price is not None else None,
        "sale_date": r.sale_date,
        "cover_url": r.cover_url,
    }


def _row_to_author(r) -> dict:
    awards = r.awards
    if isinstance(awards, str):
        try:
            awards = json.loads(awards)
        except Exception:
            awards = []
    return {
        "name": r.name or "",
        "country": r.country or "",
        "dob": r.dob or "",
        "awards": awards or [],
    }


_BOOK_SORT_MAP = {
    "title":      "b.title ASC",
    "title-desc": "b.title DESC",
    "year":       "b.year ASC",
    "author":     "a.name ASC",
    "date_added": "b.date_added DESC",
    "rating":     "b.rating DESC",
}

_BOOK_SELECT = """
    SELECT b.isbn, b.title, b.author_id, b.pages, b.year, b.publisher, b.status,
           b.format, b.description, b.rating, b.thoughts, b.date_added, b.date_read,
           b.sale_price, b.sale_date, b.cover_url, b.borrower, b.due_date,
           GROUP_CONCAT(g.name ORDER BY g.name SEPARATOR ',') AS genres
    FROM books b
    LEFT JOIN authors a ON b.author_id = a.author_id
    LEFT JOIN book_genres bg ON b.isbn = bg.isbn AND b.user_id = bg.user_id
    LEFT JOIN genres g ON bg.genre_id = g.genre_id
"""


def _ensure_genres(c, genre_names: list[str]) -> list[int]:
    """Insert genres that don't exist; return their IDs."""
    if not genre_names:
        return []
    for name in genre_names:
        c.execute(text("INSERT IGNORE INTO genres (name) VALUES (:n)"), {"n": name})
    placeholders = ", ".join(f":g{i}" for i in range(len(genre_names)))
    params = {f"g{i}": name for i, name in enumerate(genre_names)}
    rows = c.execute(text(f"SELECT genre_id FROM genres WHERE name IN ({placeholders})"), params).all()
    return [r.genre_id for r in rows]


def _set_book_genres(c, isbn: str, user_id: str, genre_names: list[str]) -> None:
    c.execute(text("DELETE FROM book_genres WHERE isbn=:isbn AND user_id=:uid"),
              {"isbn": isbn, "uid": user_id})
    for gid in _ensure_genres(c, genre_names):
        c.execute(text("INSERT IGNORE INTO book_genres (isbn, user_id, genre_id) VALUES (:isbn, :uid, :gid)"),
                  {"isbn": isbn, "uid": user_id, "gid": gid})


def _set_wishlist_genres(c, isbn: str, user_id: str, genre_names: list[str]) -> None:
    c.execute(text("DELETE FROM wishlist_genres WHERE isbn=:isbn AND user_id=:uid"),
              {"isbn": isbn, "uid": user_id})
    for gid in _ensure_genres(c, genre_names):
        c.execute(text("INSERT IGNORE INTO wishlist_genres (isbn, user_id, genre_id) VALUES (:isbn, :uid, :gid)"),
                  {"isbn": isbn, "uid": user_id, "gid": gid})


# ── users ─────────────────────────────────────────────────────────────────────

def _row_to_user(r, include_hash: bool = False) -> dict:
    d = {
        "user_id": r.user_id,
        "email": r.email,
        "username": r.username,
        "google_id": r.google_id,
        "theme": r.theme,
        "created_at": r.created_at.isoformat() if r.created_at else "",
    }
    if include_hash:
        d["password_hash"] = r.password_hash
    return d


def get_user_by_id(user_id: str) -> Optional[dict]:
    with _conn().connect() as c:
        r = c.execute(text(
            "SELECT user_id, email, username, google_id, theme, created_at FROM users WHERE user_id=:uid"
        ), {"uid": user_id}).first()
    return _row_to_user(r) if r else None


def get_user_by_email(email: str) -> Optional[dict]:
    with _conn().connect() as c:
        r = c.execute(text(
            "SELECT user_id, email, username, password_hash, google_id, theme, created_at FROM users WHERE email=:email"
        ), {"email": email}).first()
    return _row_to_user(r, include_hash=True) if r else None


def get_user_by_google_id(google_id: str) -> Optional[dict]:
    with _conn().connect() as c:
        r = c.execute(text(
            "SELECT user_id, email, username, google_id, theme, created_at FROM users WHERE google_id=:gid"
        ), {"gid": google_id}).first()
    return _row_to_user(r) if r else None


def create_user(email: str, username: str,
                password_hash: Optional[str] = None,
                google_id: Optional[str] = None) -> str:
    user_id = str(uuid.uuid4())
    with _conn().begin() as c:
        c.execute(text("""
            INSERT INTO users (user_id, email, username, password_hash, google_id)
            VALUES (:uid, :email, :username, :phash, :gid)
        """), {"uid": user_id, "email": email, "username": username,
               "phash": password_hash, "gid": google_id})
    return user_id


def put_user(user_id: str, updates: dict) -> None:
    allowed = {"username", "theme", "google_id"}
    fields = [f"{k}=:{k}" for k in updates if k in allowed]
    if not fields:
        return
    params = {k: v for k, v in updates.items() if k in allowed}
    params["uid"] = user_id
    with _conn().begin() as c:
        c.execute(text(f"UPDATE users SET {', '.join(fields)} WHERE user_id=:uid"), params)


# ── books ────────────────────────────────────────────────────────────────────

def get_book(store, isbn: str, user_id: str) -> Optional[dict]:
    sql = text(f"""
        {_BOOK_SELECT}
        WHERE b.isbn=:isbn AND b.user_id=:uid
        GROUP BY b.isbn, b.user_id
    """)
    with _conn().connect() as c:
        r = c.execute(sql, {"isbn": isbn, "uid": user_id}).first()
    return _row_to_book(r) if r else None


def put_book(store, isbn: str, book: dict, user_id: str) -> None:
    lending = book.get("lending")
    params = {
        "isbn": isbn,
        "user_id": user_id,
        "title": (book.get("title") or "")[:255],
        "author_id": book.get("author_id") or "",
        "pages": book.get("pages") or 0,
        "year": book.get("year") or 0,
        "publisher": book.get("publisher") or "",
        "status": book.get("status") or "available",
        "format": book.get("format") or "paperback",
        "description": book.get("description"),
        "rating": book.get("rating"),
        "thoughts": book.get("thoughts"),
        "date_added": book.get("date_added") or "",
        "date_read": book.get("date_read"),
        "sale_price": book.get("sale_price"),
        "sale_date": book.get("sale_date"),
        "cover_url": book.get("cover_url"),
        "borrower": lending["borrower"] if lending else None,
        "due_date": lending["due_date"] if lending else None,
    }
    sql = text("""
        INSERT INTO books (isbn, user_id, title, author_id, pages, year, publisher,
            status, format, description, rating, thoughts, date_added, date_read,
            sale_price, sale_date, cover_url, borrower, due_date)
        VALUES (:isbn, :user_id, :title, :author_id, :pages, :year, :publisher,
            :status, :format, :description, :rating, :thoughts, :date_added, :date_read,
            :sale_price, :sale_date, :cover_url, :borrower, :due_date)
        ON DUPLICATE KEY UPDATE
            title=VALUES(title), author_id=VALUES(author_id), pages=VALUES(pages),
            year=VALUES(year), publisher=VALUES(publisher), status=VALUES(status),
            format=VALUES(format), description=VALUES(description), rating=VALUES(rating),
            thoughts=VALUES(thoughts), date_added=VALUES(date_added), date_read=VALUES(date_read),
            sale_price=VALUES(sale_price), sale_date=VALUES(sale_date), cover_url=VALUES(cover_url),
            borrower=VALUES(borrower), due_date=VALUES(due_date)
    """)
    with _conn().begin() as c:
        c.execute(sql, params)
        _set_book_genres(c, isbn, user_id, book.get("genres") or [])


def delete_book(store, isbn: str, user_id: str) -> bool:
    with _conn().begin() as c:
        res = c.execute(text("DELETE FROM books WHERE isbn=:isbn AND user_id=:uid"),
                        {"isbn": isbn, "uid": user_id})
    return res.rowcount > 0


def list_books(user_id: str, sort: str = "title", status: Optional[str] = None,
               genres: Optional[list[str]] = None, q: Optional[str] = None,
               after: Optional[str] = None, before: Optional[str] = None) -> list[tuple[str, dict]]:
    order_by = _BOOK_SORT_MAP.get(sort, "b.title ASC")
    conditions = ["b.user_id = :uid"]
    params: dict = {"uid": user_id}

    if status:
        conditions.append("b.status = :status")
        params["status"] = status
    if q:
        conditions.append("(b.title LIKE :q OR a.name LIKE :q)")
        params["q"] = f"%{q}%"
    if after:
        conditions.append("b.date_added >= :after")
        params["after"] = after
    if before:
        conditions.append("b.date_added <= :before")
        params["before"] = before
    if genres:
        for i, g in enumerate(genres):
            conditions.append(f"""EXISTS (
                SELECT 1 FROM book_genres bg{i}
                JOIN genres gg{i} ON bg{i}.genre_id = gg{i}.genre_id
                WHERE bg{i}.isbn = b.isbn AND bg{i}.user_id = b.user_id AND gg{i}.name = :genre{i}
            )""")
            params[f"genre{i}"] = g

    where = " AND ".join(conditions)
    sql = text(f"""
        SELECT b.isbn, b.title, b.author_id, b.pages, b.year, b.publisher, b.status,
               b.format, b.description, b.rating, b.thoughts, b.date_added, b.date_read,
               b.sale_price, b.sale_date, b.cover_url, b.borrower, b.due_date,
               GROUP_CONCAT(g.name ORDER BY g.name SEPARATOR ',') AS genres
        FROM books b
        LEFT JOIN authors a ON b.author_id = a.author_id
        LEFT JOIN book_genres bg ON b.isbn = bg.isbn AND b.user_id = bg.user_id
        LEFT JOIN genres g ON bg.genre_id = g.genre_id
        WHERE {where}
        GROUP BY b.isbn, b.user_id
        ORDER BY {order_by}
    """)
    with _conn().connect() as c:
        rows = c.execute(sql, params).all()
    return [(r.isbn, _row_to_book(r)) for r in rows]


# ── genres ────────────────────────────────────────────────────────────────────

def list_genres() -> list[dict]:
    with _conn().connect() as c:
        rows = c.execute(text("SELECT genre_id, name FROM genres ORDER BY name")).all()
    return [{"genre_id": r.genre_id, "name": r.name} for r in rows]


# ── authors ──────────────────────────────────────────────────────────────────

def get_author(store, author_id: str, user_id: str) -> Optional[dict]:
    with _conn().connect() as c:
        r = c.execute(text(
            "SELECT author_id, name, country, dob, awards FROM authors WHERE author_id=:aid AND user_id=:uid"
        ), {"aid": author_id, "uid": user_id}).first()
    return _row_to_author(r) if r else None


def create_author(store, author: dict, user_id: str) -> str:
    author_id = f"author_{uuid.uuid4().hex[:8]}"
    with _conn().begin() as c:
        c.execute(text("""
            INSERT INTO authors (author_id, user_id, name, country, dob, awards)
            VALUES (:aid, :uid, :name, :country, :dob, :awards)
        """), {
            "aid": author_id,
            "uid": user_id,
            "name": (author.get("name") or "")[:255],
            "country": author.get("country") or "",
            "dob": author.get("dob") or "",
            "awards": json.dumps(author.get("awards") or []),
        })
    return author_id


def put_author(store, author_id: str, author: dict, user_id: str) -> None:
    with _conn().begin() as c:
        c.execute(text("""
            UPDATE authors SET name=:name, country=:country, dob=:dob, awards=:awards
            WHERE author_id=:aid AND user_id=:uid
        """), {
            "aid": author_id,
            "uid": user_id,
            "name": (author.get("name") or "")[:255],
            "country": author.get("country") or "",
            "dob": author.get("dob") or "",
            "awards": json.dumps(author.get("awards") or []),
        })


def delete_author(store, author_id: str, user_id: str) -> bool:
    with _conn().begin() as c:
        res = c.execute(text("DELETE FROM authors WHERE author_id=:aid AND user_id=:uid"),
                        {"aid": author_id, "uid": user_id})
    return res.rowcount > 0


def list_authors(user_id: str) -> list[tuple[str, dict]]:
    with _conn().connect() as c:
        rows = c.execute(text(
            "SELECT author_id, name, country, dob, awards FROM authors WHERE user_id=:uid ORDER BY name"
        ), {"uid": user_id}).all()
    return [(r.author_id, _row_to_author(r)) for r in rows]


def all_authors_dict(user_id: str) -> dict[str, dict]:
    return {aid: a for aid, a in list_authors(user_id)}


# ── wishlist ─────────────────────────────────────────────────────────────────

def _row_to_wishlist(r) -> dict:
    return {
        "title": r.title or "",
        "author_name": r.author_name or "",
        "year": int(r.year or 0),
        "cover_url": getattr(r, "cover_url", None),
        "buy_url": getattr(r, "buy_url", None),
        "genres": _parse_genres(getattr(r, "genres", None)),
    }


_WISHLIST_SELECT = """
    SELECT w.isbn, w.title, w.author_name, w.year, w.cover_url, w.buy_url,
           GROUP_CONCAT(g.name ORDER BY g.name SEPARATOR ',') AS genres
    FROM wishlist w
    LEFT JOIN wishlist_genres wg ON w.isbn = wg.isbn AND w.user_id = wg.user_id
    LEFT JOIN genres g ON wg.genre_id = g.genre_id
"""

_WISHLIST_SORT_MAP = {
    "title":      "w.title ASC",
    "title-desc": "w.title DESC",
    "year":       "w.year ASC",
    "year-desc":  "w.year DESC",
}


def get_wishlist_item(store, isbn: str, user_id: str) -> Optional[dict]:
    sql = text(f"""
        {_WISHLIST_SELECT}
        WHERE w.isbn=:isbn AND w.user_id=:uid
        GROUP BY w.isbn, w.user_id
    """)
    with _conn().connect() as c:
        r = c.execute(sql, {"isbn": isbn, "uid": user_id}).first()
    return _row_to_wishlist(r) if r else None


def put_wishlist_item(store, isbn: str, item: dict, user_id: str) -> None:
    params = {
        "isbn": isbn,
        "user_id": user_id,
        "title": (item.get("title") or "")[:255],
        "author_name": item.get("author_name") or "",
        "year": item.get("year") or 0,
        "cover_url": item.get("cover_url"),
        "buy_url": item.get("buy_url"),
    }
    with _conn().begin() as c:
        c.execute(text("""
            INSERT INTO wishlist (isbn, user_id, title, author_name, year, cover_url, buy_url)
            VALUES (:isbn, :user_id, :title, :author_name, :year, :cover_url, :buy_url)
            ON DUPLICATE KEY UPDATE
                title=VALUES(title), author_name=VALUES(author_name), year=VALUES(year),
                cover_url=VALUES(cover_url), buy_url=VALUES(buy_url)
        """), params)
        _set_wishlist_genres(c, isbn, user_id, item.get("genres") or [])


def delete_wishlist_item(store, isbn: str, user_id: str) -> bool:
    with _conn().begin() as c:
        res = c.execute(text("DELETE FROM wishlist WHERE isbn=:isbn AND user_id=:uid"),
                        {"isbn": isbn, "uid": user_id})
    return res.rowcount > 0


def list_wishlist(user_id: str, sort: str = "title") -> list[tuple[str, dict]]:
    order_by = _WISHLIST_SORT_MAP.get(sort, "w.title ASC")
    sql = text(f"""
        {_WISHLIST_SELECT}
        WHERE w.user_id=:uid
        GROUP BY w.isbn, w.user_id
        ORDER BY {order_by}
    """)
    with _conn().connect() as c:
        rows = c.execute(sql, {"uid": user_id}).all()
    return [(r.isbn, _row_to_wishlist(r)) for r in rows]


# ── activity ─────────────────────────────────────────────────────────────────

def log_activity(store, action: str, detail: str, user_id: str,
                 isbn: Optional[str] = None) -> None:
    with _conn().begin() as c:
        c.execute(text("""
            INSERT INTO activity (user_id, action, isbn, detail, timestamp)
            VALUES (:uid, :action, :isbn, :detail, :ts)
        """), {
            "uid": user_id,
            "action": action,
            "isbn": isbn,
            "detail": (detail or "")[:255],
            "ts": datetime.now(timezone.utc).replace(tzinfo=None),
        })


def list_activity(user_id: str, limit: int = 50) -> list[dict]:
    with _conn().connect() as c:
        rows = c.execute(text("""
            SELECT action, isbn, detail, timestamp
            FROM activity WHERE user_id=:uid
            ORDER BY timestamp DESC LIMIT :lim
        """), {"uid": user_id, "lim": limit}).all()
    return [
        {"action": r.action, "isbn": r.isbn, "detail": r.detail,
         "timestamp": r.timestamp.isoformat() if r.timestamp else None}
        for r in rows
    ]


# ── profile ──────────────────────────────────────────────────────────────────

def get_profile(store, user_id: str) -> dict:
    user = get_user_by_id(user_id)
    if not user:
        return {"username": "reader", "email": "", "theme": "system", "created_at": ""}
    return {k: user[k] for k in ("user_id", "email", "username", "theme", "created_at")}


def put_profile(store, profile: dict, user_id: str) -> None:
    put_user(user_id, {k: v for k, v in profile.items() if k in ("username", "theme")})


# ── stats ────────────────────────────────────────────────────────────────────

def compute_stats(store, user_id: str) -> dict:
    with _conn().connect() as c:
        def scalar(sql: str, extra: Optional[dict] = None) -> int:
            p = {"uid": user_id}
            if extra:
                p.update(extra)
            return c.execute(text(sql), p).scalar_one()

        total            = scalar("SELECT COUNT(*) FROM books WHERE user_id=:uid")
        authors_total    = scalar("SELECT COUNT(*) FROM authors WHERE user_id=:uid")
        wishlist_total   = scalar("SELECT COUNT(*) FROM wishlist WHERE user_id=:uid")
        books_read       = scalar("SELECT COUNT(*) FROM books WHERE user_id=:uid AND (status='read' OR (date_read IS NOT NULL AND date_read <> ''))")
        currently_reading= scalar("SELECT COUNT(*) FROM books WHERE user_id=:uid AND status='reading'")
        books_lent       = scalar("SELECT COUNT(*) FROM books WHERE user_id=:uid AND status='lent'")
        books_available  = scalar("SELECT COUNT(*) FROM books WHERE user_id=:uid AND status='available'")
        books_sold       = scalar("SELECT COUNT(*) FROM books WHERE user_id=:uid AND status='sold'")
        reviews          = scalar("SELECT COUNT(*) FROM books WHERE user_id=:uid AND thoughts IS NOT NULL AND thoughts <> ''")
        pages_read       = scalar("SELECT COALESCE(SUM(pages),0) FROM books WHERE user_id=:uid AND (date_read IS NOT NULL AND date_read <> '')")

        rows = c.execute(text("""
            SELECT g.name AS genre_name, COUNT(*) AS cnt
            FROM book_genres bg
            JOIN genres g ON bg.genre_id = g.genre_id
            WHERE bg.user_id = :uid
            GROUP BY g.genre_id, g.name
            ORDER BY cnt DESC
        """), {"uid": user_id}).all()
        genre_breakdown = {r.genre_name: r.cnt for r in rows}

    return {
        "books_owned":          total,
        "books_read":           books_read,
        "currently_reading":    currently_reading,
        "pages_read":           pages_read,
        "authors_in_collection":authors_total,
        "reviews_logged":       reviews,
        "books_lent":           books_lent,
        "books_available":      books_available,
        "books_sold":           books_sold,
        "wishlist_count":       wishlist_total,
        "genre_breakdown":      genre_breakdown,
    }
