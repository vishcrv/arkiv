import { BookOpen, AlertTriangle, Search } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Link } from "react-router-dom";

// ─── Currently Reading Section ───
function CurrentlyReading() {
  // TODO: replace with real data
  const books = [];

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
          <div key={book.id} className="flex items-center gap-4">
            <div className="h-16 w-11 rounded-md bg-muted" />
            <div className="flex flex-1 flex-col gap-1">
              <span className="text-sm font-medium text-foreground">
                {book.title}
              </span>
              <span className="text-xs text-muted-foreground">
                {book.author}
              </span>
            </div>
            <Badge variant="secondary" className="text-xs">
              {book.progress}%
            </Badge>
          </div>
        ))}
      </div>
    </div>
  );
}

// ─── Alerts Section ───
function Alerts() {
  // TODO: replace with real data
  const overdue = [];

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
            key={item.id}
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
function FilterBar() {
  const sorts = ["recent", "a-z", "genre", "rating", "author"];

  return (
    <div className="flex items-center justify-between">
      {/* Library / Wishlist Toggle */}
      <div className="flex items-center gap-1 rounded-full border border-border bg-card p-1">
        <button className="rounded-full bg-primary px-4 py-1.5 text-xs font-medium text-primary-foreground transition-colors">
          library
        </button>
        <button className="rounded-full px-4 py-1.5 text-xs font-medium text-muted-foreground transition-colors hover:text-foreground">
          wishlist
        </button>
      </div>

      {/* Sort Pills */}
      <div className="flex items-center gap-1">
        <span className="mr-2 text-xs text-muted-foreground">sort:</span>
        {sorts.map((sort) => (
          <button
            key={sort}
            className={`rounded-full px-3 py-1.5 text-xs font-medium transition-colors ${
              sort === "recent"
                ? "bg-primary/10 text-primary"
                : "text-muted-foreground hover:text-foreground"
            }`}
          >
            {sort}
          </button>
        ))}
      </div>
    </div>
  );
}

// ─── Library Grid ───
function LibraryGrid() {
  // TODO: replace with real data
  const books = [];

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
          key={book.id}
          to={`/book/${book.id}`}
          className="group flex flex-col gap-2"
        >
          <div className="aspect-[2/3] overflow-hidden rounded-lg bg-muted shadow-sm transition-shadow group-hover:shadow-md" />
          <div className="flex flex-col gap-0.5 px-0.5">
            <span className="line-clamp-1 text-sm font-medium text-foreground">
              {book.title}
            </span>
            <span className="line-clamp-1 text-xs text-muted-foreground">
              {book.author}
            </span>
          </div>
        </Link>
      ))}
    </div>
  );
}

// ─── Home Page ───
export default function Home() {
  return (
    <div className="mx-auto flex w-full max-w-6xl flex-1 flex-col gap-8 px-6 py-8">
      {/* Top Row: Currently Reading + Alerts */}
      <div className="flex gap-5">
        <div className="flex w-[60%]">
          <CurrentlyReading />
        </div>
        <div className="flex w-[40%]">
          <Alerts />
        </div>
      </div>

      {/* Filter Bar */}
      <FilterBar />

      {/* Library Grid */}
      <LibraryGrid />
    </div>
  );
}
