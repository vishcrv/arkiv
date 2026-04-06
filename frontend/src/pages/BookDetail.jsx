import { useState } from "react";
import { useParams, Link } from "react-router-dom";
import { Star, BookOpen, ChevronDown, Plus, Check, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";

// ─── Star Rating ───
function StarRating({ rating, onRate }) {
  const [hover, setHover] = useState(0);

  return (
    <div className="flex items-center gap-1">
      {[1, 2, 3, 4, 5].map((star) => (
        <button
          key={star}
          onClick={() => onRate(star)}
          onMouseEnter={() => setHover(star)}
          onMouseLeave={() => setHover(0)}
          className="text-lg transition-colors"
        >
          <Star
            className={`h-5 w-5 ${
              star <= (hover || rating)
                ? "fill-amber-400 text-amber-400"
                : "text-muted-foreground/30"
            }`}
          />
        </button>
      ))}
    </div>
  );
}

// ─── Discovery Mode (don't own book) ───
function DiscoveryMode({ book }) {
  const [wishlisted, setWishlisted] = useState(false);

  return (
    <div className="mx-auto flex w-full max-w-3xl flex-1 flex-col gap-8 px-6 py-8">
      {/* Book Header */}
      <div className="flex gap-6">
        {book.cover ? (
          <img
            src={book.cover}
            alt={book.title}
            className="h-56 w-36 shrink-0 rounded-lg object-cover shadow-md"
          />
        ) : (
          <div className="flex h-56 w-36 shrink-0 items-center justify-center rounded-lg bg-muted shadow-md">
            <BookOpen className="h-8 w-8 text-muted-foreground/40" />
          </div>
        )}

        <div className="flex flex-col gap-2">
          <h1 className="font-heading text-2xl font-bold text-foreground">
            {book.title}
          </h1>
          <Link
            to={`/author/${book.authorId}`}
            className="text-sm font-medium text-primary hover:underline"
          >
            {book.author}
          </Link>

          <div className="mt-2 flex flex-col gap-1 text-sm text-muted-foreground">
            {book.year && <span>Published: {book.year}</span>}
            {book.pages && <span>Pages: {book.pages}</span>}
            {book.genre && <span>Genre: {book.genre}</span>}
            {book.publisher && <span>Publisher: {book.publisher}</span>}
            {book.isbn && <span>ISBN: {book.isbn}</span>}
          </div>
        </div>
      </div>

      {/* Description */}
      {book.description && (
        <p className="text-sm leading-relaxed text-muted-foreground">
          {book.description}
        </p>
      )}

      {/* Actions */}
      <div className="flex items-center gap-3">
        <Button>add to collection</Button>
        <Button
          variant={wishlisted ? "secondary" : "outline"}
          onClick={() => setWishlisted(true)}
          disabled={wishlisted}
        >
          {wishlisted ? (
            <>
              <Check className="mr-1.5 h-4 w-4" />
              in wishlist
            </>
          ) : (
            "add to wishlist"
          )}
        </Button>
      </div>
    </div>
  );
}

// ─── Collection Mode (own book) ───
function CollectionMode({ book }) {
  const [status, setStatus] = useState(book.status || "available");
  const [format, setFormat] = useState(book.format || "paperback");
  const [rating, setRating] = useState(book.rating || 0);
  const [thoughts, setThoughts] = useState(book.thoughts || "");
  const [borrower, setBorrower] = useState(book.borrower || "");
  const [dueDate, setDueDate] = useState(book.dueDate || "");
  const [salePrice, setSalePrice] = useState("");
  const [saleDate, setSaleDate] = useState("");
  const [confirmDelete, setConfirmDelete] = useState(false);

  return (
    <div className="mx-auto flex w-full max-w-3xl flex-1 flex-col gap-8 px-6 py-8">
      {/* Book Header */}
      <div className="flex gap-6">
        {book.cover ? (
          <img
            src={book.cover}
            alt={book.title}
            className="h-56 w-36 shrink-0 rounded-lg object-cover shadow-md"
          />
        ) : (
          <div className="flex h-56 w-36 shrink-0 items-center justify-center rounded-lg bg-muted shadow-md">
            <BookOpen className="h-8 w-8 text-muted-foreground/40" />
          </div>
        )}

        <div className="flex flex-col gap-2">
          <div className="flex items-center gap-3">
            <h1 className="font-heading text-2xl font-bold text-foreground">
              {book.title}
            </h1>
            {status === "reading" && (
              <Badge variant="default">currently reading</Badge>
            )}
          </div>
          <Link
            to={`/author/${book.authorId}`}
            className="text-sm font-medium text-primary hover:underline"
          >
            {book.author}
          </Link>

          {/* Status + Format Dropdowns */}
          <div className="mt-3 flex items-center gap-4">
            <div className="flex items-center gap-2">
              <span className="text-xs text-muted-foreground">status:</span>
              <select
                value={status}
                onChange={(e) => setStatus(e.target.value)}
                className="h-7 rounded-md border border-input bg-card px-2 text-xs text-foreground outline-none focus:border-ring"
              >
                <option value="reading">reading</option>
                <option value="available">available</option>
                <option value="lent">lent</option>
                <option value="sold">sold</option>
              </select>
            </div>

            <div className="flex items-center gap-2">
              <span className="text-xs text-muted-foreground">format:</span>
              <select
                value={format}
                onChange={(e) => setFormat(e.target.value)}
                className="h-7 rounded-md border border-input bg-card px-2 text-xs text-foreground outline-none focus:border-ring"
              >
                <option value="paperback">paperback</option>
                <option value="kindle">kindle</option>
                <option value="epub">epub</option>
                <option value="pdf">pdf</option>
              </select>
            </div>
          </div>
        </div>
      </div>

      {/* Conditional: Lent Fields */}
      {status === "lent" && (
        <div className="flex items-center gap-4 rounded-lg border border-border bg-card p-4">
          <div className="flex flex-1 flex-col gap-1">
            <label className="text-xs text-muted-foreground">borrower</label>
            <Input
              value={borrower}
              onChange={(e) => setBorrower(e.target.value)}
              placeholder="name"
              className="h-8 text-sm"
            />
          </div>
          <div className="flex flex-1 flex-col gap-1">
            <label className="text-xs text-muted-foreground">due date</label>
            <Input
              type="date"
              value={dueDate}
              onChange={(e) => setDueDate(e.target.value)}
              className="h-8 text-sm"
            />
          </div>
        </div>
      )}

      {/* Conditional: Sold Fields */}
      {status === "sold" && (
        <div className="flex items-center gap-4 rounded-lg border border-border bg-card p-4">
          <div className="flex flex-1 flex-col gap-1">
            <label className="text-xs text-muted-foreground">sale price</label>
            <Input
              value={salePrice}
              onChange={(e) => setSalePrice(e.target.value)}
              placeholder="amount"
              className="h-8 text-sm"
            />
          </div>
          <div className="flex flex-1 flex-col gap-1">
            <label className="text-xs text-muted-foreground">date</label>
            <Input
              type="date"
              value={saleDate}
              onChange={(e) => setSaleDate(e.target.value)}
              className="h-8 text-sm"
            />
          </div>
        </div>
      )}

      {/* Book Metadata */}
      <div className="flex flex-wrap gap-x-4 gap-y-1 text-sm text-muted-foreground">
        {book.year && <span>Published: {book.year}</span>}
        {book.pages && <span>· Pages: {book.pages}</span>}
        {book.genre && <span>· Genre: {book.genre}</span>}
        {book.publisher && <span>· Publisher: {book.publisher}</span>}
        {book.isbn && <span>· ISBN: {book.isbn}</span>}
      </div>

      {/* Rating */}
      <div className="rounded-xl border border-border bg-card p-5 shadow-[0_1px_3px_0_rgba(44,37,32,0.04),0_0_0_1px_rgba(44,37,32,0.02)] dark:shadow-none">
        <h3 className="mb-3 font-heading text-sm font-semibold text-foreground">
          your rating
        </h3>
        <div className="flex items-center gap-3">
          <StarRating rating={rating} onRate={setRating} />
          {rating === 0 && (
            <span className="text-xs text-muted-foreground">rate this book</span>
          )}
        </div>
      </div>

      {/* Thoughts */}
      <div className="rounded-xl border border-border bg-card p-5 shadow-[0_1px_3px_0_rgba(44,37,32,0.04),0_0_0_1px_rgba(44,37,32,0.02)] dark:shadow-none">
        <h3 className="mb-3 font-heading text-sm font-semibold text-foreground">
          your thoughts
        </h3>
        {thoughts === "" ? (
          <div className="flex flex-col gap-3">
            <textarea
              placeholder="what did you think?"
              value={thoughts}
              onChange={(e) => setThoughts(e.target.value)}
              className="min-h-[80px] w-full resize-none rounded-lg border border-input bg-transparent px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground outline-none focus:border-ring"
            />
            <Button size="sm" className="self-end">
              save
            </Button>
          </div>
        ) : (
          <div className="flex flex-col gap-3">
            <textarea
              value={thoughts}
              onChange={(e) => setThoughts(e.target.value)}
              className="min-h-[80px] w-full resize-none rounded-lg border border-input bg-transparent px-3 py-2 text-sm text-foreground outline-none focus:border-ring"
            />
            <Button size="sm" className="self-end">
              save
            </Button>
          </div>
        )}
      </div>

      {/* More by this Author */}
      <div className="rounded-xl border border-border bg-card p-5 shadow-[0_1px_3px_0_rgba(44,37,32,0.04),0_0_0_1px_rgba(44,37,32,0.02)] dark:shadow-none">
        <h3 className="mb-4 font-heading text-sm font-semibold text-foreground">
          more by this author
        </h3>
        {/* TODO: fetch from OpenLibrary API */}
        <p className="text-xs text-muted-foreground">
          no other books found
        </p>
      </div>

      {/* Danger Zone */}
      <div className="flex justify-end border-t border-border pt-6">
        {confirmDelete ? (
          <div className="flex items-center gap-2">
            <span className="text-xs text-muted-foreground">are you sure?</span>
            <Button variant="destructive" size="sm" onClick={() => {/* TODO: remove book */}}>
              yes, remove
            </Button>
            <Button variant="ghost" size="sm" onClick={() => setConfirmDelete(false)}>
              cancel
            </Button>
          </div>
        ) : (
          <button
            onClick={() => setConfirmDelete(true)}
            className="text-xs text-destructive transition-colors hover:text-destructive/80"
          >
            remove from collection
          </button>
        )}
      </div>
    </div>
  );
}

// ─── Book Detail Page ───
export default function BookDetail() {
  const { id } = useParams();

  // TODO: load book from store / OpenLibrary API by id (ISBN)
  // For now, show discovery mode with placeholder data
  const book = null;
  const owned = false;

  if (!book) {
    return (
      <div className="mx-auto flex w-full max-w-3xl flex-1 flex-col items-center justify-center px-6 py-24 text-center">
        <BookOpen className="mb-4 h-10 w-10 text-muted-foreground/40" />
        <p className="font-heading text-base font-medium text-foreground">
          book not found
        </p>
        <p className="mt-1 text-sm text-muted-foreground">
          ISBN: {id}
        </p>
      </div>
    );
  }

  return owned ? <CollectionMode book={book} /> : <DiscoveryMode book={book} />;
}
