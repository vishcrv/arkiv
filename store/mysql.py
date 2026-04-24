"""
Arkiv data layer — MySQL backend.
Drop-in for store/sf.py. Same function names, same call shape.
"""
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
    pass  # writes commit per-call via engine.begin()


# ── helpers ──────────────────────────────────────────────────────────────────

def _row_to_book(r) -> dict:
    lending = None
    if r.borrower:
        lending = {"borrower": r.borrower, "due_date": r.due_date or ""}
    return {
        "title": r.title or "",
        "author_id": r.author_id or "",
        "pages": int(r.pages or 0),
        "year": int(r.year or 0),
        "genre": r.genre or "",
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


_BOOK_COLS = ("isbn, title, author_id, pages, year, genre, publisher, status, format, "
              "description, rating, thoughts, date_added, date_read, sale_price, "
              "sale_date, cover_url, borrower, due_date")

_BOOK_SORT_MAP = {
    "title": "b.title",
    "year": "b.year",
    "author": "a.name",
    "date_added": "b.date_added",
}


# ── books ────────────────────────────────────────────────────────────────────

def get_book(store, isbn: str) -> Optional[dict]:
    with _conn().connect() as c:
        r = c.execute(text(f"SELECT {_BOOK_COLS} FROM books WHERE isbn = :isbn"),
                      {"isbn": isbn}).first()
    return _row_to_book(r) if r else None


def put_book(store, isbn: str, book: dict) -> None:
    lending = book.get("lending")
    params = {
        "isbn": isbn,
        "title": (book.get("title") or "")[:255],
        "author_id": book.get("author_id") or "",
        "pages": book.get("pages") or 0,
        "year": book.get("year") or 0,
        "genre": book.get("genre") or "",
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
        INSERT INTO books (isbn, title, author_id, pages, year, genre, publisher,
            status, format, description, rating, thoughts, date_added, date_read,
            sale_price, sale_date, cover_url, borrower, due_date)
        VALUES (:isbn, :title, :author_id, :pages, :year, :genre, :publisher,
            :status, :format, :description, :rating, :thoughts, :date_added, :date_read,
            :sale_price, :sale_date, :cover_url, :borrower, :due_date)
        ON DUPLICATE KEY UPDATE
            title=VALUES(title), author_id=VALUES(author_id), pages=VALUES(pages),
            year=VALUES(year), genre=VALUES(genre), publisher=VALUES(publisher),
            status=VALUES(status), format=VALUES(format), description=VALUES(description),
            rating=VALUES(rating), thoughts=VALUES(thoughts), date_added=VALUES(date_added),
            date_read=VALUES(date_read), sale_price=VALUES(sale_price),
            sale_date=VALUES(sale_date), cover_url=VALUES(cover_url),
            borrower=VALUES(borrower), due_date=VALUES(due_date)
    """)
    with _conn().begin() as c:
        c.execute(sql, params)


def delete_book(store, isbn: str) -> bool:
    with _conn().begin() as c:
        res = c.execute(text("DELETE FROM books WHERE isbn = :isbn"), {"isbn": isbn})
    return res.rowcount > 0


def list_books(sort: str = "title") -> list[tuple[str, dict]]:
    order_by = _BOOK_SORT_MAP.get(sort, "b.title")
    sql = text(f"""
        SELECT {", ".join("b." + c for c in _BOOK_COLS.replace(" ", "").split(","))}
        FROM books b LEFT JOIN authors a ON b.author_id = a.author_id
        ORDER BY {order_by}
    """)
    with _conn().connect() as c:
        rows = c.execute(sql).all()
    return [(r.isbn, _row_to_book(r)) for r in rows]


# ── authors ──────────────────────────────────────────────────────────────────

def get_author(store, author_id: str) -> Optional[dict]:
    with _conn().connect() as c:
        r = c.execute(text("SELECT author_id, name, country, dob, awards FROM authors WHERE author_id = :aid"),
                      {"aid": author_id}).first()
    return _row_to_author(r) if r else None


def create_author(store, author: dict) -> str:
    author_id = f"author_{uuid.uuid4().hex[:8]}"
    params = {
        "author_id": author_id,
        "name": (author.get("name") or "")[:255],
        "country": author.get("country") or "",
        "dob": author.get("dob") or "",
        "awards": json.dumps(author.get("awards") or []),
    }
    with _conn().begin() as c:
        c.execute(text("""
            INSERT INTO authors (author_id, name, country, dob, awards)
            VALUES (:author_id, :name, :country, :dob, :awards)
        """), params)
    return author_id


def put_author(store, author_id: str, author: dict) -> None:
    params = {
        "author_id": author_id,
        "name": (author.get("name") or "")[:255],
        "country": author.get("country") or "",
        "dob": author.get("dob") or "",
        "awards": json.dumps(author.get("awards") or []),
    }
    with _conn().begin() as c:
        c.execute(text("""
            UPDATE authors SET name=:name, country=:country, dob=:dob, awards=:awards
            WHERE author_id=:author_id
        """), params)


def delete_author(store, author_id: str) -> bool:
    with _conn().begin() as c:
        res = c.execute(text("DELETE FROM authors WHERE author_id = :aid"), {"aid": author_id})
    return res.rowcount > 0


def list_authors() -> list[tuple[str, dict]]:
    with _conn().connect() as c:
        rows = c.execute(text("SELECT author_id, name, country, dob, awards FROM authors ORDER BY name")).all()
    return [(r.author_id, _row_to_author(r)) for r in rows]


def all_authors_dict() -> dict[str, dict]:
    return {aid: a for aid, a in list_authors()}


# ── wishlist ─────────────────────────────────────────────────────────────────

def _row_to_wishlist(r) -> dict:
    return {
        "title": r.title or "",
        "author_name": r.author_name or "",
        "year": int(r.year or 0),
        "genre": r.genre or "",
    }


def get_wishlist_item(store, isbn: str) -> Optional[dict]:
    with _conn().connect() as c:
        r = c.execute(text("SELECT isbn, title, author_name, year, genre FROM wishlist WHERE isbn=:isbn"),
                      {"isbn": isbn}).first()
    return _row_to_wishlist(r) if r else None


def put_wishlist_item(store, isbn: str, item: dict) -> None:
    params = {
        "isbn": isbn,
        "title": (item.get("title") or "")[:255],
        "author_name": item.get("author_name") or "",
        "year": item.get("year") or 0,
        "genre": item.get("genre") or "",
    }
    with _conn().begin() as c:
        c.execute(text("""
            INSERT INTO wishlist (isbn, title, author_name, year, genre)
            VALUES (:isbn, :title, :author_name, :year, :genre)
            ON DUPLICATE KEY UPDATE
                title=VALUES(title), author_name=VALUES(author_name),
                year=VALUES(year), genre=VALUES(genre)
        """), params)


def delete_wishlist_item(store, isbn: str) -> bool:
    with _conn().begin() as c:
        res = c.execute(text("DELETE FROM wishlist WHERE isbn=:isbn"), {"isbn": isbn})
    return res.rowcount > 0


def list_wishlist() -> list[tuple[str, dict]]:
    with _conn().connect() as c:
        rows = c.execute(text("SELECT isbn, title, author_name, year, genre FROM wishlist")).all()
    return [(r.isbn, _row_to_wishlist(r)) for r in rows]


# ── activity ─────────────────────────────────────────────────────────────────

def log_activity(store, action: str, detail: str, isbn: Optional[str] = None) -> None:
    with _conn().begin() as c:
        c.execute(text("""
            INSERT INTO activity (action, isbn, detail, timestamp)
            VALUES (:action, :isbn, :detail, :ts)
        """), {
            "action": action,
            "isbn": isbn,
            "detail": (detail or "")[:255],
            "ts": datetime.now(timezone.utc).replace(tzinfo=None),
        })


def list_activity(limit: int = 50) -> list[dict]:
    with _conn().connect() as c:
        rows = c.execute(text("""
            SELECT action, isbn, detail, timestamp
            FROM activity ORDER BY timestamp DESC LIMIT :lim
        """), {"lim": limit}).all()
    return [
        {"action": r.action, "isbn": r.isbn, "detail": r.detail,
         "timestamp": r.timestamp.isoformat() if r.timestamp else None}
        for r in rows
    ]


# ── profile ──────────────────────────────────────────────────────────────────

def get_profile(store) -> dict:
    with _conn().connect() as c:
        r = c.execute(text("SELECT username, created_at FROM profile WHERE id=1")).first()
    if not r:
        return {"username": "reader", "created_at": ""}
    return {
        "username": r.username,
        "created_at": r.created_at.isoformat() if r.created_at else "",
    }


def put_profile(store, profile: dict) -> None:
    with _conn().begin() as c:
        c.execute(text("UPDATE profile SET username=:u WHERE id=1"),
                  {"u": (profile.get("username") or "reader")[:120]})


# ── stats ────────────────────────────────────────────────────────────────────

def compute_stats(store) -> dict:
    with _conn().connect() as c:
        def scalar(sql: str) -> int:
            return c.execute(text(sql)).scalar_one()

        total = scalar("SELECT COUNT(*) FROM books")
        authors_total = scalar("SELECT COUNT(*) FROM authors")
        wishlist_total = scalar("SELECT COUNT(*) FROM wishlist")
        books_read = scalar("SELECT COUNT(*) FROM books WHERE date_read IS NOT NULL AND date_read <> ''")
        currently_reading = scalar("SELECT COUNT(*) FROM books WHERE status = 'reading'")
        books_lent = scalar("SELECT COUNT(*) FROM books WHERE status = 'lent'")
        books_available = scalar("SELECT COUNT(*) FROM books WHERE status = 'available'")
        books_sold = scalar("SELECT COUNT(*) FROM books WHERE status = 'sold'")
        reviews = scalar("SELECT COUNT(*) FROM books WHERE thoughts IS NOT NULL AND thoughts <> ''")
        pages_read = scalar("SELECT COALESCE(SUM(pages),0) FROM books WHERE date_read IS NOT NULL AND date_read <> ''")

        rows = c.execute(text("SELECT COALESCE(NULLIF(genre,''),'Unknown') AS g, COUNT(*) AS cnt FROM books GROUP BY g")).all()
        genre_breakdown = {r.g: r.cnt for r in rows}

    return {
        "books_owned": total,
        "books_read": books_read,
        "currently_reading": currently_reading,
        "pages_read": pages_read,
        "authors_in_collection": authors_total,
        "reviews_logged": reviews,
        "books_lent": books_lent,
        "books_available": books_available,
        "books_sold": books_sold,
        "wishlist_count": wishlist_total,
        "genre_breakdown": genre_breakdown,
    }