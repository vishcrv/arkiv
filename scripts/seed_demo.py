"""
Seed Arkiv with a curated demo collection — real books, Google Books covers,
mixed statuses (reading/available/lent/sold), ratings, thoughts, and activity.

Run:
    python scripts/seed_demo.py

Wipes books, authors, wishlist, activity. Keeps profile.
"""
from __future__ import annotations

import json
import os
import sys
import time
from datetime import date, datetime, timedelta, timezone

import requests
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()
ENGINE = create_engine(os.environ["MYSQL_URL"], pool_pre_ping=True, future=True)


# ── curated dataset ─────────────────────────────────────────────────────────

AUTHORS = [
    ("auth_ursula",   "Ursula K. Le Guin",        "USA",     "1929-10-21",
        ["Hugo Award", "Nebula Award", "National Book Award"]),
    ("auth_borges",   "Jorge Luis Borges",        "Argentina","1899-08-24",
        ["Formentor Prize", "Cervantes Prize"]),
    ("auth_calvino",  "Italo Calvino",            "Italy",    "1923-10-15", []),
    ("auth_murakami", "Haruki Murakami",          "Japan",    "1949-01-12",
        ["Franz Kafka Prize", "Jerusalem Prize"]),
    ("auth_morrison", "Toni Morrison",            "USA",      "1931-02-18",
        ["Nobel Prize in Literature", "Pulitzer Prize"]),
    ("auth_tolkien",  "J. R. R. Tolkien",         "UK",       "1892-01-03", []),
    ("auth_orwell",   "George Orwell",            "UK",       "1903-06-25", []),
    ("auth_atwood",   "Margaret Atwood",          "Canada",   "1939-11-18",
        ["Booker Prize", "Arthur C. Clarke Award"]),
    ("auth_garcia",   "Gabriel García Márquez",   "Colombia", "1927-03-06",
        ["Nobel Prize in Literature"]),
    ("auth_woolf",    "Virginia Woolf",           "UK",       "1882-01-25", []),
    ("auth_baldwin",  "James Baldwin",            "USA",      "1924-08-02", []),
    ("auth_dillard",  "Annie Dillard",            "USA",      "1945-04-30",
        ["Pulitzer Prize"]),
    ("auth_sebald",   "W. G. Sebald",             "Germany",  "1944-05-18", []),
    ("auth_didion",   "Joan Didion",              "USA",      "1934-12-05",
        ["National Book Award"]),
]

# Each row:
#   isbn, title, author_id, pages, year, genre, publisher,
#   status, format, description, rating, thoughts,
#   date_added, date_read, sale_price, sale_date, cover_url, borrower, due_date
TODAY = date.today()
def days_ago(n: int) -> str:
    return (TODAY - timedelta(days=n)).isoformat()


