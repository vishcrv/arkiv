"""
Arkiv REST API — FastAPI (multi-user, JWT auth)
Run: uvicorn api:app --reload --port 5000
"""

import os
from datetime import date, datetime, timedelta, timezone
from typing import Optional

import bcrypt
import jwt
from fastapi import Depends, FastAPI, HTTPException, Query, Request, Security
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as google_id_token
from pydantic import BaseModel, Field
from sqlalchemy.exc import IntegrityError, OperationalError, SQLAlchemyError

import store.mysql as store

app = FastAPI(title="Arkiv API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_JWT_SECRET = os.environ.get("JWT_SECRET", "change-me-in-production")
_JWT_ALGO = "HS256"
_JWT_EXPIRE_HOURS = 72
_GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "")
_bearer = HTTPBearer()
_VALID_STATUSES = {"available", "lent", "reading", "read", "sold"}


def _today() -> str:
    return date.today().isoformat()


def _make_token(user_id: str) -> str:
    exp = datetime.now(timezone.utc) + timedelta(hours=_JWT_EXPIRE_HOURS)
    return jwt.encode({"sub": user_id, "exp": exp}, _JWT_SECRET, algorithm=_JWT_ALGO)


def _verify_token(token: str) -> str:
    try:
        payload = jwt.decode(token, _JWT_SECRET, algorithms=[_JWT_ALGO])
        return payload["sub"]
    except jwt.ExpiredSignatureError:
        raise HTTPException(401, "Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(401, "Invalid token")


def get_current_user(creds: HTTPAuthorizationCredentials = Security(_bearer)) -> str:
    return _verify_token(creds.credentials)


def _book_out(isbn: str, book: dict, authors: dict) -> dict:
    author = authors.get(book.get("author_id", ""))
    return {"isbn": isbn, **book, "author_name": author["name"] if author else None}


# ── request bodies ───────────────────────────────────────────────────────────

class RegisterIn(BaseModel):
    email: str
    username: str
    password: str


class LoginIn(BaseModel):
    email: str
    password: str


class GoogleAuthIn(BaseModel):
    id_token: str


class BookIn(BaseModel):
    isbn: str
    title: str
    author_id: str
    pages: int = 0
    year: int = 0
    genres: list[str] = []
    publisher: str = ""
    description: Optional[str] = None
    format: str = "paperback"
    cover_url: Optional[str] = None


class BookUpdate(BaseModel):
    title: Optional[str] = None
    author_id: Optional[str] = None
    pages: Optional[int] = None
    year: Optional[int] = None
    genres: Optional[list[str]] = None
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
    genres: list[str] = []
    cover_url: Optional[str] = None
    buy_url: Optional[str] = None


class ProfileUpdate(BaseModel):
    username: Optional[str] = None
    theme: Optional[str] = None


# ── auth ─────────────────────────────────────────────────────────────────────

@app.post("/api/auth/register", status_code=201)
def register(body: RegisterIn):
    if store.get_user_by_email(body.email):
        raise HTTPException(409, "Email already registered")
    pw_hash = bcrypt.hashpw(body.password.encode(), bcrypt.gensalt()).decode()
    user_id = store.create_user(email=body.email, username=body.username.strip(),
                                password_hash=pw_hash)
    token = _make_token(user_id)
    return {"token": token, "user": store.get_user_by_id(user_id)}


@app.post("/api/auth/login")
def login(body: LoginIn):
    user = store.get_user_by_email(body.email)
    if not user or not user.get("password_hash"):
        raise HTTPException(401, "Invalid credentials")
    if not bcrypt.checkpw(body.password.encode(), user["password_hash"].encode()):
        raise HTTPException(401, "Invalid credentials")
    token = _make_token(user["user_id"])
    del user["password_hash"]
    return {"token": token, "user": user}


@app.post("/api/auth/google")
def google_auth(body: GoogleAuthIn):
    if not _GOOGLE_CLIENT_ID:
        raise HTTPException(501, "Google OAuth not configured — set GOOGLE_CLIENT_ID env var")
    try:
        info = google_id_token.verify_oauth2_token(
            body.id_token, google_requests.Request(), _GOOGLE_CLIENT_ID
        )
    except Exception:
        raise HTTPException(401, "Invalid Google token")

    google_id = info["sub"]
    email = info.get("email", "")
    name = info.get("name", email.split("@")[0])

    user = store.get_user_by_google_id(google_id) or store.get_user_by_email(email)
    if user:
        if not user.get("google_id"):
            store.put_user(user["user_id"], {"google_id": google_id})
        user_id = user["user_id"]
    else:
        user_id = store.create_user(email=email, username=name, google_id=google_id)

    return {"token": _make_token(user_id), "user": store.get_user_by_id(user_id)}


@app.get("/api/auth/me")
def me(user_id: str = Depends(get_current_user)):
    user = store.get_user_by_id(user_id)
    if not user:
        raise HTTPException(404, "User not found")
    return user


# ── genres ────────────────────────────────────────────────────────────────────

@app.get("/api/genres")
def list_genres(_: str = Depends(get_current_user)):
    return store.list_genres()


# ── books ────────────────────────────────────────────────────────────────────

@app.get("/api/books")
def list_books(
    genre: Optional[str] = None,
    genres: Optional[str] = Query(None, description="Comma-separated genre names"),
    status: Optional[str] = None,
    after: Optional[str] = None,
    before: Optional[str] = None,
    q: Optional[str] = None,
    sort: str = Query("title", pattern="^(title|title-desc|year|author|date_added|rating)$"),
    user_id: str = Depends(get_current_user),
):
    genre_filter: Optional[list[str]] = None
    if genres:
        genre_filter = [g.strip() for g in genres.split(",") if g.strip()]
    elif genre:
        genre_filter = [genre]

    books = store.list_books(user_id=user_id, sort=sort, status=status,
                             genres=genre_filter, q=q, after=after, before=before)
    authors = store.all_authors_dict(user_id)
    return [_book_out(i, b, authors) for i, b in books]


@app.get("/api/books/{isbn}")
def get_book(isbn: str, user_id: str = Depends(get_current_user)):
    db = store.load()
    book = store.get_book(db, isbn, user_id)
    if book is None:
        raise HTTPException(404, "Book not found")
    return _book_out(isbn, book, store.all_authors_dict(user_id))


@app.post("/api/books", status_code=201)
def add_book(body: BookIn, user_id: str = Depends(get_current_user)):
    db = store.load()
    if store.get_book(db, body.isbn, user_id):
        raise HTTPException(409, "ISBN already in your collection")
    if store.get_author(db, body.author_id, user_id) is None:
        raise HTTPException(404, "author_id not found")

    book = {
        "title": body.title,
        "author_id": body.author_id,
        "pages": body.pages,
        "year": body.year,
        "genres": body.genres,
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
    store.put_book(db, body.isbn, book, user_id)
    store.log_activity(db, "added", f"Added '{body.title}'", user_id=user_id, isbn=body.isbn)

    if store.get_wishlist_item(db, body.isbn, user_id):
        store.delete_wishlist_item(db, body.isbn, user_id)
        store.log_activity(db, "wishlist_removed",
                           f"Moved '{body.title}' from wishlist to collection",
                           user_id=user_id, isbn=body.isbn)

    store.save(db)
    return _book_out(body.isbn, book, store.all_authors_dict(user_id))


@app.put("/api/books/{isbn}")
def update_book(isbn: str, body: BookUpdate, user_id: str = Depends(get_current_user)):
    db = store.load()
    book = store.get_book(db, isbn, user_id)
    if book is None:
        raise HTTPException(404, "Book not found")

    data = body.model_dump(exclude_unset=True)

    if "author_id" in data and store.get_author(db, data["author_id"], user_id) is None:
        raise HTTPException(404, "author_id not found")

    if "status" in data and data["status"] not in _VALID_STATUSES:
        raise HTTPException(400, f"status must be one of: {', '.join(sorted(_VALID_STATUSES))}")

    for field in ("title", "author_id", "pages", "year", "genres", "publisher",
                  "description", "thoughts", "format", "date_read",
                  "sale_price", "sale_date", "cover_url"):
        if field in data:
            book[field] = data[field]

    if "rating" in data:
        old = book.get("rating")
        book["rating"] = data["rating"]
        if data["rating"] and data["rating"] != old:
            store.log_activity(db, "rated", f"Rated '{book['title']}' {data['rating']}/5",
                               user_id=user_id, isbn=isbn)

    if "status" in data:
        old_status = book.get("status")
        book["status"] = data["status"]
        if data["status"] == "reading" and old_status != "reading":
            store.log_activity(db, "started_reading", f"Started reading '{book['title']}'",
                               user_id=user_id, isbn=isbn)
        elif data["status"] == "read" and old_status != "read":
            book["date_read"] = book.get("date_read") or _today()
            store.log_activity(db, "finished_reading", f"Finished '{book['title']}'",
                               user_id=user_id, isbn=isbn)
        elif data["status"] == "sold" and old_status != "sold":
            store.log_activity(db, "sold", f"Sold '{book['title']}'",
                               user_id=user_id, isbn=isbn)

    if "date_read" in data and data["date_read"] and not book.get("date_read"):
        store.log_activity(db, "finished_reading", f"Finished '{book['title']}'",
                           user_id=user_id, isbn=isbn)

    store.put_book(db, isbn, book, user_id)
    store.save(db)
    return _book_out(isbn, book, store.all_authors_dict(user_id))


@app.delete("/api/books/{isbn}")
def delete_book(isbn: str, user_id: str = Depends(get_current_user)):
    db = store.load()
    book = store.get_book(db, isbn, user_id)
    if book is None:
        raise HTTPException(404, "Book not found")
    if book["status"] == "lent":
        raise HTTPException(409, f"Cannot remove: lent to '{book['lending']['borrower']}'")
    store.delete_book(db, isbn, user_id)
    store.save(db)
    return {"deleted": isbn}


# ── lending ──────────────────────────────────────────────────────────────────

@app.post("/api/books/{isbn}/lend")
def lend_book(isbn: str, body: LendIn, user_id: str = Depends(get_current_user)):
    db = store.load()
    book = store.get_book(db, isbn, user_id)
    if book is None:
        raise HTTPException(404, "Book not found")
    if book["status"] != "available":
        raise HTTPException(409, f"Cannot lend: status is '{book['status']}'")

    book["status"] = "lent"
    book["lending"] = {"borrower": body.borrower, "due_date": body.due_date}
    store.put_book(db, isbn, book, user_id)
    store.log_activity(db, "lent", f"Lent '{book['title']}' to {body.borrower}",
                       user_id=user_id, isbn=isbn)
    store.save(db)
    return _book_out(isbn, book, store.all_authors_dict(user_id))


@app.post("/api/books/{isbn}/return")
def return_book(isbn: str, user_id: str = Depends(get_current_user)):
    db = store.load()
    book = store.get_book(db, isbn, user_id)
    if book is None:
        raise HTTPException(404, "Book not found")
    if book["status"] != "lent":
        raise HTTPException(409, f"Cannot return: status is '{book['status']}'")

    borrower = book["lending"]["borrower"]
    book["status"] = "available"
    book["lending"] = None
    store.put_book(db, isbn, book, user_id)
    store.log_activity(db, "returned", f"Returned '{book['title']}' from {borrower}",
                       user_id=user_id, isbn=isbn)
    store.save(db)
    return _book_out(isbn, book, store.all_authors_dict(user_id))


# ── authors ──────────────────────────────────────────────────────────────────

@app.get("/api/authors")
def list_authors(user_id: str = Depends(get_current_user)):
    return [{"id": aid, **a} for aid, a in store.list_authors(user_id)]


@app.get("/api/authors/{author_id}")
def get_author(author_id: str, user_id: str = Depends(get_current_user)):
    db = store.load()
    author = store.get_author(db, author_id, user_id)
    if author is None:
        raise HTTPException(404, "Author not found")
    books = [
        _book_out(isbn, b, store.all_authors_dict(user_id))
        for isbn, b in store.list_books(user_id=user_id)
        if b["author_id"] == author_id
    ]
    return {"id": author_id, **author, "books": books}


@app.post("/api/authors", status_code=201)
def add_author(body: AuthorIn, user_id: str = Depends(get_current_user)):
    db = store.load()
    author = {"name": body.name, "country": body.country, "dob": body.dob, "awards": body.awards}
    author_id = store.create_author(db, author, user_id)
    store.log_activity(db, "author_added", f"Added author '{body.name}'", user_id=user_id)
    return {"id": author_id, **author}


@app.put("/api/authors/{author_id}")
def update_author(author_id: str, body: AuthorUpdate, user_id: str = Depends(get_current_user)):
    db = store.load()
    author = store.get_author(db, author_id, user_id)
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

    store.put_author(db, author_id, author, user_id)
    store.save(db)
    return {"id": author_id, **author}


@app.delete("/api/authors/{author_id}")
def delete_author(author_id: str, user_id: str = Depends(get_current_user)):
    db = store.load()
    if not store.get_author(db, author_id, user_id):
        raise HTTPException(404, "Author not found")
    linked = [isbn for isbn, b in store.list_books(user_id=user_id) if b["author_id"] == author_id]
    if linked:
        raise HTTPException(409, f"Cannot remove: linked to {len(linked)} book(s)")
    store.delete_author(db, author_id, user_id)
    store.save(db)
    return {"deleted": author_id}


# ── wishlist ─────────────────────────────────────────────────────────────────

@app.get("/api/wishlist")
def list_wishlist(
    sort: str = Query("title", pattern="^(title|title-desc|year|year-desc)$"),
    user_id: str = Depends(get_current_user),
):
    return [{"isbn": isbn, **item} for isbn, item in store.list_wishlist(user_id, sort=sort)]


@app.post("/api/wishlist", status_code=201)
def add_to_wishlist(body: WishlistIn, user_id: str = Depends(get_current_user)):
    db = store.load()
    if store.get_book(db, body.isbn, user_id):
        raise HTTPException(409, "Already in collection")
    item = {
        "title": body.title,
        "author_name": body.author_name,
        "year": body.year,
        "genres": body.genres,
        "cover_url": body.cover_url,
        "buy_url": body.buy_url,
    }
    store.put_wishlist_item(db, body.isbn, item, user_id)
    store.log_activity(db, "wishlist_added", f"Wishlisted '{body.title}'",
                       user_id=user_id, isbn=body.isbn)
    store.save(db)
    return {"isbn": body.isbn, **item}


@app.delete("/api/wishlist/{isbn}")
def remove_from_wishlist(isbn: str, user_id: str = Depends(get_current_user)):
    db = store.load()
    item = store.get_wishlist_item(db, isbn, user_id)
    if item is None:
        raise HTTPException(404, "Not in wishlist")
    store.delete_wishlist_item(db, isbn, user_id)
    store.log_activity(db, "wishlist_removed", f"Removed '{item['title']}' from wishlist",
                       user_id=user_id, isbn=isbn)
    store.save(db)
    return {"deleted": isbn}


# ── profile & stats ───────────────────────────────────────────────────────────

@app.get("/api/profile")
def get_profile(user_id: str = Depends(get_current_user)):
    db = store.load()
    return {**store.get_profile(db, user_id), "stats": store.compute_stats(db, user_id)}


@app.put("/api/profile")
def update_profile(body: ProfileUpdate, user_id: str = Depends(get_current_user)):
    db = store.load()
    updates = body.model_dump(exclude_unset=True)
    if "username" in updates:
        updates["username"] = updates["username"].strip()
    store.put_profile(db, updates, user_id)
    store.save(db)
    return store.get_profile(db, user_id)


@app.get("/api/stats")
def get_stats(user_id: str = Depends(get_current_user)):
    db = store.load()
    return store.compute_stats(db, user_id)


@app.get("/api/activity")
def get_activity(limit: int = Query(50, ge=1, le=500), user_id: str = Depends(get_current_user)):
    return store.list_activity(user_id, limit)


# ── DB exception handlers ────────────────────────────────────────────────────

@app.exception_handler(IntegrityError)
def _handle_integrity(request: Request, exc: IntegrityError):
    return JSONResponse(status_code=409, content={"detail": str(exc.orig), "code": "integrity_error"})


@app.exception_handler(OperationalError)
def _handle_operational(request: Request, exc: OperationalError):
    return JSONResponse(
        status_code=503,
        content={"detail": "Database unavailable — check MYSQL_URL and that MySQL is running",
                 "code": "db_unavailable"},
    )


@app.exception_handler(SQLAlchemyError)
def _handle_sqlalchemy(request: Request, exc: SQLAlchemyError):
    return JSONResponse(status_code=502, content={"detail": str(exc), "code": "db_error"})
