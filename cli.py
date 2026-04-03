"""
Interactive terminal menu for arkiv.
Run:  python cli.py
"""
import os
import sys
from datetime import date

import store


# --- input helpers ---

def ask(prompt, required=True):
    while True:
        val = input(f"  {prompt}: ").strip()
        if val:
            return val
        if not required:
            return ""
        print("  (required, please enter a value)")


def ask_int(prompt, required=True):
    while True:
        val = input(f"  {prompt}: ").strip()
        if not val and not required:
            return None
        try:
            return int(val)
        except ValueError:
            print("  (must be a whole number)")


def ask_float(prompt):
    while True:
        val = input(f"  {prompt}: ").strip()
        try:
            return float(val)
        except ValueError:
            print("  (must be a number, e.g. 12.99)")


def pause():
    input("\n  Press Enter to continue...")


def clear():
    os.system("cls" if os.name == "nt" else "clear")


def section(title):
    print(f"\n  {'─' * 40}")
    print(f"  {title}")
    print(f"  {'─' * 40}")


def err(msg):
    print(f"\n  ! {msg}")


def ok(msg):
    print(f"\n  ✓ {msg}")


# --- author actions ---

def do_list_authors():
    db = store.load()
    authors = sorted(db["authors"].items(), key=lambda x: x[1]["name"].lower())
    section("All Authors")
    if not authors:
        print("  (none)")
        return
    for _, a in authors:
        awards = ", ".join(a["awards"]) if a["awards"] else "—"
        print(f"  {a['name']}  |  {a['country']}  |  b.{a['dob']}  |  {awards}")


def do_add_author():
    section("Add Author")
    name = ask("Full name")
    country = ask("Country")
    dob = ask("Date of birth (YYYY-MM-DD)")
    awards_raw = ask("Awards (comma-separated, or leave blank)", required=False)
    awards = [a.strip() for a in awards_raw.split(",")] if awards_raw else []

    db = store.load()
    author_id = store.new_author_id()
    store.put_author(db, author_id, {"name": name, "country": country, "dob": dob, "awards": awards})
    store.save(db)
    ok(f"Added '{name}' ({author_id})")


def do_view_author():
    section("View Author")
    name = ask("Author name")
    db = store.load()
    author_id, author = _find_author(db, name)
    if author is None:
        return
    print(f"\n  Name:    {author['name']}")
    print(f"  Country: {author['country']}")
    print(f"  DOB:     {author['dob']}")
    print(f"  Awards:  {', '.join(author['awards']) if author['awards'] else '—'}")
    books = [(isbn, b) for isbn, b in db["books"].items() if b["author_id"] == author_id]
    print(f"\n  Books ({len(books)}):")
    if not books:
        print("    (none)")
    for isbn, b in sorted(books, key=lambda x: x[1]["year"]):
        print(f"    [{isbn}] {b['title']} ({b['year']}) — {b['status']}")


def do_update_author():
    section("Update Author")
    name = ask("Author name to update")
    db = store.load()
    author_id, author = _find_author(db, name)
    if author is None:
        return
    print("  (leave blank to keep current value)")
    new_name = ask(f"New name [{author['name']}]", required=False)
    new_country = ask(f"New country [{author['country']}]", required=False)
    new_dob = ask(f"New DOB [{author['dob']}]", required=False)
    add_award = ask("Add award (or blank)", required=False)
    remove_award = ask("Remove award (or blank)", required=False)

    if new_name:
        author["name"] = new_name
    if new_country:
        author["country"] = new_country
    if new_dob:
        author["dob"] = new_dob
    if add_award and add_award not in author["awards"]:
        author["awards"].append(add_award)
    if remove_award:
        author["awards"] = [a for a in author["awards"] if a != remove_award]

    store.put_author(db, author_id, author)
    store.save(db)
    ok(f"Updated '{author['name']}'.")


def do_remove_author():
    section("Remove Author")
    name = ask("Author name to remove")
    db = store.load()
    author_id, author = _find_author(db, name)
    if author is None:
        return
    linked = [b["title"] for b in db["books"].values() if b["author_id"] == author_id]
    if linked:
        err(f"Cannot remove — linked books: {', '.join(linked)}")
        return
    confirm = ask(f"Type '{name}' to confirm deletion")
    if confirm != name:
        print("  Cancelled.")
        return
    store.delete_author(db, author_id)
    store.save(db)
    ok(f"Removed '{name}'.")


