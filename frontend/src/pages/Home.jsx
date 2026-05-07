import { useState, useEffect, useCallback } from "react";
import { BookOpen, AlertTriangle, Search, Plus, X } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { booksApi, wishlistApi } from "@/lib/api";
import { Loading, ErrorBox } from "@/components/states";
import { useAuth } from "@/lib/auth";

const SORT_API = {
  recent: "date_added",
  "a-z":  "title",
  "z-a":  "title-desc",
  rating: "rating",
  author: "author",
};

const STATUS_FILTERS = ["all", "reading", "read", "available", "lent", "sold"];

function greeting() {
  const h = new Date().getHours();
  if (h < 12) return "good morning";
  if (h < 17) return "good afternoon";
  return "good evening";
}

// ─── Default cover fallback ───
function BookCover({ coverUrl, title, className = "" }) {
  const [err, setErr] = useState(false);
  if (!coverUrl || err) {
    return (
      <div className={`flex items-center justify-center rounded-lg bg-muted shadow-sm ${className}`}>
        <BookOpen className="h-8 w-8 text-muted-foreground/30" />
      </div>
    );
  }
  return (
    <img
      src={coverUrl}
      alt={title}
      className={`rounded-lg object-cover shadow-sm ${className}`}
      onError={() => setErr(true)}
    />
  );
}

