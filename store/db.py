import json
import uuid
from pathlib import Path

from .models import Author, Book, Store

DATA_FILE = Path(__file__).parent.parent / "data.json"

_EMPTY: Store = {"authors": {}, "books": {}}


# --- persistence ---

def load() -> Store:
    if not DATA_FILE.exists():
        return {"authors": {}, "books": {}}
    with open(DATA_FILE) as f:
        return json.load(f)


def save(store: Store) -> None:
    with open(DATA_FILE, "w") as f:
        json.dump(store, f, indent=2)


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