# --- book actions ---

def do_list_books():
    db = store.load()
    books = sorted(db["books"].items(), key=lambda x: x[1]["title"].lower())
    section("All Books")
    if not books:
        print("  (none)")
        return
    for isbn, b in books:
        author = db["authors"].get(b["author_id"])
        author_name = author["name"] if author else b["author_id"]
        print(f"  [{isbn}] {b['title']} — {author_name} ({b['year']}) [{b['status']}]")


def do_add_book():
    section("Add Book")
    # show authors so user can pick an ID
    db = store.load()
    authors = sorted(db["authors"].items(), key=lambda x: x[1]["name"].lower())
    if not authors:
        err("No authors found. Add an author first.")
        return
    print("\n  Available authors:")
    for aid, a in authors:
        print(f"    {aid}  —  {a['name']}")
    print()
    title = ask("Title")
    isbn = ask("ISBN-13")
    if store.get_book(db, isbn):
        err(f"ISBN '{isbn}' already exists.")
        return
    author_id = ask("Author ID (from list above)")
    if author_id not in db["authors"]:
        err(f"Author ID '{author_id}' not found.")
        return
    pages = ask_int("Page count")
    year = ask_int("Publication year")
    genre = ask("Genre")
    publisher = ask("Publisher")

    store.put_book(db, isbn, {
        "title": title, "author_id": author_id, "pages": pages,
        "year": year, "genre": genre, "publisher": publisher,
        "status": "available", "lending": None, "sale": None,
    })
    store.save(db)
    ok(f"Added '{title}' ({isbn})")


def do_view_book():
    section("View Book")
    isbn = ask("ISBN")
    db = store.load()
    book = store.get_book(db, isbn)
    if book is None:
        err(f"No book with ISBN '{isbn}'.")
        return
    author = db["authors"].get(book["author_id"])
    author_name = author["name"] if author else book["author_id"]
    print(f"\n  Title:     {book['title']}")
    print(f"  ISBN:      {isbn}")
    print(f"  Author:    {author_name}")
    print(f"  Year:      {book['year']}")
    print(f"  Genre:     {book['genre']}")
    print(f"  Publisher: {book['publisher']}")
    print(f"  Pages:     {book['pages']}")
    print(f"  Status:    {book['status']}")
    if book["status"] == "lent" and book["lending"]:
        l = book["lending"]
        print(f"  Borrower:  {l['borrower']}  |  Due: {l['due_date']}")
    if book["status"] == "sold" and book["sale"]:
        s = book["sale"]
        print(f"  Buyer:     {s['buyer']}  |  ${s['price']}  |  {s['date']}")


def do_update_book():
    section("Update Book")
    isbn = ask("ISBN of book to update")
    db = store.load()
    book = store.get_book(db, isbn)
    if book is None:
        err(f"No book with ISBN '{isbn}'.")
        return
    print("  (leave blank to keep current value)")
    new_title = ask(f"Title [{book['title']}]", required=False)
    new_genre = ask(f"Genre [{book['genre']}]", required=False)
    new_publisher = ask(f"Publisher [{book['publisher']}]", required=False)
    new_pages = ask_int(f"Pages [{book['pages']}]", required=False)
    new_year = ask_int(f"Year [{book['year']}]", required=False)

    if new_title:
        book["title"] = new_title
    if new_genre:
        book["genre"] = new_genre
    if new_publisher:
        book["publisher"] = new_publisher
    if new_pages is not None:
        book["pages"] = new_pages
    if new_year is not None:
        book["year"] = new_year

    store.put_book(db, isbn, book)
    store.save(db)
    ok(f"Updated '{book['title']}'.")


def do_remove_book():
    section("Remove Book")
    isbn = ask("ISBN")
    db = store.load()
    book = store.get_book(db, isbn)
    if book is None:
        err(f"No book with ISBN '{isbn}'.")
        return
    if book["status"] == "lent":
        err(f"Cannot remove — currently lent to '{book['lending']['borrower']}'.")
        return
    confirm = ask(f"Type the title '{book['title']}' to confirm deletion")
    if confirm != book["title"]:
        print("  Cancelled.")
        return
    store.delete_book(db, isbn)
    store.save(db)
    ok(f"Removed '{book['title']}'.")


# --- lending actions ---

