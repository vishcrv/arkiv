import { useState, useEffect } from "react";
import { useParams, Link } from "react-router-dom";
import { Star, BookOpen, User, Award } from "lucide-react";
import { authorsApi, ApiError } from "@/lib/api";
import { Loading, ErrorBox } from "@/components/states";

function BookCover({ url, title }) {
  const [err, setErr] = useState(false);
  if (!url || err) {
    return (
      <div className="flex h-16 w-11 items-center justify-center rounded-md bg-muted">
        <BookOpen className="h-4 w-4 text-muted-foreground/40" />
      </div>
    );
  }
  return (
    <img src={url} alt={title} className="h-16 w-11 rounded-md object-cover"
      onError={() => setErr(true)} />
  );
}

function OwnedBookRow({ book }) {
  return (
    <Link to={`/book/${book.isbn}`}
      className="flex items-center gap-4 rounded-lg p-2 transition-colors hover:bg-muted/50">
      <BookCover url={book.cover_url} title={book.title} />
      <div className="flex flex-1 flex-col gap-0.5 min-w-0">
        <span className="truncate text-sm font-medium text-foreground">{book.title}</span>
        {book.genres?.length > 0 && (
          <span className="text-xs text-muted-foreground">{book.genres.slice(0, 2).join(", ")}</span>
        )}
      </div>
      <div className="flex shrink-0 items-center gap-0.5">
        {[1, 2, 3, 4, 5].map((star) => (
          <Star key={star} className={`h-3.5 w-3.5 ${star <= (book.rating || 0) ? "fill-amber-400 text-amber-400" : "text-muted-foreground/30"}`} />
        ))}
      </div>
    </Link>
  );
}

export default function AuthorDetail() {
  const { id } = useParams();
  const [author, setAuthor]   = useState(null);
  const [notFound, setNotFound] = useState(false);
  const [error, setError]     = useState(null);

  function load() {
    setError(null);
    setNotFound(false);
    authorsApi.get(id)
      .then(setAuthor)
      .catch((err) => {
        if (err instanceof ApiError && err.status === 404) setNotFound(true);
        else setError(err.message);
      });
  }

  useEffect(load, [id]);

  if (notFound) {
    return (
      <div className="mx-auto flex w-full max-w-3xl flex-1 flex-col items-center justify-center px-6 py-24 text-center">
        <User className="mb-4 h-10 w-10 text-muted-foreground/40" />
        <p className="font-heading text-base font-medium">author not found</p>
        <p className="mt-1 text-sm text-muted-foreground">ID: {id}</p>
      </div>
    );
  }

  if (error) return <div className="mx-auto w-full max-w-3xl px-4 py-8 sm:px-6"><ErrorBox message={error} onRetry={load} /></div>;
  if (!author) return <Loading />;

  const ownedBooks = author.books || [];
  const avgRating = ownedBooks.filter((b) => b.rating).length > 0
    ? (ownedBooks.reduce((s, b) => s + (b.rating || 0), 0) / ownedBooks.filter((b) => b.rating).length).toFixed(1)
    : null;

  return (
    <div className="mx-auto flex w-full max-w-3xl flex-1 flex-col gap-8 px-4 py-6 sm:px-6 sm:py-8">
      {/* Author Header */}
      <div className="flex items-start gap-4">
        <div className="flex h-16 w-16 shrink-0 items-center justify-center rounded-full bg-primary/10">
          <span className="font-heading text-xl font-semibold text-primary">
            {author.name[0]?.toUpperCase()}
          </span>
        </div>
        <div className="flex flex-col gap-1">
          <h1 className="font-heading text-2xl font-bold text-foreground">{author.name}</h1>
          <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-sm text-muted-foreground">
            {author.country && <span>{author.country}</span>}
            {author.dob && <span>· b. {author.dob}</span>}
            {ownedBooks.length > 0 && <span>· {ownedBooks.length} book{ownedBooks.length !== 1 ? "s" : ""} in collection</span>}
            {avgRating && <span>· avg rating {avgRating} ★</span>}
          </div>
        </div>
      </div>

      {/* Awards */}
      {author.awards?.length > 0 && (
        <div className="rounded-xl border border-border bg-card p-5 shadow-sm dark:shadow-none">
          <div className="mb-3 flex items-center gap-2">
            <Award className="h-4 w-4 text-muted-foreground" />
            <h2 className="font-heading text-sm font-semibold text-foreground">awards</h2>
          </div>
          <div className="flex flex-wrap gap-2">
            {author.awards.map((award, i) => (
              <span key={i}
                className="rounded-full border border-border px-3 py-1 text-xs text-muted-foreground">
                {award}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Books in collection */}
      <div className="rounded-xl border border-border bg-card p-5 shadow-sm dark:shadow-none">
        <h2 className="mb-3 font-heading text-sm font-semibold text-foreground">in your collection</h2>
        {ownedBooks.length > 0 ? (
          <div className="flex flex-col gap-1">
            {ownedBooks.map((book) => <OwnedBookRow key={book.isbn} book={book} />)}
          </div>
        ) : (
          <p className="text-sm text-muted-foreground">no books by this author in your collection yet</p>
        )}
      </div>
    </div>
  );
}
