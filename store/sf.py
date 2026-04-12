"""
Arkiv data layer — Salesforce backend.
Drop-in for store/db.py. Same function names, same call shape.
"""
import os
from datetime import datetime, timezone
from typing import Optional

from dotenv import load_dotenv
from simple_salesforce import Salesforce
from simple_salesforce.exceptions import SalesforceResourceNotFound

load_dotenv()

_sf: Optional[Salesforce] = None


def _connect() -> Salesforce:
    global _sf
    if _sf is None:
        _sf = Salesforce(
            username=os.environ["SF_USERNAME"],
            password=os.environ["SF_PASSWORD"],
            security_token=os.environ.get("SF_TOKEN", ""),
            domain=os.environ.get("SF_DOMAIN", "login"),
        )
    return _sf


# ── load/save shims (api.py still calls these) ────────────────────────────────

def load():
    """Return the SF session — api.py passes this around as `db`."""
    return _connect()


def save(store) -> None:
    """No-op. SF writes are immediate."""
    pass


# ── field mapping ─────────────────────────────────────────────────────────────

_BOOK_FIELDS = (
    "Id, Name, ISBN__c, Author__c, Pages__c, Year__c, Genre__c, Publisher__c, "
    "Status__c, Format__c, Description__c, Rating__c, Thoughts__c, "
    "Date_Added__c, Date_Read__c, Sale_Price__c, Sale_Date__c, "
    "Borrower__c, Due_Date__c, Cover_URL__c"
)

# api.py sort param → SOQL ORDER BY clause
_BOOK_SORT_MAP = {
    "title": "Name",
    "year": "Year__c",
    "author": "Author__r.Name",
    "date_added": "Date_Added__c",
}


def _sf_to_book(rec: dict) -> dict:
    lending = None
    if rec.get("Borrower__c"):
        lending = {"borrower": rec["Borrower__c"], "due_date": rec.get("Due_Date__c") or ""}
    return {
        "title": rec.get("Name") or "",
        "author_id": rec.get("Author__c") or "",
        "pages": int(rec.get("Pages__c") or 0),
        "year": int(rec.get("Year__c") or 0),
        "genre": rec.get("Genre__c") or "",
        "publisher": rec.get("Publisher__c") or "",
        "status": rec.get("Status__c") or "available",
        "lending": lending,
        "description": rec.get("Description__c"),
        "rating": int(rec["Rating__c"]) if rec.get("Rating__c") is not None else None,
        "thoughts": rec.get("Thoughts__c"),
        "format": rec.get("Format__c") or "paperback",
        "date_added": rec.get("Date_Added__c") or "",
        "date_read": rec.get("Date_Read__c"),
        "sale_price": float(rec["Sale_Price__c"]) if rec.get("Sale_Price__c") is not None else None,
        "sale_date": rec.get("Sale_Date__c"),
        "cover_url": rec.get("Cover_URL__c"),
    }


def _book_to_sf(isbn: str, book: dict) -> dict:
    data = {
        "Name": (book.get("title") or "")[:80],
        "Author__c": book.get("author_id") or None,
        "Pages__c": book.get("pages") or None,
        "Year__c": book.get("year") or None,
        "Genre__c": book.get("genre") or None,
        "Publisher__c": book.get("publisher") or None,
        "Status__c": book.get("status") or "available",
        "Format__c": book.get("format") or "paperback",
        "Description__c": book.get("description"),
        "Rating__c": book.get("rating"),
        "Thoughts__c": book.get("thoughts"),
        "Date_Added__c": book.get("date_added") or None,
        "Date_Read__c": book.get("date_read"),
        "Sale_Price__c": book.get("sale_price"),
        "Sale_Date__c": book.get("sale_date"),
        "Cover_URL__c": book.get("cover_url"),
    }
    lending = book.get("lending")
    data["Borrower__c"] = lending["borrower"] if lending else None
    data["Due_Date__c"] = lending["due_date"] if lending else None
    return data


# ── books ─────────────────────────────────────────────────────────────────────

def get_book(store, isbn: str) -> Optional[dict]:
    sf = _connect()
    res = sf.query(f"SELECT {_BOOK_FIELDS} FROM Book__c WHERE ISBN__c = '{isbn}' LIMIT 1")
    if res["totalSize"] == 0:
        return None
    return _sf_to_book(res["records"][0])


