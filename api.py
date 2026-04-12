"""
Arkiv REST API — FastAPI
Run: uvicorn api:app --reload --port 5000
Docs: http://localhost:5000/docs
"""

from datetime import date, datetime, timezone
from typing import Optional

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from simple_salesforce.exceptions import (
    SalesforceAuthenticationFailed,
    SalesforceError,
    SalesforceMalformedRequest,
    SalesforceResourceNotFound,
)

import store.sf as store

app = FastAPI(title="Arkiv API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def _today() -> str:
    return date.today().isoformat()


def _book_out(isbn: str, book: dict, authors: dict) -> dict:
    author = authors.get(book.get("author_id", ""))
    return {"isbn": isbn, **book, "author_name": author["name"] if author else None}


# ── request bodies ──────────────────────────────────────────────────────────

class BookIn(BaseModel):
    isbn: str
    title: str
    author_id: str
    pages: int = 0
    year: int = 0
    genre: str = ""
    publisher: str = ""
    description: Optional[str] = None
    format: str = "paperback"
    cover_url: Optional[str] = None


class BookUpdate(BaseModel):
    title: Optional[str] = None
    author_id: Optional[str] = None
    pages: Optional[int] = None
    year: Optional[int] = None
    genre: Optional[str] = None
    publisher: Optional[str] = None
    status: Optional[str] = None
    description: Optional[str] = None
    rating: Optional[int] = Field(None, ge=1, le=5)
    thoughts: Optional[str] = None
    format: Optional[str] = None
    date_read: Optional[str] = None
    sale_price: Optional[float] = None
    sale_date: Optional[str] = None
    cover_url: Optional[str] = None


class LendIn(BaseModel):
    borrower: str
    due_date: str


class AuthorIn(BaseModel):
    name: str
    country: str = ""
    dob: str = ""
    awards: list[str] = []


class AuthorUpdate(BaseModel):
    name: Optional[str] = None
    country: Optional[str] = None
    dob: Optional[str] = None
    awards: Optional[list[str]] = None
    add_award: Optional[list[str]] = None
    remove_award: Optional[list[str]] = None


class WishlistIn(BaseModel):
    isbn: str
    title: str
    author_name: str = ""
    year: int = 0
    genre: str = ""


class ProfileUpdate(BaseModel):
    username: str


# ── books ───────────────────────────────────────────────────────────────────

@app.get("/api/books")
def list_books(
    genre: Optional[str] = None,
    status: Optional[str] = None,
    after: Optional[int] = None,
    before: Optional[int] = None,
    sort: str = Query("title", pattern="^(title|year|author|date_added)$"),
):
    books = store.list_books(sort=sort)  # SOQL ORDER BY pushed down
    authors = store.all_authors_dict()

    if genre:
        books = [(i, b) for i, b in books if b.get("genre", "").lower() == genre.lower()]
    if status:
        books = [(i, b) for i, b in books if b.get("status") == status]
    if after:
        books = [(i, b) for i, b in books if b.get("year", 0) > after]
    if before:
        books = [(i, b) for i, b in books if b.get("year", 0) < before]

    return [_book_out(i, b, authors) for i, b in books]


@app.get("/api/books/{isbn}")
def get_book(isbn: str):
    db = store.load()
    book = store.get_book(db, isbn)
    if book is None:
        raise HTTPException(404, "Book not found")
    return _book_out(isbn, book, store.all_authors_dict())


@app.post("/api/books", status_code=201)
def add_book(body: BookIn):
    db = store.load()
    if store.get_book(db, body.isbn):
        raise HTTPException(409, "ISBN already exists")
    if store.get_author(db, body.author_id) is None:
        raise HTTPException(404, "author_id not found")

    book = {
        "title": body.title,
        "author_id": body.author_id,
        "pages": body.pages,
        "year": body.year,
        "genre": body.genre,
        "publisher": body.publisher,
        "status": "available",
        "lending": None,
        "description": body.description,
        "rating": None,
        "thoughts": None,
        "format": body.format,
        "date_added": _today(),
        "date_read": None,
        "sale_price": None,
        "sale_date": None,
        "cover_url": body.cover_url,
    }
    store.put_book(db, body.isbn, book)
    store.log_activity(db, "added", f"Added '{body.title}'", isbn=body.isbn)

    if store.get_wishlist_item(db, body.isbn):
        store.delete_wishlist_item(db, body.isbn)
        store.log_activity(db, "wishlist_removed", f"Moved '{body.title}' from wishlist to collection", isbn=body.isbn)

    store.save(db)
    return _book_out(body.isbn, book, store.all_authors_dict())


@app.put("/api/books/{isbn}")
def update_book(isbn: str, body: BookUpdate):
    db = store.load()
    book = store.get_book(db, isbn)
    if book is None:
        raise HTTPException(404, "Book not found")

    data = body.model_dump(exclude_unset=True)

    if "author_id" in data and store.get_author(db, data["author_id"]) is None:
        raise HTTPException(404, "author_id not found")

    if "status" in data and data["status"] not in ("available", "lent", "reading", "sold"):
        raise HTTPException(400, "status must be available | lent | reading | sold")

    for field in ("title", "author_id", "pages", "year", "genre", "publisher",
                  "description", "thoughts", "format", "date_read", "sale_price", "sale_date",
                  "cover_url"):
        if field in data:
            book[field] = data[field]

    if "rating" in data:
        old = book.get("rating")
        book["rating"] = data["rating"]
        if data["rating"] and data["rating"] != old:
            store.log_activity(db, "rated", f"Rated '{book['title']}' {data['rating']}/5", isbn=isbn)

    if "status" in data:
        old_status = book.get("status")
        book["status"] = data["status"]
        if data["status"] == "reading" and old_status != "reading":
            store.log_activity(db, "started_reading", f"Started reading '{book['title']}'", isbn=isbn)
        elif data["status"] == "sold" and old_status != "sold":
            store.log_activity(db, "sold", f"Sold '{book['title']}'", isbn=isbn)

    if "date_read" in data and data["date_read"] and not book.get("date_read"):
        store.log_activity(db, "finished_reading", f"Finished '{book['title']}'", isbn=isbn)

    store.put_book(db, isbn, book)
    store.save(db)
    return _book_out(isbn, book, store.all_authors_dict())


@app.delete("/api/books/{isbn}")
def delete_book(isbn: str):
    db = store.load()
    book = store.get_book(db, isbn)
    if book is None:
        raise HTTPException(404, "Book not found")
    if book["status"] == "lent":
        raise HTTPException(409, f"Cannot remove: lent to '{book['lending']['borrower']}'")
    store.delete_book(db, isbn)
    store.save(db)
    return {"deleted": isbn}


# ── lending ──────────────────────────────────────────────────────────────────

@app.post("/api/books/{isbn}/lend")
def lend_book(isbn: str, body: LendIn):
    db = store.load()
    book = store.get_book(db, isbn)
    if book is None:
        raise HTTPException(404, "Book not found")
    if book["status"] != "available":
        raise HTTPException(409, f"Cannot lend: status is '{book['status']}'")

    book["status"] = "lent"
    book["lending"] = {"borrower": body.borrower, "due_date": body.due_date}
    store.put_book(db, isbn, book)
    store.log_activity(db, "lent", f"Lent '{book['title']}' to {body.borrower}", isbn=isbn)
    store.save(db)
    return _book_out(isbn, book, store.all_authors_dict())


@app.post("/api/books/{isbn}/return")
def return_book(isbn: str):
    db = store.load()
    book = store.get_book(db, isbn)
    if book is None:
        raise HTTPException(404, "Book not found")
    if book["status"] != "lent":
        raise HTTPException(409, f"Cannot return: status is '{book['status']}'")

    borrower = book["lending"]["borrower"]
    book["status"] = "available"
    book["lending"] = None
    store.put_book(db, isbn, book)
    store.log_activity(db, "returned", f"Returned '{book['title']}' from {borrower}", isbn=isbn)
    store.save(db)
    return _book_out(isbn, book, store.all_authors_dict())


# ── authors ──────────────────────────────────────────────────────────────────

@app.get("/api/authors")
def list_authors():
    authors = store.list_authors()
    authors.sort(key=lambda x: x[1]["name"].lower())
    return [{"id": aid, **a} for aid, a in authors]


@app.get("/api/authors/{author_id}")
def get_author(author_id: str):
    db = store.load()
    author = store.get_author(db, author_id)
    if author is None:
        raise HTTPException(404, "Author not found")
    authors = store.all_authors_dict()
    books = [
        _book_out(isbn, b, authors)
        for isbn, b in store.list_books()
        if b["author_id"] == author_id
    ]
    return {"id": author_id, **author, "books": books}


@app.post("/api/authors", status_code=201)
def add_author(body: AuthorIn):
    db = store.load()
    author = {"name": body.name, "country": body.country, "dob": body.dob, "awards": body.awards}
    author_id = store.create_author(db, author)
    store.log_activity(db, "author_added", f"Added author '{body.name}'")
    return {"id": author_id, **author}


@app.put("/api/authors/{author_id}")
def update_author(author_id: str, body: AuthorUpdate):
    db = store.load()
    author = store.get_author(db, author_id)
    if author is None:
        raise HTTPException(404, "Author not found")

    data = body.model_dump(exclude_unset=True)
    for field in ("name", "country", "dob"):
        if field in data:
            author[field] = data[field]
    if "awards" in data:
        author["awards"] = data["awards"]
    if "add_award" in data:
        for award in data["add_award"]:
            if award not in author["awards"]:
                author["awards"].append(award)
    if "remove_award" in data:
        author["awards"] = [a for a in author["awards"] if a not in data["remove_award"]]

    store.put_author(db, author_id, author)
    store.save(db)
    return {"id": author_id, **author}


@app.delete("/api/authors/{author_id}")
def delete_author(author_id: str):
    db = store.load()
    if not store.get_author(db, author_id):
        raise HTTPException(404, "Author not found")
    linked = [isbn for isbn, b in store.list_books() if b["author_id"] == author_id]
    if linked:
        raise HTTPException(409, f"Cannot remove: linked to {len(linked)} book(s)")
    store.delete_author(db, author_id)
    store.save(db)
    return {"deleted": author_id}


# ── wishlist ─────────────────────────────────────────────────────────────────

@app.get("/api/wishlist")
def list_wishlist():
    return [{"isbn": isbn, **item} for isbn, item in store.list_wishlist()]


@app.post("/api/wishlist", status_code=201)
def add_to_wishlist(body: WishlistIn):
    db = store.load()
    if store.get_book(db, body.isbn):
        raise HTTPException(409, "Already in collection")
    item = {"title": body.title, "author_name": body.author_name, "year": body.year, "genre": body.genre}
    store.put_wishlist_item(db, body.isbn, item)
    store.log_activity(db, "wishlist_added", f"Wishlisted '{body.title}'", isbn=body.isbn)
    store.save(db)
    return {"isbn": body.isbn, **item}


@app.delete("/api/wishlist/{isbn}")
def remove_from_wishlist(isbn: str):
    db = store.load()
    item = store.get_wishlist_item(db, isbn)
    if item is None:
        raise HTTPException(404, "Not in wishlist")
    store.delete_wishlist_item(db, isbn)
    store.log_activity(db, "wishlist_removed", f"Removed '{item['title']}' from wishlist", isbn=isbn)
    store.save(db)
    return {"deleted": isbn}


# ── profile & stats ───────────────────────────────────────────────────────────

@app.get("/api/profile")
def get_profile():
    db = store.load()
    return {**store.get_profile(db), "stats": store.compute_stats(db)}


@app.put("/api/profile")
def update_profile(body: ProfileUpdate):
    db = store.load()
    profile = store.get_profile(db)
    profile["username"] = body.username.strip()
    store.put_profile(db, profile)
    store.save(db)
    return profile


@app.get("/api/stats")
def get_stats():
    db = store.load()
    return store.compute_stats(db)


@app.get("/api/activity")
def get_activity(limit: int = Query(50, ge=1, le=500)):
    return store.list_activity(limit)


# ── Salesforce exception handlers ────────────────────────────────────────────
# Map simple-salesforce errors to clean HTTP responses instead of raw 500s.

def _sf_error_payload(exc: SalesforceError) -> dict:
    """Pull the first error message out of a SalesforceError, fall back to str()."""
    content = getattr(exc, "content", None)
    if isinstance(content, list) and content:
        first = content[0]
        if isinstance(first, dict):
            return {
                "detail": first.get("message") or str(exc),
                "code": first.get("errorCode"),
            }
    return {"detail": str(exc)}


@app.exception_handler(SalesforceMalformedRequest)
def _handle_sf_malformed(request: Request, exc: SalesforceMalformedRequest):
    # Validation rule, picklist mismatch, missing required field, bad SOQL, etc.
    return JSONResponse(status_code=400, content=_sf_error_payload(exc))


@app.exception_handler(SalesforceResourceNotFound)
def _handle_sf_not_found(request: Request, exc: SalesforceResourceNotFound):
    return JSONResponse(status_code=404, content={"detail": "Salesforce record not found"})


@app.exception_handler(SalesforceAuthenticationFailed)
def _handle_sf_auth(request: Request, exc: SalesforceAuthenticationFailed):
    return JSONResponse(
        status_code=503,
        content={"detail": "Salesforce authentication failed — check .env credentials"},
    )


@app.exception_handler(SalesforceError)
def _handle_sf_other(request: Request, exc: SalesforceError):
    # Catch-all for anything simple-salesforce raises that we didn't list above.
    return JSONResponse(status_code=502, content=_sf_error_payload(exc))