def do_lend_book():
    section("Lend a Book")
    isbn = ask("ISBN")
    db = store.load()
    book = store.get_book(db, isbn)
    if book is None:
        err(f"No book with ISBN '{isbn}'.")
        return
    if book["status"] != "available":
        err(f"Cannot lend — status is '{book['status']}'.")
        return
    borrower = ask("Borrower name")
    due_date = ask("Due date (YYYY-MM-DD)")
    book["status"] = "lent"
    book["lending"] = {"borrower": borrower, "due_date": due_date}
    store.put_book(db, isbn, book)
    store.save(db)
    ok(f"Lent '{book['title']}' to {borrower}, due {due_date}.")


def do_return_book():
    section("Return a Book")
    isbn = ask("ISBN")
    db = store.load()
    book = store.get_book(db, isbn)
    if book is None:
        err(f"No book with ISBN '{isbn}'.")
        return
    if book["status"] != "lent":
        err(f"Cannot return — status is '{book['status']}'.")
        return
    borrower = book["lending"]["borrower"]
    book["status"] = "available"
    book["lending"] = None
    store.put_book(db, isbn, book)
    store.save(db)
    ok(f"Returned '{book['title']}' from {borrower}.")


def do_list_lent():
    db = store.load()
    lent = [(isbn, b) for isbn, b in db["books"].items() if b["status"] == "lent"]
    section("Currently Lent")
    if not lent:
        print("  (none)")
        return
    for isbn, b in sorted(lent, key=lambda x: x[1]["lending"]["due_date"]):
        l = b["lending"]
        print(f"  [{isbn}] {b['title']}  |  {l['borrower']}  |  due {l['due_date']}")


def do_overdue():
    db = store.load()
    today = date.today().isoformat()
    overdue = [
        (isbn, b) for isbn, b in db["books"].items()
        if b["status"] == "lent" and b["lending"]["due_date"] < today
    ]
    section("Overdue Books")
    if not overdue:
        print("  (none)")
        return
    for isbn, b in sorted(overdue, key=lambda x: x[1]["lending"]["due_date"]):
        l = b["lending"]
        print(f"  [{isbn}] {b['title']}  |  {l['borrower']}  |  due {l['due_date']}  *** OVERDUE ***")


# --- sale actions ---

def do_sell_book():
    section("Sell a Book")
    isbn = ask("ISBN")
    db = store.load()
    book = store.get_book(db, isbn)
    if book is None:
        err(f"No book with ISBN '{isbn}'.")
        return
    if book["status"] != "available":
        err(f"Cannot sell — status is '{book['status']}'.")
        return
    buyer = ask("Buyer name")
    price = ask_float("Sale price")
    sale_date = ask("Sale date (YYYY-MM-DD)", )
    book["status"] = "sold"
    book["sale"] = {"buyer": buyer, "price": price, "date": sale_date}
    store.put_book(db, isbn, book)
    store.save(db)
    ok(f"Sold '{book['title']}' to {buyer} for ${price}.")


def do_list_sold():
    db = store.load()
    sold = [(isbn, b) for isbn, b in db["books"].items() if b["status"] == "sold"]
    section("Sold Books")
    if not sold:
        print("  (none)")
        return
    for isbn, b in sorted(sold, key=lambda x: x[1]["sale"]["date"], reverse=True):
        s = b["sale"]
        print(f"  [{isbn}] {b['title']}  |  {s['buyer']}  |  ${s['price']}  |  {s['date']}")


# --- search actions ---

def do_find_isbn():
    section("Find by ISBN")
    isbn = ask("ISBN")
    db = store.load()
    book = store.get_book(db, isbn)
    if book is None:
        err(f"No book with ISBN '{isbn}'.")
        return
    author = db["authors"].get(book["author_id"])
    author_name = author["name"] if author else book["author_id"]
    print(f"\n  [{isbn}] {book['title']} — {author_name} ({book['year']}, {book['genre']}) [{book['status']}]")


def do_find_author():
    section("Find Books by Author")
    name = ask("Author name")
    db = store.load()
    author_id, author = _find_author(db, name)
    if author is None:
        return
    books = [(isbn, b) for isbn, b in db["books"].items() if b["author_id"] == author_id]
    if not books:
        print(f"  No books found for '{name}'.")
        return
    for isbn, b in sorted(books, key=lambda x: x[1]["year"]):
        print(f"  [{isbn}] {b['title']} ({b['year']}) [{b['status']}]")


