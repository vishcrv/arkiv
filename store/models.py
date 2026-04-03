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
    status: str     # available | lent
    lending: Optional[Lending]


class Store(TypedDict):
    authors: dict[str, Author]
    books: dict[str, Book]   # key = ISBN-13
