import { useState, useEffect } from "react";
import { BookOpen, AlertTriangle, Search } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Link } from "react-router-dom";
import { booksApi, wishlistApi } from "@/lib/api";

// ─── Currently Reading ───
function CurrentlyReading({ books }) {
  if (books.length === 0) {
    return (
      <div className="flex flex-1 flex-col items-center justify-center rounded-xl border border-border bg-card shadow-[0_1px_3px_0_rgba(44,37,32,0.04),0_0_0_1px_rgba(44,37,32,0.02)] dark:shadow-none px-6 py-12 text-center">
        <BookOpen className="mb-3 h-8 w-8 text-muted-foreground/50" />
        <p className="font-heading text-sm font-medium text-foreground">
          nothing on the nightstand?
        </p>
        <p className="mt-1 text-xs text-muted-foreground">
          pick something from your library below
        </p>
      </div>
    );
  }

  return (
    <div className="flex flex-1 flex-col gap-3 rounded-xl border border-border bg-card shadow-[0_1px_3px_0_rgba(44,37,32,0.04),0_0_0_1px_rgba(44,37,32,0.02)] dark:shadow-none p-5">
      <h2 className="font-heading text-sm font-semibold text-foreground">
        currently reading
      </h2>
      <div className="flex flex-col gap-3">
        {books.map((book) => (
          <Link
            key={book.isbn}
            to={`/book/${book.isbn}`}
            className="flex items-center gap-4 rounded-lg transition-colors hover:bg-muted/50"
          >
            {book.cover_url ? (
              <img
                src={book.cover_url}
                alt={book.title}
                className="h-16 w-11 rounded-md object-cover"
                onError={(e) => { e.currentTarget.style.display = "none"; }}
              />
            ) : (
              <div className="h-16 w-11 rounded-md bg-muted" />
            )}
            <div className="flex flex-1 flex-col gap-1">
              <span className="text-sm font-medium text-foreground">
                {book.title}
              </span>
              <span className="text-xs text-muted-foreground">
                {book.author_name}
              </span>
            </div>
            <Badge variant="secondary" className="text-xs">
              reading
            </Badge>
          </Link>
        ))}
      </div>
    </div>
  );
}

// ─── Alerts ───
function Alerts({ overdue }) {
  if (overdue.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center rounded-xl border border-border bg-card shadow-[0_1px_3px_0_rgba(44,37,32,0.04),0_0_0_1px_rgba(44,37,32,0.02)] dark:shadow-none px-6 py-12 text-center">
        <AlertTriangle className="mb-3 h-8 w-8 text-muted-foreground/50" />
        <p className="font-heading text-sm font-medium text-foreground">
          all clear, nobody owes you
        </p>
        <p className="mt-1 text-xs text-muted-foreground">
          lent books will show up here when overdue
        </p>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-3 rounded-xl border border-border bg-card shadow-[0_1px_3px_0_rgba(44,37,32,0.04),0_0_0_1px_rgba(44,37,32,0.02)] dark:shadow-none p-5">
      <h2 className="font-heading text-sm font-semibold text-foreground">
        overdue
      </h2>
      <div className="flex flex-col gap-3">
        {overdue.map((item) => (
          <div
            key={item.isbn}
            className="flex items-center justify-between text-sm"
          >
            <div className="flex flex-col">
              <span className="font-medium text-foreground">{item.title}</span>
              <span className="text-xs text-muted-foreground">
                lent to {item.borrower}
              </span>
            </div>
            <Badge variant="destructive" className="text-xs">
              {item.days}d overdue
            </Badge>
          </div>
        ))}
      </div>
    </div>
  );
}

// ─── Filter Bar ───
function FilterBar({ view, setView, sort, setSort }) {
  const sorts = ["recent", "a-z", "genre", "rating", "author"];

  return (
    <div className="flex items-center justify-between">
      <div className="flex items-center gap-1 rounded-full border border-border bg-card p-1">
        <button
          onClick={() => setView("library")}
          className={`rounded-full px-4 py-1.5 text-xs font-medium transition-colors ${
            view === "library"
              ? "bg-primary text-primary-foreground"
              : "text-muted-foreground hover:text-foreground"
          }`}
        >
          library
        </button>
        <button
          onClick={() => setView("wishlist")}
          className={`rounded-full px-4 py-1.5 text-xs font-medium transition-colors ${
            view === "wishlist"
              ? "bg-primary text-primary-foreground"
              : "text-muted-foreground hover:text-foreground"
          }`}
        >
          wishlist
        </button>
      </div>

      <div className="flex items-center gap-1">
        <span className="mr-2 text-xs text-muted-foreground">sort:</span>
        {sorts.map((s) => (
          <button
            key={s}
            onClick={() => setSort(s)}
            className={`rounded-full px-3 py-1.5 text-xs font-medium transition-colors ${
              sort === s
                ? "bg-primary/10 text-primary"
                : "text-muted-foreground hover:text-foreground"
            }`}
          >
            {s}
          </button>
        ))}
      </div>
    </div>
  );
}

