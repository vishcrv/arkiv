import argparse
import json
import sys

import store


# --- helpers ---

def find_author_by_name(db, name):
    name_lower = name.lower()
    matches = [(aid, a) for aid, a in db["authors"].items()
               if a["name"].lower() == name_lower]
    if len(matches) == 1:
        return matches[0]
    return None, None


# --- commands ---

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


# --- parser ---

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="arkiv", description="book collection manager")
    sub = p.add_subparsers(dest="cmd", required=True)

    # dump — handy while building out the rest
    d = sub.add_parser("dump", help="print store contents")
    d.add_argument("what", nargs="?", default="all", choices=["all", "authors", "books"])
    d.set_defaults(func=cmd_dump)

    # add-author
    aa = sub.add_parser("add-author", help="add a new author")
    aa.add_argument("--name", required=True)
    aa.add_argument("--country", required=True)
    aa.add_argument("--dob", required=True, help="date of birth (YYYY-MM-DD)")
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

    return p


def main():
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