BOOKS = [
    # — currently reading —
    dict(isbn="9780060850524", title="Brave New World", author_id="auth_orwell",  # placeholder author swap
         pages=311, year=2006, genre="Fiction", publisher="Harper Perennial",
         status="reading", format="paperback", rating=None, thoughts=None,
         date_added=days_ago(8), date_read=None),
    dict(isbn="9780156028356", title="If on a winter's night a traveler",
         author_id="auth_calvino", pages=260, year=1981, genre="Fiction",
         publisher="Harvest", status="reading", format="kindle",
         rating=None, thoughts=None, date_added=days_ago(3), date_read=None),
    dict(isbn="9780525436195", title="The Way of Kings", author_id="auth_tolkien",
         pages=1007, year=2010, genre="Fantasy", publisher="Tor Books",
         status="reading", format="paperback", rating=None,
         thoughts="Slow start, but the worldbuilding is remarkable.",
         date_added=days_ago(20), date_read=None),

    # — read & available, with ratings + thoughts —
    dict(isbn="9780060929794", title="One Hundred Years of Solitude",
         author_id="auth_garcia", pages=417, year=1998, genre="Fiction",
         publisher="Harper Perennial", status="available", format="paperback",
         rating=5,
         thoughts="A book that re-arranges what you think a sentence can carry. "
                  "Macondo lives somewhere just behind my eyes now.",
         date_added=days_ago(220), date_read=days_ago(190)),
    dict(isbn="9780441172719", title="The Left Hand of Darkness",
         author_id="auth_ursula", pages=304, year=1987, genre="Sci-Fi",
         publisher="Ace Books", status="available", format="paperback",
         rating=5,
         thoughts="Cold, careful, generous. The only sci-fi I keep re-reading.",
         date_added=days_ago(400), date_read=days_ago(380)),
    dict(isbn="9780375703768", title="Labyrinths", author_id="auth_borges",
         pages=256, year=2007, genre="Fiction", publisher="New Directions",
         status="available", format="paperback",
         rating=5,
         thoughts="Library of Babel keeps showing up in my dreams.",
         date_added=days_ago(150), date_read=days_ago(120)),
    dict(isbn="9780375714832", title="Invisible Cities", author_id="auth_calvino",
         pages=176, year=1978, genre="Fiction", publisher="Harvest",
         status="available", format="paperback",
         rating=5,
         thoughts="Read it in one sitting on a long train ride. Felt like the train was the book.",
         date_added=days_ago(360), date_read=days_ago(340)),
    dict(isbn="9780679732761", title="Beloved", author_id="auth_morrison",
         pages=324, year=2004, genre="Fiction", publisher="Vintage",
         status="available", format="paperback",
         rating=5,
         thoughts="Hard, necessary. Took me three weeks to finish 300 pages.",
         date_added=days_ago(280), date_read=days_ago(250)),
    dict(isbn="9780307743657", title="The Handmaid's Tale", author_id="auth_atwood",
         pages=311, year=1998, genre="Fiction", publisher="Anchor",
         status="available", format="kindle",
         rating=4,
         thoughts="Cold, controlled prose. The afterword is what stuck.",
         date_added=days_ago(170), date_read=days_ago(140)),
    dict(isbn="9780156907392", title="To the Lighthouse", author_id="auth_woolf",
         pages=209, year=1989, genre="Fiction", publisher="Harvest",
         status="available", format="paperback",
         rating=4,
         thoughts="The middle section, 'Time Passes', is one of the bravest things in English.",
         date_added=days_ago(330), date_read=days_ago(310)),
    dict(isbn="9780679732181", title="The Fire Next Time", author_id="auth_baldwin",
         pages=128, year=1992, genre="Non-Fiction", publisher="Vintage",
         status="available", format="paperback",
         rating=5,
         thoughts="Should be required reading. Twice.",
         date_added=days_ago(95), date_read=days_ago(80)),
    dict(isbn="9780061233326", title="Pilgrim at Tinker Creek",
         author_id="auth_dillard", pages=304, year=2007, genre="Non-Fiction",
         publisher="Harper Perennial", status="available", format="paperback",
         rating=4,
         thoughts="Walk slowly through this one. It rewards walking slowly.",
         date_added=days_ago(60), date_read=days_ago(45)),
    dict(isbn="9780811214131", title="Austerlitz", author_id="auth_sebald",
         pages=298, year=2001, genre="Fiction", publisher="New Directions",
         status="available", format="paperback",
         rating=4,
         thoughts="No paragraph breaks for pages — and somehow still gentle.",
         date_added=days_ago(210), date_read=days_ago(180)),
    dict(isbn="9780375718908", title="The Year of Magical Thinking",
         author_id="auth_didion", pages=240, year=2006, genre="Non-Fiction",
         publisher="Vintage", status="available", format="kindle",
         rating=5,
         thoughts="Grief, observed without flinching.",
         date_added=days_ago(45), date_read=days_ago(30)),
    dict(isbn="9780099908401", title="Norwegian Wood", author_id="auth_murakami",
         pages=389, year=2000, genre="Fiction", publisher="Vintage",
         status="available", format="paperback",
         rating=4,
         thoughts="My favourite Murakami. The quiet one.",
         date_added=days_ago(500), date_read=days_ago(480)),
    dict(isbn="9780156030410", title="Mr. Palomar", author_id="auth_calvino",
         pages=130, year=1986, genre="Fiction", publisher="Harvest",
         status="available", format="paperback",
         rating=4,
         thoughts="A book about looking. Reads like a slow exhale.",
         date_added=days_ago(70), date_read=days_ago(55)),

    # — lent (one overdue) —
    dict(isbn="9780547928227", title="The Hobbit", author_id="auth_tolkien",
         pages=300, year=2012, genre="Fantasy", publisher="Houghton Mifflin",
         status="lent", format="paperback", rating=5,
         thoughts="Comfort book. Re-read every two years.",
         date_added=days_ago(800), date_read=days_ago(700),
         borrower="Mira", due_date=(TODAY + timedelta(days=12)).isoformat()),
    dict(isbn="9780451524935", title="1984", author_id="auth_orwell",
         pages=328, year=1961, genre="Fiction", publisher="Signet Classic",
         status="lent", format="paperback", rating=5,
         thoughts="Re-read every election year. Still scary.",
         date_added=days_ago(900), date_read=days_ago(820),
         borrower="Daniel", due_date=(TODAY - timedelta(days=4)).isoformat()),  # overdue
    dict(isbn="9781400033416", title="Kafka on the Shore",
         author_id="auth_murakami", pages=480, year=2006, genre="Fiction",
         publisher="Vintage", status="lent", format="paperback", rating=4,
         thoughts=None, date_added=days_ago(420), date_read=days_ago(400),
         borrower="Aanya", due_date=(TODAY + timedelta(days=20)).isoformat()),

    # — sold —
    dict(isbn="9780156628709", title="The Waves", author_id="auth_woolf",
         pages=297, year=1959, genre="Fiction", publisher="Harvest",
         status="sold", format="paperback", rating=3,
         thoughts="Beautiful but I never reach for it. Found it a better home.",
         date_added=days_ago(600), date_read=days_ago(560),
         sale_price=8.50, sale_date=days_ago(40)),
    dict(isbn="9780679723165", title="The Aleph and Other Stories",
         author_id="auth_borges", pages=240, year=1971, genre="Fiction",
         publisher="Vintage", status="sold", format="paperback", rating=4,
         thoughts="Already had Labyrinths — this overlapped too much.",
         date_added=days_ago(480), date_read=days_ago(450),
         sale_price=6.00, sale_date=days_ago(110)),
]

