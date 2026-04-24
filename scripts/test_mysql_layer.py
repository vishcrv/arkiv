import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import store.mysql as store

db = store.load()
print("authors:", len(store.list_authors()))
print("books  :", len(store.list_books()))
print("sorted by year:", [b[1]["year"] for b in store.list_books(sort="year")[:5]])
print("stats  :", store.compute_stats(db))
print("profile:", store.get_profile(db))
print("activity (5):", store.list_activity(5))