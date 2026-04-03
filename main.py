import argparse
import json
import sys
from datetime import date

import store


# --- helpers ---

def find_author_by_name(db, name):
    name_lower = name.lower()
    matches = [(aid, a) for aid, a in db["authors"].items()
               if a["name"].lower() == name_lower]
    if len(matches) == 1:
        return matches[0]
    return None, None


def get_book_or_exit(db, isbn):
    book = store.get_book(db, isbn)
    if book is None:
        print(f"Book '{isbn}' not found.", file=sys.stderr)
        sys.exit(1)
    return book


# --- author commands ---

def cmd_dump(args):
    """print raw store"""
    db = store.load()
    target = args.what  # authors | books | all
    if target in ("authors", "books"):
        print(json.dumps(db[target], indent=2))
    else:
        print(json.dumps(db, indent=2))


def cmd_add_author(args):
    db = store.load()
    awards = [a.strip() for a in args.awards.split(",")] if args.awards else []
    author_id = store.new_author_id()
    store.put_author(db, author_id, {
        "name": args.name,
        "country": args.country,
        "dob": args.dob,
        "awards": awards,
    })
    store.save(db)
    print(f"Added '{args.name}' ({author_id})")


def cmd_list_authors(args):
    db = store.load()
    authors = sorted(db["authors"].items(), key=lambda x: x[1]["name"].lower())
    if not authors:
        print("No authors.")
        return
    for _, a in authors:
        awards = ", ".join(a["awards"]) if a["awards"] else "—"
        print(f"{a['name']}  |  {a['country']}  |  b.{a['dob']}  |  {awards}")


def cmd_update_author(args):
    db = store.load()
    author_id, author = find_author_by_name(db, args.name)
    if author is None:
        print(f"Author '{args.name}' not found.", file=sys.stderr)
        sys.exit(1)

    if args.new_name:
        author["name"] = args.new_name
    if args.country:
        author["country"] = args.country
    if args.dob:
        author["dob"] = args.dob
    for award in args.add_award or []:
        if award not in author["awards"]:
            author["awards"].append(award)
    if args.remove_award:
        author["awards"] = [a for a in author["awards"] if a not in args.remove_award]

    store.put_author(db, author_id, author)
    store.save(db)
    print(f"Updated '{author['name']}'.")


def cmd_remove_author(args):
    db = store.load()
    author_id, author = find_author_by_name(db, args.name)
    if author is None:
        print(f"Author '{args.name}' not found.", file=sys.stderr)
        sys.exit(1)

    linked = [isbn for isbn, b in db["books"].items() if b["author_id"] == author_id]
    if linked:
        titles = ", ".join(f"'{db['books'][isbn]['title']}'" for isbn in linked)
        print(f"Cannot remove: linked books — {titles}", file=sys.stderr)
        sys.exit(1)

    store.delete_author(db, author_id)
    store.save(db)
    print(f"Removed '{args.name}'.")


def cmd_view_author(args):
    db = store.load()
    author_id, author = find_author_by_name(db, args.name)
    if author is None:
        print(f"Author '{args.name}' not found.", file=sys.stderr)
        sys.exit(1)

    print(f"Name:    {author['name']}")
    print(f"Country: {author['country']}")
    print(f"DOB:     {author['dob']}")
    print(f"Awards:  {', '.join(author['awards']) if author['awards'] else '—'}")

    books = [(isbn, b) for isbn, b in db["books"].items() if b["author_id"] == author_id]
    print(f"\nBooks ({len(books)}):")
    if not books:
        print("  (none)")
    for isbn, b in sorted(books, key=lambda x: x[1]["year"]):
        print(f"  [{isbn}] {b['title']} ({b['year']}) — {b['status']}")


# --- book commands ---

def cmd_add_book(args):
    db = store.load()
    if store.get_book(db, args.isbn):
        print(f"ISBN '{args.isbn}' already exists.", file=sys.stderr)
        sys.exit(1)
    if args.author_id not in db["authors"]:
        print(f"Author ID '{args.author_id}' not found.", file=sys.stderr)
        sys.exit(1)
    store.put_book(db, args.isbn, {
        "title": args.title,
        "author_id": args.author_id,
        "pages": args.pages,
        "year": args.year,
        "genre": args.genre,
        "publisher": args.publisher,
        "status": "available",
        "lending": None,
    })
    store.save(db)
    print(f"Added '{args.title}' ({args.isbn})")


