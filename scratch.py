# scratch.py at project root
import store.sf as store

db = store.load()
print("connected ok")
print("books:", store.list_books())
print("stats:", store.compute_stats(db))