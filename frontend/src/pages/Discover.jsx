import { useState } from "react";
import { Link } from "react-router-dom";
import { Search, Plus, Check, BookOpen } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";

function SearchResult({ book }) {
  // TODO: check against real collection data
  const [added, setAdded] = useState(false);

  return (
    <div className="flex items-center gap-4 rounded-xl border border-border bg-card p-4 shadow-[0_1px_3px_0_rgba(44,37,32,0.04),0_0_0_1px_rgba(44,37,32,0.02)] dark:shadow-none transition-colors">
      <Link to={`/book/${book.isbn}`} className="shrink-0">
        {book.cover ? (
          <img
            src={book.cover}
            alt={book.title}
            className="h-24 w-16 rounded-md object-cover"
          />
        ) : (
          <div className="flex h-24 w-16 items-center justify-center rounded-md bg-muted">
            <BookOpen className="h-5 w-5 text-muted-foreground/40" />
          </div>
        )}
      </Link>

      <div className="flex flex-1 flex-col gap-1">
        <Link
          to={`/book/${book.isbn}`}
          className="text-sm font-medium text-foreground hover:underline"
        >
          {book.title}
        </Link>
        <span className="text-xs text-muted-foreground">
          {book.author}
          {book.year && ` · ${book.year}`}
          {book.pages && ` · ${book.pages} pages`}
        </span>
      </div>

      <Button
        variant={added ? "secondary" : "outline"}
        size="icon"
        onClick={() => setAdded(true)}
        disabled={added}
        className="shrink-0"
      >
        {added ? (
          <Check className="h-4 w-4 text-primary" />
        ) : (
          <Plus className="h-4 w-4" />
        )}
      </Button>
    </div>
  );
}

export default function Discover() {
  const [query, setQuery] = useState("");
  // TODO: replace with real OpenLibrary API search
  const results = [];

  return (
    <div className="mx-auto flex w-full max-w-3xl flex-1 flex-col gap-6 px-6 py-8">
      {/* Search Input */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
        <Input
          type="text"
          placeholder="search by title, author, or ISBN..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          className="h-10 pl-10 text-sm"
        />
      </div>

      {/* Results */}
      {query === "" ? (
        <div className="flex flex-col items-center justify-center py-24 text-center">
          <Search className="mb-4 h-10 w-10 text-muted-foreground/40" />
          <p className="font-heading text-base font-medium text-foreground">
            search for any book
          </p>
          <p className="mt-1 text-sm text-muted-foreground">
            we'll pull the details from OpenLibrary
          </p>
        </div>
      ) : results.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-24 text-center">
          <BookOpen className="mb-4 h-10 w-10 text-muted-foreground/40" />
          <p className="font-heading text-base font-medium text-foreground">
            nothing found
          </p>
          <p className="mt-1 text-sm text-muted-foreground">
            try a different title or ISBN
          </p>
        </div>
      ) : (
        <div className="flex flex-col gap-3">
          {results.map((book) => (
            <SearchResult key={book.isbn} book={book} />
          ))}
        </div>
      )}
    </div>
  );
}