def cmd_remove_book(args):
    db = store.load()
    book = get_book_or_exit(db, args.isbn)
    if book["status"] == "lent":
        print(f"Cannot remove: book is currently lent to '{book['lending']['borrower']}'.", file=sys.stderr)
        sys.exit(1)
    store.delete_book(db, args.isbn)
    store.save(db)
    print(f"Removed '{book['title']}' ({args.isbn})")


def cmd_view_book(args):
    db = store.load()
    book = get_book_or_exit(db, args.isbn)
    author = db["authors"].get(book["author_id"])
    author_name = author["name"] if author else book["author_id"]

    print(f"Title:     {book['title']}")
    print(f"ISBN:      {args.isbn}")
    print(f"Author:    {author_name} ({book['author_id']})")
    print(f"Year:      {book['year']}")
    print(f"Genre:     {book['genre']}")
    print(f"Publisher: {book['publisher']}")
    print(f"Pages:     {book['pages']}")
    print(f"Status:    {book['status']}")

    if book["status"] == "lent" and book["lending"]:
        l = book["lending"]
        print(f"  Borrower: {l['borrower']}  |  Due: {l['due_date']}")
def cmd_update_book(args):
    db = store.load()
    book = get_book_or_exit(db, args.isbn)

    if args.title:
        book["title"] = args.title
    if args.author_id:
        if args.author_id not in db["authors"]:
            print(f"Author ID '{args.author_id}' not found.", file=sys.stderr)
            sys.exit(1)
        book["author_id"] = args.author_id
    if args.pages is not None:
        book["pages"] = args.pages
    if args.year is not None:
        book["year"] = args.year
    if args.genre:
        book["genre"] = args.genre
    if args.publisher:
        book["publisher"] = args.publisher

    store.put_book(db, args.isbn, book)
    store.save(db)
    print(f"Updated '{book['title']}' ({args.isbn})")


# --- lending commands ---

def cmd_lend_book(args):
    db = store.load()
    book = get_book_or_exit(db, args.isbn)
    if book["status"] != "available":
        print(f"Cannot lend: book is '{book['status']}'.", file=sys.stderr)
        sys.exit(1)
    book["status"] = "lent"
    book["lending"] = {"borrower": args.borrower, "due_date": args.due_date}
    store.put_book(db, args.isbn, book)
    store.save(db)
    print(f"Lent '{book['title']}' to {args.borrower}, due {args.due_date}.")


def cmd_return_book(args):
    db = store.load()
    book = get_book_or_exit(db, args.isbn)
    if book["status"] != "lent":
        print(f"Cannot return: book is '{book['status']}'.", file=sys.stderr)
        sys.exit(1)
    borrower = book["lending"]["borrower"]
    book["status"] = "available"
    book["lending"] = None
    store.put_book(db, args.isbn, book)
    store.save(db)
    print(f"Returned '{book['title']}' from {borrower}.")


def cmd_list_lent(args):
    db = store.load()
    lent = [(isbn, b) for isbn, b in db["books"].items() if b["status"] == "lent"]
    if not lent:
        print("No books currently lent.")
        return
    for isbn, b in sorted(lent, key=lambda x: x[1]["lending"]["due_date"]):
        l = b["lending"]
        print(f"[{isbn}] {b['title']}  |  {l['borrower']}  |  due {l['due_date']}")


def cmd_overdue(args):
    db = store.load()
    today = date.today().isoformat()
    overdue = [
        (isbn, b) for isbn, b in db["books"].items()
        if b["status"] == "lent" and b["lending"]["due_date"] < today
    ]
    if not overdue:
        print("No overdue books.")
        return
    for isbn, b in sorted(overdue, key=lambda x: x[1]["lending"]["due_date"]):
        l = b["lending"]
        print(f"[{isbn}] {b['title']}  |  {l['borrower']}  |  due {l['due_date']}  OVERDUE")


# --- utility commands ---