def put_book(store, isbn: str, book: dict) -> None:
    """Upsert by ISBN External ID."""
    sf = _connect()
    data = _book_to_sf(isbn, book)
    sf.Book__c.upsert(f"ISBN__c/{isbn}", data)


def delete_book(store, isbn: str) -> bool:
    sf = _connect()
    res = sf.query(f"SELECT Id FROM Book__c WHERE ISBN__c = '{isbn}' LIMIT 1")
    if res["totalSize"] == 0:
        return False
    sf.Book__c.delete(res["records"][0]["Id"])
    return True


def list_books(sort: str = "title") -> list[tuple[str, dict]]:
    """Returns [(isbn, book_dict), ...] — used by api.py list_books endpoint.

    `sort` accepts the same keys as the api.py query param: title|year|author|date_added.
    SOQL ORDER BY is pushed down to Salesforce so we don't sort in Python.
    """
    sf = _connect()
    order_by = _BOOK_SORT_MAP.get(sort, "Name")
    res = sf.query(f"SELECT {_BOOK_FIELDS} FROM Book__c ORDER BY {order_by}")
    return [(r["ISBN__c"], _sf_to_book(r)) for r in res["records"]]


# ── authors ───────────────────────────────────────────────────────────────────

_AUTHOR_FIELDS = "Id, Name, Country__c, DOB__c, Awards__c"


def _sf_to_author(rec: dict) -> dict:
    awards_str = rec.get("Awards__c") or ""
    return {
        "name": rec.get("Name") or "",
        "country": rec.get("Country__c") or "",
        "dob": rec.get("DOB__c") or "",
        "awards": [a.strip() for a in awards_str.split(",") if a.strip()],
    }


def _author_to_sf(author: dict) -> dict:
    return {
        "Name": (author.get("name") or "")[:80],
        "Country__c": author.get("country") or None,
        "DOB__c": author.get("dob") or None,
        "Awards__c": ", ".join(author.get("awards") or []) or None,
    }


def get_author(store, author_id: str) -> Optional[dict]:
    sf = _connect()
    try:
        rec = sf.Author__c.get(author_id)
    except SalesforceResourceNotFound:
        return None
    return _sf_to_author(rec)


def create_author(store, author: dict) -> str:
    """Returns the new SF Id."""
    sf = _connect()
    res = sf.Author__c.create(_author_to_sf(author))
    return res["id"]


def put_author(store, author_id: str, author: dict) -> None:
    sf = _connect()
    sf.Author__c.update(author_id, _author_to_sf(author))


def delete_author(store, author_id: str) -> bool:
    sf = _connect()
    try:
        sf.Author__c.delete(author_id)
        return True
    except SalesforceResourceNotFound:
        return False


def list_authors() -> list[tuple[str, dict]]:
    sf = _connect()
    res = sf.query(f"SELECT {_AUTHOR_FIELDS} FROM Author__c ORDER BY Name")
    return [(r["Id"], _sf_to_author(r)) for r in res["records"]]


def all_authors_dict() -> dict[str, dict]:
    """Helper for api.py _book_out which expects a dict of authors."""
    return {aid: a for aid, a in list_authors()}


# ── wishlist ──────────────────────────────────────────────────────────────────

_WISHLIST_FIELDS = "Id, Name, ISBN__c, Author_Name__c, Year__c, Genre__c"


def _sf_to_wishlist(rec: dict) -> dict:
    return {
        "title": rec.get("Name") or "",
        "author_name": rec.get("Author_Name__c") or "",
        "year": int(rec.get("Year__c") or 0),
        "genre": rec.get("Genre__c") or "",
    }


def get_wishlist_item(store, isbn: str) -> Optional[dict]:
    sf = _connect()
    res = sf.query(f"SELECT {_WISHLIST_FIELDS} FROM Wishlist_Item__c WHERE ISBN__c = '{isbn}' LIMIT 1")
    if res["totalSize"] == 0:
        return None
    return _sf_to_wishlist(res["records"][0])


