from typing import Optional
from typing_extensions import TypedDict


class Lending(TypedDict):
    borrower: str
    due_date: str  # ISO 8601


class Sale(TypedDict):
    buyer: str
    price: float
    date: str  # ISO 8601


class Author(TypedDict):
    name: str
    country: str
    dob: str        # ISO 8601
    awards: list[str]


class Book(TypedDict):
    title: str
    author_id: str  # uuid → authors key
    genre: str
    year: int
    status: str     # available | lent | sold
    lending: Optional[Lending]
    sale: Optional[Sale]


class Store(TypedDict):
    authors: dict[str, Author]
    books: dict[str, Book]   # key = ISBN-13