def cmd_stats(args):
    db = store.load()
    books = db["books"]
    authors = db["authors"]

    total_books = len(books)
    total_authors = len(authors)

    status_counts = {"available": 0, "lent": 0}
    genre_counts = {}

    for b in books.values():
        status_counts[b["status"]] = status_counts.get(b["status"], 0) + 1
        genre_counts[b["genre"]] = genre_counts.get(b["genre"], 0) + 1
    print(f"Authors : {total_authors}")
    print(f"Books   : {total_books}")
    print(f"  available : {status_counts['available']}")
    print(f"  lent      : {status_counts['lent']}")
    print(f"\nBy genre:")
    for genre, count in sorted(genre_counts.items(), key=lambda x: -x[1]):
        print(f"  {genre:<20} {count}")


def cmd_help(args):
    help_text = """
arkiv — book collection manager

  AUTHORS
    add-author      --name --country --dob [--awards]
    list-authors
    view-author     <name>
    update-author   <name> [--name --country --dob --add-award --remove-award]
    remove-author   <name>

  BOOKS
    add-book        --title --isbn --pages --year --genre --publisher --author-id
    list-books      [--sort title|year|author]
    view-book       <isbn>
    update-book     <isbn> [--title --pages --year --genre --publisher --author-id]
    remove-book     <isbn>

  LENDING
    lend-book       <isbn> --borrower --due-date
    return-book     <isbn>
    list-lent
    overdue

  SEARCH
    find-isbn       <isbn>
    find-author     <name>
    filter-books    [--genre --status --after --before]

  UTILITY
    stats
    dump            [all|authors|books]
"""
    print(help_text.strip())


# --- search & filter commands ---

def _format_book_row(isbn, book, authors):
    author = authors.get(book["author_id"])
    author_name = author["name"] if author else book["author_id"]
    return f"[{isbn}] {book['title']} — {author_name} ({book['year']}, {book['genre']}) [{book['status']}]"


def cmd_find_isbn(args):
    db = store.load()
    book = store.get_book(db, args.isbn)
    if book is None:
        print(f"No book with ISBN '{args.isbn}'.", file=sys.stderr)
        sys.exit(1)
    print(_format_book_row(args.isbn, book, db["authors"]))


def cmd_find_author(args):
    db = store.load()
    author_id, author = find_author_by_name(db, args.name)
    if author is None:
        print(f"Author '{args.name}' not found.", file=sys.stderr)
        sys.exit(1)
    books = [(isbn, b) for isbn, b in db["books"].items() if b["author_id"] == author_id]
    if not books:
        print(f"No books found for '{args.name}'.")
        return
    for isbn, b in sorted(books, key=lambda x: x[1]["year"]):
        print(_format_book_row(isbn, b, db["authors"]))


def cmd_filter_books(args):
    db = store.load()
    results = list(db["books"].items())

    if args.genre:
        genre_lower = args.genre.lower()
        results = [(isbn, b) for isbn, b in results if b["genre"].lower() == genre_lower]
    if args.status:
        results = [(isbn, b) for isbn, b in results if b["status"] == args.status]
    if args.after:
        results = [(isbn, b) for isbn, b in results if b["year"] > args.after]
    if args.before:
        results = [(isbn, b) for isbn, b in results if b["year"] < args.before]

    if not results:
        print("No books match the given filters.")
        return
    for isbn, b in sorted(results, key=lambda x: x[1]["year"]):
        print(_format_book_row(isbn, b, db["authors"]))


def cmd_list_books(args):
    db = store.load()
    books = list(db["books"].items())
    if not books:
        print("No books.")
        return

    sort_key = {
        "title":  lambda x: x[1]["title"].lower(),
        "year":   lambda x: x[1]["year"],
        "author": lambda x: (db["authors"].get(x[1]["author_id"], {}).get("name", "") or "").lower(),
    }[args.sort]

    for isbn, b in sorted(books, key=sort_key):
        print(_format_book_row(isbn, b, db["authors"]))