# Patch the Brave New World author swap — Huxley isn't in author list, use Orwell stand-in
# (skipping for demo realism — we want a varied list). Actually let's add Huxley.
AUTHORS.append(("auth_huxley", "Aldous Huxley", "UK", "1894-07-26", []))
for b in BOOKS:
    if b["isbn"] == "9780060850524":
        b["author_id"] = "auth_huxley"

WISHLIST = [
    ("9780374533557", "Thinking, Fast and Slow", "Daniel Kahneman", 2013, "Non-Fiction"),
    ("9780374275631", "The Vegetarian", "Han Kang", 2016, "Fiction"),
    ("9780374159603", "Stay True", "Hua Hsu", 2022, "Non-Fiction"),
    ("9780525559474", "The Midnight Library", "Matt Haig", 2020, "Fiction"),
    ("9780374538590", "Tomorrow, and Tomorrow, and Tomorrow", "Gabrielle Zevin", 2022, "Fiction"),
    ("9780525521143", "An Immense World", "Ed Yong", 2022, "Non-Fiction"),
]


# ── Google Books cover lookup ───────────────────────────────────────────────

def _cover_from_query(query: str) -> str | None:
    try:
        r = requests.get(
            "https://www.googleapis.com/books/v1/volumes",
            params={"q": query, "maxResults": 5, "printType": "books"},
            timeout=10,
        )
        if r.status_code != 200:
            return None
        for item in r.json().get("items") or []:
            info = item.get("volumeInfo", {})
            links = info.get("imageLinks", {}) or {}
            url = (links.get("thumbnail")
                   or links.get("smallThumbnail")
                   or links.get("medium")
                   or links.get("large"))
            if url:
                url = url.replace("http://", "https://").replace("&edge=curl", "")
                return url
        return None
    except Exception as e:
        print(f"  ! query failed ({query!r}): {e}", file=sys.stderr)
        return None


def fetch_cover(isbn: str, title: str, author_name: str) -> str | None:
    """Try ISBN, then title+author fallback, with retries."""
    queries = [
        f"isbn:{isbn}",
        f'intitle:"{title}" inauthor:"{author_name}"',
        f"{title} {author_name}",
    ]
    for q in queries:
        for attempt in range(2):
            url = _cover_from_query(q)
            if url:
                return url
            time.sleep(0.5)
    return None


# ── seeding ─────────────────────────────────────────────────────────────────

def wipe(c) -> None:
    c.execute(text("SET FOREIGN_KEY_CHECKS=0"))
    for t in ("activity", "wishlist", "books", "authors"):
        c.execute(text(f"DELETE FROM {t}"))
    c.execute(text("ALTER TABLE activity AUTO_INCREMENT = 1"))
    c.execute(text("SET FOREIGN_KEY_CHECKS=1"))


def insert_authors(c) -> None:
    for aid, name, country, dob, awards in AUTHORS:
        c.execute(text("""
            INSERT INTO authors (author_id, name, country, dob, awards)
            VALUES (:aid, :name, :country, :dob, :awards)
        """), {"aid": aid, "name": name, "country": country, "dob": dob,
               "awards": json.dumps(awards)})


