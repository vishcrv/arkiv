from typing import Optional
from typing_extensions import TypedDict


class Lending(TypedDict):
    borrower: str
    due_date: str  # ISO 8601


class Author(TypedDict):
    name: str
    country: str
    dob: str        # ISO 8601
    awards: list[str]


class Book(TypedDict):
    title: str
    author_id: str  # uuid → authors key
    pages: int
    year: int
    genre: str
    publisher: str
    status: str     # available | lent | reading | sold
    lending: Optional[Lending]
    description: Optional[str]
    rating: Optional[int]       # 1–5, user's personal rating
    thoughts: Optional[str]     # user's notes/review
    format: str                 # paperback | kindle | epub | pdf
    date_added: str             # ISO 8601 — when added to collection
    date_read: Optional[str]    # ISO 8601 — when finished
    sale_price: Optional[float] # if status == "sold"
    sale_date: Optional[str]    # ISO 8601, if status == "sold"


class WishlistItem(TypedDict):
    title: str
    author_name: str
    year: int
    genre: str


class ActivityEntry(TypedDict):
    action: str     # added | rated | lent | returned | sold | started_reading | finished_reading | wishlist_added | wishlist_removed | author_added
    isbn: Optional[str]
    timestamp: str  # ISO 8601
    detail: str


class Profile(TypedDict):
    username: str
    created_at: str  # ISO 8601


class Store(TypedDict):
    authors: dict[str, Author]
    books: dict[str, Book]          # key = ISBN-13
    wishlist: dict[str, WishlistItem]  # key = ISBN-13
    activity: list[ActivityEntry]
    profile: Profile