// ─── Library Grid ───
function LibraryGrid({ view, books, wishlist }) {
  if (view === "wishlist") {
    if (wishlist.length === 0) {
      return (
        <div className="flex flex-col items-center justify-center rounded-xl border border-dashed border-border py-24 text-center">
          <BookOpen className="mb-4 h-10 w-10 text-muted-foreground/40" />
          <p className="font-heading text-base font-medium text-foreground">
            wishlist is empty
          </p>
          <p className="mb-5 mt-1 text-sm text-muted-foreground">
            save books you want to read
          </p>
          <Link
            to="/discover"
            className="inline-flex items-center justify-center rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/80"
          >
            <Search className="mr-2 h-4 w-4" />
            discover books
          </Link>
        </div>
      );
    }

    return (
      <div className="grid grid-cols-2 gap-5 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6">
        {wishlist.map((item) => (
          <div key={item.isbn} className="flex flex-col gap-2">
            {item.cover_url ? (
              <img
                src={item.cover_url}
                alt={item.title}
                className="aspect-[2/3] w-full rounded-lg object-cover shadow-sm"
                onError={(e) => { e.currentTarget.style.display = "none"; }}
              />
            ) : (
              <div className="aspect-[2/3] overflow-hidden rounded-lg bg-muted shadow-sm" />
            )}
            <div className="flex flex-col gap-0.5 px-0.5">
              <span className="line-clamp-1 text-sm font-medium text-foreground">
                {item.title}
              </span>
              <span className="line-clamp-1 text-xs text-muted-foreground">
                {item.author_name}
              </span>
            </div>
          </div>
        ))}
      </div>
    );
  }

  if (books.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center rounded-xl border border-dashed border-border py-24 text-center">
        <BookOpen className="mb-4 h-10 w-10 text-muted-foreground/40" />
        <p className="font-heading text-base font-medium text-foreground">
          your library is empty
        </p>
        <p className="mb-5 mt-1 text-sm text-muted-foreground">
          start by searching for your first book
        </p>
        <Link
          to="/discover"
          className="inline-flex items-center justify-center rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/80"
        >
          <Search className="mr-2 h-4 w-4" />
          search for your first book
        </Link>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-2 gap-5 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6">
      {books.map((book) => (
        <Link
          key={book.isbn}
          to={`/book/${book.isbn}`}
          className="group flex flex-col gap-2"
        >
          {book.cover_url ? (
            <img
              src={book.cover_url}
              alt={book.title}
              className="aspect-[2/3] w-full rounded-lg object-cover shadow-sm transition-shadow group-hover:shadow-md"
              onError={(e) => { e.currentTarget.style.display = "none"; }}
            />
          ) : (
            <div className="aspect-[2/3] overflow-hidden rounded-lg bg-muted shadow-sm transition-shadow group-hover:shadow-md" />
          )}
          <div className="flex flex-col gap-0.5 px-0.5">
            <span className="line-clamp-1 text-sm font-medium text-foreground">
              {book.title}
            </span>
            <span className="line-clamp-1 text-xs text-muted-foreground">
              {book.author_name}
            </span>
          </div>
        </Link>
      ))}
    </div>
  );
}

// ─── Home Page ───
export default function Home() {
  const [view, setView] = useState("library");
  const [sort, setSort] = useState("recent");
  const [books, setBooks] = useState([]);
  const [wishlist, setWishlist] = useState([]);

  useEffect(() => {
    booksApi.list().then(setBooks).catch(console.error);
    wishlistApi.list().then(setWishlist).catch(console.error);
  }, []);

  const readingBooks = books.filter((b) => b.status === "reading");

  const today = new Date().toISOString().slice(0, 10);
  const overdueBooks = books
    .filter((b) => b.status === "lent" && b.lending?.due_date < today)
    .map((b) => ({
      isbn: b.isbn,
      title: b.title,
      borrower: b.lending.borrower,
      days: Math.floor(
        (Date.now() - new Date(b.lending.due_date).getTime()) / 86400000
      ),
    }));

  const sortedBooks = [...books].sort((a, b) => {
    switch (sort) {
      case "a-z":    return a.title.localeCompare(b.title);
      case "genre":  return (a.genre || "").localeCompare(b.genre || "");
      case "rating": return (b.rating || 0) - (a.rating || 0);
      case "author": return (a.author_name || "").localeCompare(b.author_name || "");
      default:       return (b.date_added || "").localeCompare(a.date_added || "");
    }
  });

  return (
    <div className="mx-auto flex w-full max-w-6xl flex-1 flex-col gap-8 px-6 py-8">
      <div className="flex gap-5">
        <div className="flex w-[60%]">
          <CurrentlyReading books={readingBooks} />
        </div>
        <div className="flex w-[40%]">
          <Alerts overdue={overdueBooks} />
        </div>
      </div>

      <FilterBar view={view} setView={setView} sort={sort} setSort={setSort} />

      <LibraryGrid view={view} books={sortedBooks} wishlist={wishlist} />
    </div>
  );
}