def put_wishlist_item(store, isbn: str, item: dict) -> None:
    sf = _connect()
    data = {
        "Name": (item.get("title") or "")[:80],
        "Author_Name__c": item.get("author_name") or None,
        "Year__c": item.get("year") or None,
        "Genre__c": item.get("genre") or None,
    }
    sf.Wishlist_Item__c.upsert(f"ISBN__c/{isbn}", data)


def delete_wishlist_item(store, isbn: str) -> bool:
    sf = _connect()
    res = sf.query(f"SELECT Id FROM Wishlist_Item__c WHERE ISBN__c = '{isbn}' LIMIT 1")
    if res["totalSize"] == 0:
        return False
    sf.Wishlist_Item__c.delete(res["records"][0]["Id"])
    return True


def list_wishlist() -> list[tuple[str, dict]]:
    sf = _connect()
    res = sf.query(f"SELECT {_WISHLIST_FIELDS} FROM Wishlist_Item__c")
    return [(r["ISBN__c"], _sf_to_wishlist(r)) for r in res["records"]]


# ── activity ──────────────────────────────────────────────────────────────────

def log_activity(store, action: str, detail: str, isbn: Optional[str] = None) -> None:
    sf = _connect()
    sf.Activity_Entry__c.create({
        "Action__c": action,
        "Detail__c": detail[:255],
        "ISBN__c": isbn,
        "Timestamp__c": datetime.now(timezone.utc).isoformat(),
    })


def list_activity(limit: int = 50) -> list[dict]:
    sf = _connect()
    res = sf.query(
        f"SELECT Action__c, ISBN__c, Detail__c, Timestamp__c "
        f"FROM Activity_Entry__c ORDER BY Timestamp__c DESC LIMIT {limit}"
    )
    return [
        {
            "action": r["Action__c"],
            "isbn": r.get("ISBN__c"),
            "detail": r.get("Detail__c"),
            "timestamp": r.get("Timestamp__c"),
        }
        for r in res["records"]
    ]


# ── profile (uses standard User record) ───────────────────────────────────────

def get_profile(store) -> dict:
    sf = _connect()
    user_id = sf.session_id  # not actually the user id; need a different call
    res = sf.query("SELECT Username, Name, CreatedDate, SmallPhotoUrl FROM User WHERE Username = '{0}' LIMIT 1".format(os.environ["SF_USERNAME"]))
    if res["totalSize"] == 0:
        return {"username": os.environ.get("SF_USERNAME", "reader"), "created_at": ""}
    u = res["records"][0]
    return {
        "username": u.get("Name") or u.get("Username"),
        "created_at": u.get("CreatedDate") or "",
        "photo_url": u.get("SmallPhotoUrl"),
    }


def put_profile(store, profile: dict) -> None:
    """No-op for now — User record edits need separate logic and aren't critical."""
    pass


# ── stats ─────────────────────────────────────────────────────────────────────

def compute_stats(store) -> dict:
    sf = _connect()

    def count(soql: str) -> int:
        return sf.query(soql)["totalSize"]

    total = count("SELECT Id FROM Book__c")
    authors_total = count("SELECT Id FROM Author__c")
    wishlist_total = count("SELECT Id FROM Wishlist_Item__c")
    books_read = count("SELECT Id FROM Book__c WHERE Date_Read__c != null")
    currently_reading = count("SELECT Id FROM Book__c WHERE Status__c = 'reading'")
    books_lent = count("SELECT Id FROM Book__c WHERE Status__c = 'lent'")
    books_available = count("SELECT Id FROM Book__c WHERE Status__c = 'available'")
    books_sold = count("SELECT Id FROM Book__c WHERE Status__c = 'sold'")
    # Long Text Area fields can't be filtered in SOQL — fetch + count in Python
    thoughts_res = sf.query("SELECT Thoughts__c FROM Book__c")
    reviews = sum(1 for r in thoughts_res["records"] if r.get("Thoughts__c"))

    pages_res = sf.query("SELECT Pages__c FROM Book__c WHERE Date_Read__c != null")
    pages_read = sum(int(r.get("Pages__c") or 0) for r in pages_res["records"])

    genre_res = sf.query("SELECT Genre__c, COUNT(Id) cnt FROM Book__c GROUP BY Genre__c")
    genre_breakdown = {(r["Genre__c"] or "Unknown"): r["cnt"] for r in genre_res["records"]}

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