# --- parser ---

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="arkiv", description="book collection manager")
    sub = p.add_subparsers(dest="cmd", required=True)

    # dump
    d = sub.add_parser("dump", help="print store contents")
    d.add_argument("what", nargs="?", default="all", choices=["all", "authors", "books"])
    d.set_defaults(func=cmd_dump)

    # add-author
    aa = sub.add_parser("add-author", help="add a new author")
    aa.add_argument("--name", required=True)
    aa.add_argument("--country", required=True)
    aa.add_argument("--dob", required=True, help="YYYY-MM-DD")
    aa.add_argument("--awards", default="", help="comma-separated awards")
    aa.set_defaults(func=cmd_add_author)

    # list-authors
    la = sub.add_parser("list-authors", help="list all authors alphabetically")
    la.set_defaults(func=cmd_list_authors)

    # update-author
    ua = sub.add_parser("update-author", help="edit an author's fields")
    ua.add_argument("name", help="current name of the author to update")
    ua.add_argument("--name", dest="new_name", help="rename the author")
    ua.add_argument("--country")
    ua.add_argument("--dob")
    ua.add_argument("--add-award", action="append", metavar="AWARD")
    ua.add_argument("--remove-award", action="append", metavar="AWARD")
    ua.set_defaults(func=cmd_update_author)

    # remove-author
    ra = sub.add_parser("remove-author", help="delete an author (blocked if books exist)")
    ra.add_argument("name")
    ra.set_defaults(func=cmd_remove_author)

    # view-author
    va = sub.add_parser("view-author", help="show author profile and their books")
    va.add_argument("name")
    va.set_defaults(func=cmd_view_author)

    # add-book
    ab = sub.add_parser("add-book", help="add a new book")
    ab.add_argument("--title", required=True)
    ab.add_argument("--isbn", required=True)
    ab.add_argument("--pages", required=True, type=int)
    ab.add_argument("--year", required=True, type=int)
    ab.add_argument("--genre", required=True)
    ab.add_argument("--publisher", required=True)
    ab.add_argument("--author-id", required=True, dest="author_id")
    ab.set_defaults(func=cmd_add_book)

    # remove-book
    rb = sub.add_parser("remove-book", help="delete a book by ISBN")
    rb.add_argument("isbn")
    rb.set_defaults(func=cmd_remove_book)

    # view-book
    vb = sub.add_parser("view-book", help="show full book details")
    vb.add_argument("isbn")
    vb.set_defaults(func=cmd_view_book)

    # update-book
    ub = sub.add_parser("update-book", help="edit a book's fields")
    ub.add_argument("isbn")
    ub.add_argument("--title")
    ub.add_argument("--author-id", dest="author_id")
    ub.add_argument("--pages", type=int)
    ub.add_argument("--year", type=int)
    ub.add_argument("--genre")
    ub.add_argument("--publisher")
    ub.set_defaults(func=cmd_update_book)

    # lend-book
    lb = sub.add_parser("lend-book", help="lend a book to someone")
    lb.add_argument("isbn")
    lb.add_argument("--borrower", required=True)
    lb.add_argument("--due-date", required=True, dest="due_date", help="YYYY-MM-DD")
    lb.set_defaults(func=cmd_lend_book)

    # return-book
    ret = sub.add_parser("return-book", help="mark a lent book as returned")
    ret.add_argument("isbn")
    ret.set_defaults(func=cmd_return_book)

    # list-lent
    ll = sub.add_parser("list-lent", help="show all currently lent books")
    ll.set_defaults(func=cmd_list_lent)

    # overdue
    od = sub.add_parser("overdue", help="show lent books past their due date")
    od.set_defaults(func=cmd_overdue)

    # stats
    st = sub.add_parser("stats", help="collection statistics")
    st.set_defaults(func=cmd_stats)

    # help
    hp = sub.add_parser("help", help="list all commands")
    hp.set_defaults(func=cmd_help)

    # find-isbn
    fi = sub.add_parser("find-isbn", help="look up a book by ISBN")
    fi.add_argument("isbn")
    fi.set_defaults(func=cmd_find_isbn)

    # find-author
    fa = sub.add_parser("find-author", help="list all books by an author")
    fa.add_argument("name")
    fa.set_defaults(func=cmd_find_author)

    # filter-books
    fb = sub.add_parser("filter-books", help="filter books by genre, year range, or status")
    fb.add_argument("--genre")
    fb.add_argument("--status", choices=["available", "lent"])
    fb.add_argument("--after", type=int, metavar="YEAR")
    fb.add_argument("--before", type=int, metavar="YEAR")
    fb.set_defaults(func=cmd_filter_books)

    # list-books
    lb2 = sub.add_parser("list-books", help="list all books with optional sort")
    lb2.add_argument("--sort", choices=["title", "year", "author"], default="title")
    lb2.set_defaults(func=cmd_list_books)

    return p


def main():
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
