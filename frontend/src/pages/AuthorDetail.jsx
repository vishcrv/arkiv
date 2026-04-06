import { useParams, Link } from "react-router-dom";
import { useState } from "react";
import { Star, Plus, Check, BookOpen, User } from "lucide-react";
import { Button } from "@/components/ui/button";

function OwnedBookRow({ book }) {
  return (
    <Link
      to={`/book/${book.isbn}`}
      className="flex items-center gap-4 rounded-lg p-2 transition-colors hover:bg-muted/50"
    >
      {book.cover ? (
        <img
          src={book.cover}
          alt={book.title}
          className="h-16 w-11 rounded-md object-cover"
        />
      ) : (
        <div className="flex h-16 w-11 items-center justify-center rounded-md bg-muted">
          <BookOpen className="h-4 w-4 text-muted-foreground/40" />
        </div>
      )}
      <span className="flex-1 text-sm font-medium text-foreground">
        {book.title}
      </span>
      <div className="flex items-center gap-0.5">
        {[1, 2, 3, 4, 5].map((star) => (
          <Star
            key={star}
            className={`h-3.5 w-3.5 ${
              star <= (book.rating || 0)
                ? "fill-amber-400 text-amber-400"
                : "text-muted-foreground/30"
            }`}
          />
        ))}
      </div>
    </Link>
  );
}

function OtherBookRow({ book }) {
  const [added, setAdded] = useState(false);

  return (
    <div className="flex items-center gap-4 rounded-lg p-2">
      <Link to={`/book/${book.isbn}`} className="shrink-0">
        {book.cover ? (
          <img
            src={book.cover}
            alt={book.title}
            className="h-16 w-11 rounded-md object-cover"
          />
        ) : (
          <div className="flex h-16 w-11 items-center justify-center rounded-md bg-muted">
            <BookOpen className="h-4 w-4 text-muted-foreground/40" />
          </div>
        )}
      </Link>
      <div className="flex flex-1 flex-col gap-0.5">
        <Link
          to={`/book/${book.isbn}`}
          className="text-sm font-medium text-foreground hover:underline"
        >
          {book.title}
        </Link>
        <span className="text-xs text-muted-foreground">
          {book.year && `${book.year}`}
          {book.pages && ` · ${book.pages} pages`}
        </span>
      </div>
      <Button
        variant={added ? "secondary" : "outline"}
        size="icon-sm"
        onClick={() => setAdded(true)}
        disabled={added}
      >
        {added ? (
          <Check className="h-3.5 w-3.5 text-primary" />
        ) : (
          <Plus className="h-3.5 w-3.5" />
        )}
      </Button>
    </div>
  );
}

export default function AuthorDetail() {
  const { id } = useParams();

  // TODO: load author data from store + OpenLibrary API
  const author = null;
  const ownedBooks = [];
  const otherBooks = [];

  if (!author) {
    return (
      <div className="mx-auto flex w-full max-w-3xl flex-1 flex-col items-center justify-center px-6 py-24 text-center">
        <User className="mb-4 h-10 w-10 text-muted-foreground/40" />
        <p className="font-heading text-base font-medium text-foreground">
          author not found
        </p>
        <p className="mt-1 text-sm text-muted-foreground">
          ID: {id}
        </p>
      </div>
    );
  }

  return (
    <div className="mx-auto flex w-full max-w-3xl flex-1 flex-col gap-8 px-6 py-8">
      {/* Author Header */}
      <div className="flex flex-col gap-1">
        <h1 className="font-heading text-2xl font-bold text-foreground">
          {author.name}
        </h1>
        <div className="flex flex-wrap items-center gap-2 text-sm text-muted-foreground">
          {author.country && <span>{author.country}</span>}
          {author.birthYear && <span>· Born: {author.birthYear}</span>}
        </div>
        {author.awards && author.awards.length > 0 && (
          <span className="text-sm text-muted-foreground">
            Awards: {author.awards.join(", ")}
          </span>
        )}
      </div>

      {/* Books in Your Collection */}
      {ownedBooks.length > 0 && (
        <div className="rounded-xl border border-border bg-card p-5 shadow-[0_1px_3px_0_rgba(44,37,32,0.04),0_0_0_1px_rgba(44,37,32,0.02)] dark:shadow-none">
          <h2 className="mb-3 font-heading text-sm font-semibold text-foreground">
            in your collection
          </h2>
          <div className="flex flex-col gap-1">
            {ownedBooks.map((book) => (
              <OwnedBookRow key={book.isbn} book={book} />
            ))}
          </div>
        </div>
      )}

      {/* Other Books */}
      {otherBooks.length > 0 && (
        <div className="rounded-xl border border-border bg-card p-5 shadow-[0_1px_3px_0_rgba(44,37,32,0.04),0_0_0_1px_rgba(44,37,32,0.02)] dark:shadow-none">
          <h2 className="mb-3 font-heading text-sm font-semibold text-foreground">
            other books by this author
          </h2>
          <div className="flex flex-col gap-1">
            {otherBooks.map((book) => (
              <OtherBookRow key={book.isbn} book={book} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