def do_filter_books():
    section("Filter Books")
    print("  (leave blank to skip a filter)")
    genre = ask("Genre", required=False)
    status = ask("Status (available / lent / sold)", required=False)
    after = ask_int("Published after year", required=False)
    before = ask_int("Published before year", required=False)

    db = store.load()
    results = list(db["books"].items())
    if genre:
        results = [(i, b) for i, b in results if b["genre"].lower() == genre.lower()]
    if status:
        results = [(i, b) for i, b in results if b["status"] == status]
    if after is not None:
        results = [(i, b) for i, b in results if b["year"] > after]
    if before is not None:
        results = [(i, b) for i, b in results if b["year"] < before]

    print(f"\n  {len(results)} result(s):")
    for isbn, b in sorted(results, key=lambda x: x[1]["year"]):
        author = db["authors"].get(b["author_id"])
        author_name = author["name"] if author else b["author_id"]
        print(f"  [{isbn}] {b['title']} — {author_name} ({b['year']}) [{b['status']}]")


# --- utility actions ---

def do_stats():
    db = store.load()
    books = db["books"]
    status_counts = {"available": 0, "lent": 0, "sold": 0}
    genre_counts = {}
    sales_total = 0.0
    for b in books.values():
        status_counts[b["status"]] = status_counts.get(b["status"], 0) + 1
        genre_counts[b["genre"]] = genre_counts.get(b["genre"], 0) + 1
        if b["status"] == "sold" and b["sale"]:
            sales_total += b["sale"]["price"]

    section("Collection Stats")
    print(f"  Authors        : {len(db['authors'])}")
    print(f"  Total books    : {len(books)}")
    print(f"    available    : {status_counts['available']}")
    print(f"    lent         : {status_counts['lent']}")
    print(f"    sold         : {status_counts['sold']}")
    print(f"\n  By genre:")
    for genre, count in sorted(genre_counts.items(), key=lambda x: -x[1]):
        print(f"    {genre:<20} {count}")
    print(f"\n  Total sales value: ${sales_total:.2f}")


# --- internal helper ---

def _find_author(db, name):
    name_lower = name.lower()
    matches = [(aid, a) for aid, a in db["authors"].items()
               if a["name"].lower() == name_lower]
    if len(matches) == 1:
        return matches[0]
    err(f"Author '{name}' not found.")
    return None, None


# --- menu ---

MENU = [
    ("AUTHORS", [
        ("List authors",       do_list_authors),
        ("Add author",         do_add_author),
        ("View author",        do_view_author),
        ("Update author",      do_update_author),
        ("Remove author",      do_remove_author),
    ]),
    ("BOOKS", [
        ("List books",         do_list_books),
        ("Add book",           do_add_book),
        ("View book",          do_view_book),
        ("Update book",        do_update_book),
        ("Remove book",        do_remove_book),
    ]),
    ("LENDING", [
        ("Lend a book",        do_lend_book),
        ("Return a book",      do_return_book),
        ("List lent books",    do_list_lent),
        ("Overdue books",      do_overdue),
    ]),
    ("SALES", [
        ("Sell a book",        do_sell_book),
        ("List sold books",    do_list_sold),
    ]),
    ("SEARCH", [
        ("Find by ISBN",       do_find_isbn),
        ("Find by author",     do_find_author),
        ("Filter books",       do_filter_books),
    ]),
    ("UTILITY", [
        ("Stats",              do_stats),
    ]),
]


def print_menu(items):
    clear()
    print("\n  ╔══════════════════════════════════════╗")
    print("  ║        ARKIV  Book Collection        ║")
    print("  ╚══════════════════════════════════════╝\n")
    n = 1
    for group, actions in items:
        print(f"  {group}")
        for label, _ in actions:
            print(f"   {n:2}.  {label}")
            n += 1
        print()
    print("    0.  Exit\n")


def run():
    # flatten for index lookup
    flat = [(label, fn) for _, actions in MENU for label, fn in actions]

    while True:
        print_menu(MENU)
        choice = input("  Choose an option: ").strip()
        if choice == "0":
            print("\n  Goodbye.\n")
            sys.exit(0)
        try:
            idx = int(choice) - 1
            if idx < 0 or idx >= len(flat):
                raise ValueError
        except ValueError:
            input("  Invalid choice. Press Enter to try again...")
            continue

        label, fn = flat[idx]
        clear()
        try:
            fn()
        except KeyboardInterrupt:
            print("\n  (cancelled)")
        pause()


if __name__ == "__main__":
    run()
