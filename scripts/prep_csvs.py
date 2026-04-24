"""One-shot CSV transform: SF raw exports → MySQL-ready CSVs.

Run: python scripts/prep_csvs.py
Reads:  migration/sf_raw/{authors,books,wishlist,activity}.csv
Writes: migration/mysql_ready/{authors,books,wishlist,activity}.csv
        migration/mysql_ready/author_id_map.csv
"""
import csv
import json
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "migration" / "sf_raw"
DST = ROOT / "migration" / "mysql_ready"
DST.mkdir(parents=True, exist_ok=True)


def sf_date(s: str) -> str:
    """SF gives YYYY-MM-DD already for Date fields. Keep as-is; blank stays blank."""
    return (s or "").strip()


def sf_datetime(s: str) -> str:
    """SF datetime like '2024-01-15T10:30:00.000+0000' → '2024-01-15 10:30:00.000000' for MySQL DATETIME(6)."""
    s = (s or "").strip()
    if not s:
        return ""
    # Strip timezone suffix, replace T with space, pad/truncate fractional to 6 digits
    core = s.split("+")[0].split("Z")[0].replace("T", " ")
    if "." in core:
        base, frac = core.split(".")
        frac = (frac + "000000")[:6]
        return f"{base}.{frac}"
    return f"{core}.000000"


def awards_to_json(s: str) -> str:
    """SF Awards__c is a comma-separated string; MySQL wants a JSON array."""
    if not s or not s.strip():
        return "[]"
    items = [a.strip() for a in s.split(",") if a.strip()]
    return json.dumps(items, ensure_ascii=False)


# ── authors ──────────────────────────────────────────────────────────────────
id_map: dict[str, str] = {}  # SF Id → author_<uuid8>

with open(SRC / "authors.csv", newline="", encoding="cp1252") as f_in, \
     open(DST / "authors.csv", "w", newline="", encoding="utf-8") as f_out:
    reader = csv.DictReader(f_in)
    writer = csv.writer(f_out)
    writer.writerow(["author_id", "name", "country", "dob", "awards"])
    for row in reader:
        sf_id = row["Id"]
        new_id = f"author_{uuid.uuid4().hex[:8]}"
        id_map[sf_id] = new_id
        writer.writerow([
            new_id,
            row.get("Name", ""),
            row.get("Country__c", "") or "",
            sf_date(row.get("DOB__c", "")),
            awards_to_json(row.get("Awards__c", "")),
        ])

# Save mapping so you can audit later
with open(DST / "author_id_map.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["sf_id", "author_id"])
    for k, v in id_map.items():
        w.writerow([k, v])

print(f"authors: {len(id_map)} rows")

# ── books ────────────────────────────────────────────────────────────────────
book_count = 0
with open(SRC / "books.csv", newline="", encoding="cp1252") as f_in, \
     open(DST / "books.csv", "w", newline="", encoding="utf-8") as f_out:
    reader = csv.DictReader(f_in)
    writer = csv.writer(f_out)
    writer.writerow([
        "isbn", "title", "author_id", "pages", "year", "genre", "publisher",
        "status", "format", "description", "rating", "thoughts",
        "date_added", "date_read", "sale_price", "sale_date", "cover_url",
        "borrower", "due_date",
    ])
    for row in reader:
        sf_author_id = row.get("Author__c", "")
        new_author_id = id_map.get(sf_author_id)
        if not new_author_id:
            raise SystemExit(f"Book {row.get('ISBN__c')} references unknown author {sf_author_id!r}")
        writer.writerow([
            row.get("ISBN__c", ""),
            row.get("Name", ""),
            new_author_id,
            row.get("Pages__c", "") or "0",
            row.get("Year__c", "") or "0",
            row.get("Genre__c", "") or "",
            row.get("Publisher__c", "") or "",
            row.get("Status__c", "") or "available",
            row.get("Format__c", "") or "paperback",
            row.get("Description__c", "") or "",
            row.get("Rating__c", ""),       # blank → NULL
            row.get("Thoughts__c", "") or "",
            sf_date(row.get("Date_Added__c", "")) or "",
            sf_date(row.get("Date_Read__c", "")),
            row.get("Sale_Price__c", ""),    # blank → NULL
            sf_date(row.get("Sale_Date__c", "")),
            row.get("Cover_URL__c", "") or "",
            row.get("Borrower__c", "") or "",
            sf_date(row.get("Due_Date__c", "")),
        ])
        book_count += 1
print(f"books: {book_count} rows")

# ── wishlist ─────────────────────────────────────────────────────────────────
wl_count = 0
with open(SRC / "wishlist.csv", newline="", encoding="cp1252") as f_in, \
     open(DST / "wishlist.csv", "w", newline="", encoding="utf-8") as f_out:
    reader = csv.DictReader(f_in)
    writer = csv.writer(f_out)
    writer.writerow(["isbn", "title", "author_name", "year", "genre"])
    for row in reader:
        writer.writerow([
            row.get("ISBN__c", ""),
            row.get("Name", ""),
            row.get("Author_Name__c", "") or "",
            row.get("Year__c", "") or "0",
            row.get("Genre__c", "") or "",
        ])
        wl_count += 1
print(f"wishlist: {wl_count} rows")

# ── activity ─────────────────────────────────────────────────────────────────
ac_count = 0
with open(SRC / "activity.csv", newline="", encoding="cp1252") as f_in, \
     open(DST / "activity.csv", "w", newline="", encoding="utf-8") as f_out:
    reader = csv.DictReader(f_in)
    writer = csv.writer(f_out)
    writer.writerow(["action", "isbn", "detail", "timestamp"])
    for row in reader:
        writer.writerow([
            row.get("Action__c", ""),
            row.get("ISBN__c", "") or "",
            row.get("Detail__c", "") or "",
            sf_datetime(row.get("Timestamp__c", "")),
        ])
        ac_count += 1
print(f"activity: {ac_count} rows")

print("\nDone. Files in migration/mysql_ready/")