def insert_books(c, covers: dict[str, str | None]) -> None:
    for b in BOOKS:
        params = {
            "isbn": b["isbn"],
            "title": b["title"],
            "author_id": b["author_id"],
            "pages": b.get("pages") or 0,
            "year": b.get("year") or 0,
            "genre": b.get("genre", ""),
            "publisher": b.get("publisher", ""),
            "status": b.get("status", "available"),
            "format": b.get("format", "paperback"),
            "description": b.get("description"),
            "rating": b.get("rating"),
            "thoughts": b.get("thoughts"),
            "date_added": b["date_added"],
            "date_read": b.get("date_read"),
            "sale_price": b.get("sale_price"),
            "sale_date": b.get("sale_date"),
            "cover_url": covers.get(b["isbn"]),
            "borrower": b.get("borrower"),
            "due_date": b.get("due_date"),
        }
        c.execute(text("""
            INSERT INTO books (isbn, title, author_id, pages, year, genre, publisher,
                status, format, description, rating, thoughts, date_added, date_read,
                sale_price, sale_date, cover_url, borrower, due_date)
            VALUES (:isbn, :title, :author_id, :pages, :year, :genre, :publisher,
                :status, :format, :description, :rating, :thoughts, :date_added, :date_read,
                :sale_price, :sale_date, :cover_url, :borrower, :due_date)
        """), params)


def insert_wishlist(c) -> None:
    for isbn, title, author_name, year, genre in WISHLIST:
        c.execute(text("""
            INSERT INTO wishlist (isbn, title, author_name, year, genre)
            VALUES (:isbn, :title, :author_name, :year, :genre)
        """), {"isbn": isbn, "title": title, "author_name": author_name,
               "year": year, "genre": genre})


def insert_activity(c) -> None:
    """Hand-roll a believable activity feed with explicit timestamps."""
    rows: list[tuple[str, str | None, str, datetime]] = []

    def add(action, isbn, detail, days_back, hours=10, minutes=0):
        ts = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=days_back, hours=hours, minutes=minutes)
        rows.append((action, isbn, detail, ts))

    # Recent (visible at top of profile)
    add("started_reading", "9780156028356", "Started reading 'If on a winter's night a traveler'", 3, 2)
    add("rated", "9780375718908", "Rated 'The Year of Magical Thinking' 5/5", 5, 4)
    add("finished_reading", "9780375718908", "Finished 'The Year of Magical Thinking'", 5, 5)
    add("lent", "9780547928227", "Lent 'The Hobbit' to Mira", 7, 9)
    add("wishlist_added", "9780374533557", "Wishlisted 'Thinking, Fast and Slow'", 9, 11)
    add("started_reading", "9780525436195", "Started reading 'The Way of Kings'", 20, 12)
    add("sold", "9780156628709", "Sold 'The Waves'", 40, 14)
    add("rated", "9780061233326", "Rated 'Pilgrim at Tinker Creek' 4/5", 45, 15)
    add("finished_reading", "9780061233326", "Finished 'Pilgrim at Tinker Creek'", 45, 16)
    add("returned", "9780099908401", "Returned 'Norwegian Wood' from Sam", 60, 9)
    add("added", "9780811214131", "Added 'Austerlitz'", 80, 13)
    add("lent", "9780451524935", "Lent '1984' to Daniel", 90, 10)
    add("rated", "9780679732181", "Rated 'The Fire Next Time' 5/5", 80, 17)
    add("author_added", None, "Added author 'James Baldwin'", 95, 8)
    add("added", "9780679732181", "Added 'The Fire Next Time'", 95, 9)
    add("wishlist_removed", "9780525521143", "Removed 'An Immense World' from wishlist", 130, 12)

    for action, isbn, detail, ts in rows:
        c.execute(text("""
            INSERT INTO activity (action, isbn, detail, timestamp)
            VALUES (:action, :isbn, :detail, :ts)
        """), {"action": action, "isbn": isbn, "detail": detail, "ts": ts})


def main() -> None:
    print("→ fetching covers from Google Books…")
    author_names = {aid: name for aid, name, *_ in AUTHORS}
    covers: dict[str, str | None] = {}
    for b in BOOKS:
        url = fetch_cover(b["isbn"], b["title"], author_names.get(b["author_id"], ""))
        covers[b["isbn"]] = url
        print(f"  {b['isbn']}  {b['title'][:40]:40s}  {'OK' if url else '—'}")
        time.sleep(0.4)  # be polite

    print("\n→ wiping + inserting…")
    with ENGINE.begin() as c:
        wipe(c)
        insert_authors(c)
        insert_books(c, covers)
        insert_wishlist(c)
        insert_activity(c)

    with ENGINE.connect() as c:
        for t in ("authors", "books", "wishlist", "activity"):
            n = c.execute(text(f"SELECT COUNT(*) FROM {t}")).scalar_one()
            print(f"  {t}: {n}")

    print("\n✓ seeded.")


if __name__ == "__main__":
    main()