// ─── Currently Reading ───
function CurrentlyReading({ books }) {
  if (books.length === 0) {
    return (
      <div className="flex flex-1 flex-col items-center justify-center rounded-xl border border-border bg-card px-6 py-12 text-center shadow-sm dark:shadow-none">
        <BookOpen className="mb-3 h-8 w-8 text-muted-foreground/50" />
        <p className="font-heading text-sm font-medium text-foreground">nothing on the nightstand?</p>
        <p className="mt-1 text-xs text-muted-foreground">pick something from your library below</p>
      </div>
    );
  }
  return (
    <div className="flex flex-1 flex-col gap-3 rounded-xl border border-border bg-card p-5 shadow-sm dark:shadow-none">
      <h2 className="font-heading text-sm font-semibold text-foreground">currently reading</h2>
      <div className="flex flex-col gap-3">
        {books.map((book) => (
          <Link key={book.isbn} to={`/book/${book.isbn}`}
            className="flex items-center gap-4 rounded-lg transition-colors hover:bg-muted/50">
            <BookCover coverUrl={book.cover_url} title={book.title} className="h-16 w-11 shrink-0" />
            <div className="flex flex-1 flex-col gap-1 min-w-0">
              <span className="truncate text-sm font-medium text-foreground">{book.title}</span>
              <span className="text-xs text-muted-foreground">{book.author_name}</span>
            </div>
            <Badge variant="secondary" className="text-xs shrink-0">reading</Badge>
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
      <div className="flex flex-col items-center justify-center rounded-xl border border-border bg-card px-6 py-12 text-center shadow-sm dark:shadow-none">
        <AlertTriangle className="mb-3 h-8 w-8 text-muted-foreground/50" />
        <p className="font-heading text-sm font-medium text-foreground">all clear</p>
        <p className="mt-1 text-xs text-muted-foreground">lent books will show here when overdue</p>
      </div>
    );
  }
  return (
    <div className="flex flex-col gap-3 rounded-xl border border-border bg-card p-5 shadow-sm dark:shadow-none">
      <h2 className="font-heading text-sm font-semibold text-foreground">overdue</h2>
      <div className="flex flex-col gap-3">
        {overdue.map((item) => (
          <div key={item.isbn} className="flex items-center justify-between text-sm">
            <div className="flex flex-col">
              <span className="font-medium text-foreground">{item.title}</span>
              <span className="text-xs text-muted-foreground">lent to {item.borrower}</span>
            </div>
            <Badge variant="destructive" className="text-xs">{item.days}d overdue</Badge>
          </div>
        ))}
      </div>
    </div>
  );
}

// ─── Filter Bar ───
function FilterBar({ view, setView, sort, setSort, statusFilter, setStatusFilter }) {
  const sorts = ["recent", "a-z", "z-a", "rating", "author"];
  return (
    <div className="flex flex-col gap-3">
      <div className="flex flex-wrap items-center gap-3">
        <div className="flex items-center gap-1 rounded-full border border-border bg-card p-1">
          {["library", "wishlist"].map((v) => (
            <button key={v} onClick={() => setView(v)}
              className={`rounded-full px-4 py-1.5 text-xs font-medium transition-colors ${
                view === v ? "bg-primary text-primary-foreground" : "text-muted-foreground hover:text-foreground"
              }`}>
              {v}
            </button>
          ))}
        </div>
        <div className="flex flex-wrap items-center gap-1">
          <span className="mr-1 text-xs text-muted-foreground">sort:</span>
          {sorts.map((s) => (
            <button key={s} onClick={() => setSort(s)}
              className={`rounded-full px-3 py-1.5 text-xs font-medium transition-colors ${
                sort === s ? "bg-primary/10 text-primary" : "text-muted-foreground hover:text-foreground"
              }`}>
              {s}
            </button>
          ))}
        </div>
      </div>
      {view === "library" && (
        <div className="flex flex-wrap items-center gap-1">
          <span className="mr-1 text-xs text-muted-foreground">status:</span>
          {STATUS_FILTERS.map((s) => (
            <button key={s} onClick={() => setStatusFilter(s)}
              className={`rounded-full px-3 py-1.5 text-xs font-medium transition-colors ${
                statusFilter === s ? "bg-primary/10 text-primary" : "text-muted-foreground hover:text-foreground"
              }`}>
              {s}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

// ─── Library Grid ───
function LibraryGrid({ view, books, wishlist, onRemoveWishlist, onPromoteWishlist }) {
  if (view === "wishlist") {
    if (wishlist.length === 0) {
      return (
        <div className="flex flex-col items-center justify-center rounded-xl border border-dashed border-border py-24 text-center">
          <BookOpen className="mb-4 h-10 w-10 text-muted-foreground/40" />
          <p className="font-heading text-base font-medium text-foreground">wishlist is empty</p>
          <p className="mb-5 mt-1 text-sm text-muted-foreground">save books you want to read</p>
          <Link to="/discover"
            className="inline-flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/80">
            <Search className="h-4 w-4" /> discover books
          </Link>
        </div>
      );
    }
    return (
      <div className="grid grid-cols-2 gap-5 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6">
        {wishlist.map((item) => (
          <div key={item.isbn} className="flex flex-col gap-2">
            <div className="group relative aspect-[2/3] w-full">
              <BookCover coverUrl={item.cover_url} title={item.title} className="h-full w-full" />
              <div className="absolute inset-0 flex items-center justify-center gap-2 rounded-lg bg-black/50 opacity-0 transition-opacity group-hover:opacity-100">
                <Button size="sm" variant="secondary" onClick={() => onPromoteWishlist(item)} title="add to library">
                  <Plus className="h-4 w-4" />
                </Button>
                <Button size="sm" variant="destructive" onClick={() => onRemoveWishlist(item.isbn)} title="remove">
                  <X className="h-4 w-4" />
                </Button>
              </div>
            </div>
            <div className="flex flex-col gap-0.5 px-0.5">
              <span className="line-clamp-1 text-sm font-medium text-foreground">{item.title}</span>
              <span className="line-clamp-1 text-xs text-muted-foreground">{item.author_name}</span>
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
        <p className="font-heading text-base font-medium text-foreground">your library is empty</p>
        <p className="mb-5 mt-1 text-sm text-muted-foreground">start by searching for your first book</p>
        <Link to="/discover"
          className="inline-flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/80">
          <Search className="h-4 w-4" /> search for your first book
        </Link>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-2 gap-5 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6">
      {books.map((book) => (
        <Link key={book.isbn} to={`/book/${book.isbn}`} className="group flex flex-col gap-2">
          <BookCover
            coverUrl={book.cover_url}
            title={book.title}
            className="aspect-[2/3] w-full transition-shadow group-hover:shadow-md"
          />
          <div className="flex flex-col gap-0.5 px-0.5">
            <span className="line-clamp-1 text-sm font-medium text-foreground">{book.title}</span>
            <span className="line-clamp-1 text-xs text-muted-foreground">{book.author_name}</span>
          </div>
        </Link>
      ))}
    </div>
  );
}

// ─── Home ───
export default function Home() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();

  const qParam = searchParams.get("q") || "";

  const [view, setView]               = useState("library");
  const [sort, setSort]               = useState("recent");
  const [statusFilter, setStatusFilter] = useState("all");
  const [books, setBooks]             = useState([]);
  const [wishlist, setWishlist]       = useState([]);
  const [loading, setLoading]         = useState(true);
  const [error, setError]             = useState(null);

  const fetchData = useCallback(() => {
    setLoading(true);
    setError(null);
    const params = { sort: SORT_API[sort] || "date_added" };
    if (statusFilter !== "all") params.status = statusFilter;
    if (qParam) params.q = qParam;

    Promise.all([booksApi.list(params), wishlistApi.list()])
      .then(([b, w]) => { setBooks(b); setWishlist(w); })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [sort, statusFilter, qParam]);

  useEffect(() => { fetchData(); }, [fetchData]);

  const today = new Date().toISOString().slice(0, 10);
  const readingBooks  = books.filter((b) => b.status === "reading");
  const overdueBooks  = books
    .filter((b) => b.status === "lent" && b.lending?.due_date < today)
    .map((b) => ({
      isbn: b.isbn, title: b.title, borrower: b.lending.borrower,
      days: Math.floor((Date.now() - new Date(b.lending.due_date).getTime()) / 86400000),
    }));

  async function handleRemoveWishlist(isbn) {
    try {
      await wishlistApi.remove(isbn);
      setWishlist((w) => w.filter((i) => i.isbn !== isbn));
    } catch (e) { setError(e.message); }
  }

  function handlePromoteWishlist(item) {
    navigate("/discover", { state: { prefill: item } });
  }

  function clearSearch() {
    setSearchParams({});
  }

  if (loading && books.length === 0) {
    return (
      <div className="mx-auto flex w-full max-w-6xl flex-1 flex-col px-4 py-6 sm:px-6 sm:py-8">
        <Loading />
      </div>
    );
  }

  if (error) {
    return (
      <div className="mx-auto flex w-full max-w-6xl flex-1 flex-col px-4 py-6 sm:px-6 sm:py-8">
        <ErrorBox message={error} onRetry={fetchData} />
      </div>
    );
  }

  return (
    <div className="mx-auto flex w-full max-w-6xl flex-1 flex-col gap-8 px-4 py-6 sm:px-6 sm:py-8">
      {/* Welcome banner */}
      {!qParam && (
        <div>
          <h1 className="font-heading text-2xl font-semibold text-foreground">
            {greeting()}{user?.username ? `, ${user.username}` : ""}
          </h1>
          <p className="mt-0.5 text-sm text-muted-foreground">
            {new Date().toLocaleDateString("en-US", { weekday: "long", month: "long", day: "numeric" })}
          </p>
        </div>
      )}

      {/* Search result banner */}
      {qParam && (
        <div className="flex items-center justify-between">
          <div>
            <h1 className="font-heading text-2xl font-semibold text-foreground">
              results for &ldquo;{qParam}&rdquo;
            </h1>
            <p className="mt-0.5 text-sm text-muted-foreground">{books.length} book{books.length !== 1 ? "s" : ""} found</p>
          </div>
          <button onClick={clearSearch}
            className="flex items-center gap-1.5 rounded-full px-3 py-1.5 text-xs font-medium text-muted-foreground hover:text-foreground hover:bg-muted transition-colors">
            <X className="h-3.5 w-3.5" /> clear search
          </button>
        </div>
      )}

      {/* Top row — only when not searching */}
      {!qParam && (
        <div className="flex flex-col gap-5 sm:flex-row">
          <div className="flex w-full sm:w-[60%]">
            <CurrentlyReading books={readingBooks} />
          </div>
          <div className="flex w-full sm:w-[40%]">
            <Alerts overdue={overdueBooks} />
          </div>
        </div>
      )}

      <FilterBar
        view={view} setView={setView}
        sort={sort} setSort={setSort}
        statusFilter={statusFilter} setStatusFilter={setStatusFilter}
      />

      <LibraryGrid
        view={view}
        books={books}
        wishlist={wishlist}
        onRemoveWishlist={handleRemoveWishlist}
        onPromoteWishlist={handlePromoteWishlist}
      />
    </div>
  );
}
