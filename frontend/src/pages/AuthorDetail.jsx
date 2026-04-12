import { useState, useEffect } from "react";
import { useParams, Link } from "react-router-dom";
import { Star, BookOpen, User } from "lucide-react";

function OwnedBookRow({ book }) {
  return (
    <Link
      to={`/book/${book.isbn}`}
      className="flex items-center gap-4 rounded-lg p-2 transition-colors hover:bg-muted/50"
    >
      <div className="flex h-16 w-11 items-center justify-center rounded-md bg-muted">
        <BookOpen className="h-4 w-4 text-muted-foreground/40" />
      </div>
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

export default function AuthorDetail() {
  const { id } = useParams();
  const [author, setAuthor] = useState(null);
  const [notFound, setNotFound] = useState(false);

  useEffect(() => {
    fetch(`/api/authors/${id}`)
      .then((r) => {
        if (r.status === 404) { setNotFound(true); return null; }
        return r.json();
      })
      .then((data) => { if (data) setAuthor(data); })
      .catch(console.error);
  }, [id]);

  if (notFound) {
    return (
      <div className="mx-auto flex w-full max-w-3xl flex-1 flex-col items-center justify-center px-6 py-24 text-center">
        <User className="mb-4 h-10 w-10 text-muted-foreground/40" />
        <p className="font-heading text-base font-medium text-foreground">
          author not found
        </p>
        <p className="mt-1 text-sm text-muted-foreground">ID: {id}</p>
      </div>
    );
  }

  if (!author) return null;

  const ownedBooks = author.books || [];

  return (
    <div className="mx-auto flex w-full max-w-3xl flex-1 flex-col gap-8 px-6 py-8">
      {/* Author Header */}
      <div className="flex flex-col gap-1">
        <h1 className="font-heading text-2xl font-bold text-foreground">
          {author.name}
        </h1>
        <div className="flex flex-wrap items-center gap-2 text-sm text-muted-foreground">
          {author.country && <span>{author.country}</span>}
          {author.dob && <span>· Born: {author.dob}</span>}
        </div>
        {author.awards?.length > 0 && (
          <span className="text-sm text-muted-foreground">
            Awards: {author.awards.join(", ")}
          </span>
        )}
      </div>

      {/* Books in collection */}
      {ownedBooks.length > 0 ? (
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
      ) : (
        <div className="rounded-xl border border-border bg-card p-5 shadow-[0_1px_3px_0_rgba(44,37,32,0.04),0_0_0_1px_rgba(44,37,32,0.02)] dark:shadow-none">
          <p className="text-sm text-muted-foreground">
            no books by this author in your collection
          </p>
        </div>
      )}

      {/* Other books — OpenLibrary phase */}
    </div>
  );
}
