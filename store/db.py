import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

from .models import ActivityEntry, Author, Book, Profile, Store, WishlistItem

DATA_FILE = Path(__file__).parent.parent / "data.json"

_BOOK_DEFAULTS: dict = {
    "description": None,
    "rating": None,
    "thoughts": None,
    "format": "paperback",
    "date_added": "1970-01-01",
    "date_read": None,
    "sale_price": None,
    "sale_date": None,
}

_DEFAULT_PROFILE: Profile = {
    "username": "reader",
    "created_at": "1970-01-01T00:00:00+00:00",
}


# --- persistence ---

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def migrate(store: dict) -> Store:
    """Fill in missing keys so old data.json files don't crash."""
    store.setdefault("authors", {})
    store.setdefault("books", {})
    store.setdefault("wishlist", {})
    store.setdefault("activity", [])
    store.setdefault("profile", dict(_DEFAULT_PROFILE))

    for book in store["books"].values():
        for key, default in _BOOK_DEFAULTS.items():
            book.setdefault(key, default)

    return store  # type: ignore[return-value]


def load() -> Store:
    if not DATA_FILE.exists():
        return {
            "authors": {},
            "books": {},
            "wishlist": {},
            "activity": [],
            "profile": dict(_DEFAULT_PROFILE),
        }
    with open(DATA_FILE) as f:
        raw = json.load(f)
    return migrate(raw)


def save(store: Store) -> None:
    with open(DATA_FILE, "w") as f:
        json.dump(store, f, indent=2)


# --- activity ---

def log_activity(store: Store, action: str, detail: str, isbn: str | None = None) -> None:
    store["activity"].append({
        "action": action,
        "isbn": isbn,
        "timestamp": _now(),
        "detail": detail,
    })


# --- profile ---

def get_profile(store: Store) -> Profile:
    return store["profile"]


def put_profile(store: Store, profile: Profile) -> None:
    store["profile"] = profile


# --- authors ---

def new_author_id() -> str:
    return f"author_{uuid.uuid4().hex[:8]}"


def get_author(store: Store, author_id: str) -> Author | None:
    return store["authors"].get(author_id)


def put_author(store: Store, author_id: str, author: Author) -> None:
    store["authors"][author_id] = author


def delete_author(store: Store, author_id: str) -> bool:
    if author_id not in store["authors"]:
        return False
    del store["authors"][author_id]
    return True


# --- books ---

def get_book(store: Store, isbn: str) -> Book | None:
    return store["books"].get(isbn)


def put_book(store: Store, isbn: str, book: Book) -> None:
    store["books"][isbn] = book


def delete_book(store: Store, isbn: str) -> bool:
    if isbn not in store["books"]:
        return False
    del store["books"][isbn]
    return True


# --- wishlist ---

def get_wishlist_item(store: Store, isbn: str) -> WishlistItem | None:
    return store["wishlist"].get(isbn)


def put_wishlist_item(store: Store, isbn: str, item: WishlistItem) -> None:
    store["wishlist"][isbn] = item


def delete_wishlist_item(store: Store, isbn: str) -> bool:
    if isbn not in store["wishlist"]:
        return False
    del store["wishlist"][isbn]
    return True


# --- stats ---

def compute_stats(store: Store) -> dict:
    books = store["books"]
    authors = store["authors"]
    wishlist = store["wishlist"]

    total_books = len(books)
    total_authors = len(authors)
    wishlist_count = len(wishlist)

    books_read = sum(1 for b in books.values() if b.get("date_read"))
    currently_reading = sum(1 for b in books.values() if b.get("status") == "reading")
    pages_read = sum(b.get("pages", 0) for b in books.values() if b.get("date_read"))
    reviews_logged = sum(1 for b in books.values() if b.get("thoughts"))
    books_lent = sum(1 for b in books.values() if b.get("status") == "lent")
    books_available = sum(1 for b in books.values() if b.get("status") == "available")
    books_sold = sum(1 for b in books.values() if b.get("status") == "sold")

    genre_counts: dict[str, int] = {}
    for b in books.values():
        g = b.get("genre", "Unknown")
        genre_counts[g] = genre_counts.get(g, 0) + 1

    return {
        "books_owned": total_books,
        "books_read": books_read,
        "currently_reading": currently_reading,
        "pages_read": pages_read,
        "authors_in_collection": total_authors,
        "reviews_logged": reviews_logged,
        "books_lent": books_lent,
        "books_available": books_available,
        "books_sold": books_sold,
        "wishlist_count": wishlist_count,
        "genre_breakdown": genre_counts,
    }
