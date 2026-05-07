import { useState, useEffect } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import { Star, BookOpen } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { booksApi, ApiError } from "@/lib/api";
import { Loading, ErrorBox } from "@/components/states";

function StarRating({ rating, onRate }) {
  const [hover, setHover] = useState(0);
  return (
    <div className="flex items-center gap-1">
      {[1, 2, 3, 4, 5].map((star) => (
        <button key={star} onClick={() => onRate(star)}
          onMouseEnter={() => setHover(star)} onMouseLeave={() => setHover(0)}
          className="text-lg transition-colors">
          <Star className={`h-5 w-5 ${star <= (hover || rating) ? "fill-amber-400 text-amber-400" : "text-muted-foreground/30"}`} />
        </button>
      ))}
    </div>
  );
}

function BookCoverClickable({ book }) {
  const [err, setErr] = useState(false);

  function handleClick() {
    const q = encodeURIComponent(`${book.title} ${book.author_name || ""}`);
    window.open(`https://www.google.com/search?q=${q}`, "_blank", "noopener");
  }

  const inner = (!book.cover_url || err)
    ? (
      <div className="flex h-full w-full items-center justify-center rounded-lg bg-muted shadow-md">
        <BookOpen className="h-8 w-8 text-muted-foreground/40" />
      </div>
    )
    : (
      <img src={book.cover_url} alt={book.title}
        className="h-full w-full rounded-lg object-cover shadow-md"
        onError={() => setErr(true)} />
    );

  return (
    <button onClick={handleClick} title="search on Google"
      className="h-44 w-28 shrink-0 cursor-pointer overflow-hidden rounded-lg transition-opacity hover:opacity-80 sm:h-56 sm:w-36">
      {inner}
    </button>
  );
}

const STATUS_OPTIONS = ["available", "reading", "read", "lent", "sold"];

function CollectionMode({ book, setBook, navigate }) {
  const [status, setStatus]     = useState(book.status || "available");
  const [format, setFormat]     = useState(book.format || "paperback");
  const [rating, setRating]     = useState(book.rating || 0);
  const [thoughts, setThoughts] = useState(book.thoughts || "");
  const [borrower, setBorrower] = useState(book.lending?.borrower || "");
  const [dueDate, setDueDate]   = useState(book.lending?.due_date || "");
  const [salePrice, setSalePrice] = useState(book.sale_price?.toString() || "");
  const [saleDate, setSaleDate] = useState(book.sale_date || "");
  const [coverUrl, setCoverUrl] = useState(book.cover_url || "");
  const [confirmDelete, setConfirmDelete] = useState(false);
  const [saving, setSaving]     = useState(false);

  async function put(body) { return booksApi.update(book.isbn, body); }

  async function handleStatusSelect(newStatus) {
    setStatus(newStatus);
    if (newStatus === "lent" || newStatus === "sold") return;
    setSaving(true);
    try {
      let updated;
      if (book.status === "lent") {
        updated = await booksApi.return(book.isbn);
        if (newStatus !== "available") updated = await put({ status: newStatus });
      } else {
        updated = await put({ status: newStatus });
      }
      setBook(updated);
      if (newStatus === "read") setStatus("read");
    } finally { setSaving(false); }
  }

  async function handleRate(star) {
    setRating(star);
    const updated = await put({ rating: star });
    setBook(updated);
  }

  async function handleThoughtsSave() {
    setSaving(true);
    try { const updated = await put({ thoughts }); setBook(updated); }
    finally { setSaving(false); }
  }

  async function handleLendSave() {
    if (!borrower || !dueDate) return;
    setSaving(true);
    try {
      if (book.status === "lent") await booksApi.return(book.isbn);
      const updated = await booksApi.lend(book.isbn, { borrower, due_date: dueDate });
      setBook(updated);
    } finally { setSaving(false); }
  }

  async function handleSoldSave() {
    setSaving(true);
    try {
      const updated = await put({ status: "sold", sale_price: parseFloat(salePrice) || null, sale_date: saleDate || null });
      setBook(updated);
    } finally { setSaving(false); }
  }

  async function handleCoverSave() {
    setSaving(true);
    try { const updated = await put({ cover_url: coverUrl || null }); setBook(updated); }
    finally { setSaving(false); }
  }

  async function handleDelete() {
    await booksApi.remove(book.isbn);
    navigate("/");
  }

  return (
    <div className="mx-auto flex w-full max-w-3xl flex-1 flex-col gap-8 px-4 py-6 sm:px-6 sm:py-8">
      {/* Book Header */}
      <div className="flex flex-col gap-5 sm:flex-row sm:gap-6">
        <BookCoverClickable book={book} />

        <div className="flex flex-col gap-2">
          <div className="flex flex-wrap items-center gap-2">
            <h1 className="font-heading text-2xl font-bold text-foreground">{book.title}</h1>
            {status === "reading" && <Badge variant="default">reading</Badge>}
            {status === "read" && <Badge variant="secondary">read</Badge>}
          </div>

          <Link to={`/author/${book.author_id}`}
            className="text-sm font-medium text-primary hover:underline">
            {book.author_name}
          </Link>

          {/* Genres */}
          {book.genres?.length > 0 && (
            <div className="flex flex-wrap gap-1.5 mt-1">
              {book.genres.map((g) => (
                <Link key={g} to={`/?genres=${encodeURIComponent(g)}`}
                  className="rounded-full border border-border px-2.5 py-0.5 text-xs text-muted-foreground hover:border-primary/40 hover:text-primary transition-colors">
                  {g}
                </Link>
              ))}
            </div>
          )}

          {/* Status + Format */}
          <div className="mt-3 flex flex-wrap items-center gap-4">
            <div className="flex items-center gap-2">
              <span className="text-xs text-muted-foreground">status:</span>
              <select value={status} onChange={(e) => handleStatusSelect(e.target.value)}
                disabled={saving}
                className="h-7 rounded-md border border-input bg-card px-2 text-xs text-foreground outline-none focus:border-ring">
                {STATUS_OPTIONS.map((s) => <option key={s} value={s}>{s}</option>)}
              </select>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-xs text-muted-foreground">format:</span>
              <select value={format}
                onChange={async (e) => { setFormat(e.target.value); const u = await put({ format: e.target.value }); setBook(u); }}
                className="h-7 rounded-md border border-input bg-card px-2 text-xs text-foreground outline-none focus:border-ring">
                {["paperback", "hardcover", "kindle", "epub", "pdf"].map((f) => <option key={f} value={f}>{f}</option>)}
              </select>
            </div>
          </div>
        </div>
      </div>

      {/* Lent fields */}
      {status === "lent" && (
        <div className="flex flex-col gap-3 rounded-lg border border-border bg-card p-4 sm:flex-row sm:items-end sm:gap-4">
          <label className="flex flex-1 flex-col gap-1">
            <span className="text-xs text-muted-foreground">borrower</span>
            <Input value={borrower} onChange={(e) => setBorrower(e.target.value)} placeholder="name" className="h-8 text-sm" />
          </label>
          <label className="flex flex-1 flex-col gap-1">
            <span className="text-xs text-muted-foreground">due date</span>
            <Input type="date" value={dueDate} onChange={(e) => setDueDate(e.target.value)} className="h-8 text-sm" />
          </label>
          <Button size="sm" onClick={handleLendSave} disabled={saving || !borrower || !dueDate}>save</Button>
        </div>
      )}

      {/* Sold fields */}
      {status === "sold" && (
        <div className="flex flex-col gap-3 rounded-lg border border-border bg-card p-4 sm:flex-row sm:items-end sm:gap-4">
          <label className="flex flex-1 flex-col gap-1">
            <span className="text-xs text-muted-foreground">sale price</span>
            <Input value={salePrice} onChange={(e) => setSalePrice(e.target.value)} placeholder="amount" className="h-8 text-sm" />
          </label>
          <label className="flex flex-1 flex-col gap-1">
            <span className="text-xs text-muted-foreground">date</span>
            <Input type="date" value={saleDate} onChange={(e) => setSaleDate(e.target.value)} className="h-8 text-sm" />
          </label>
          <Button size="sm" onClick={handleSoldSave} disabled={saving}>save</Button>
        </div>
      )}

      {/* Metadata */}
      <div className="flex flex-wrap gap-x-4 gap-y-1 text-sm text-muted-foreground">
        {book.year      && <span>Published: {book.year}</span>}
        {book.pages     && <span>· Pages: {book.pages}</span>}
        {book.publisher && <span>· Publisher: {book.publisher}</span>}
        {book.isbn      && <span>· ISBN: {book.isbn}</span>}
        {book.date_read && <span>· Read: {book.date_read}</span>}
      </div>

      {book.description && (
        <p className="text-sm leading-relaxed text-muted-foreground">{book.description}</p>
      )}

      {/* Rating */}
      <div className="rounded-xl border border-border bg-card p-5 shadow-sm dark:shadow-none">
        <h3 className="mb-3 font-heading text-sm font-semibold text-foreground">your rating</h3>
        <div className="flex items-center gap-3">
          <StarRating rating={rating} onRate={handleRate} />
          {rating === 0 && <span className="text-xs text-muted-foreground">rate this book</span>}
        </div>
      </div>

      {/* Thoughts */}
      <div className="rounded-xl border border-border bg-card p-5 shadow-sm dark:shadow-none">
        <h3 className="mb-3 font-heading text-sm font-semibold text-foreground">your thoughts</h3>
        <div className="flex flex-col gap-3">
          <textarea value={thoughts} onChange={(e) => setThoughts(e.target.value)}
            placeholder="what did you think?"
            className="min-h-[80px] w-full resize-none rounded-lg border border-input bg-transparent px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground outline-none focus:border-ring" />
          <Button size="sm" className="self-end" onClick={handleThoughtsSave} disabled={saving}>save</Button>
        </div>
      </div>

      {/* Cover URL */}
      <div className="rounded-xl border border-border bg-card p-5 shadow-sm dark:shadow-none">
        <h3 className="mb-3 font-heading text-sm font-semibold text-foreground">cover image</h3>
        <div className="flex gap-2">
          <Input value={coverUrl} onChange={(e) => setCoverUrl(e.target.value)} placeholder="https://…" className="h-8 text-sm" />
          <Button size="sm" onClick={handleCoverSave} disabled={saving}>save</Button>
        </div>
      </div>

      {/* Danger Zone */}
      <div className="flex justify-end border-t border-border pt-6">
        {confirmDelete ? (
          <div className="flex items-center gap-2">
            <span className="text-xs text-muted-foreground">are you sure?</span>
            <Button variant="destructive" size="sm" onClick={handleDelete}>yes, remove</Button>
            <Button variant="ghost" size="sm" onClick={() => setConfirmDelete(false)}>cancel</Button>
          </div>
        ) : (
          <button onClick={() => setConfirmDelete(true)}
            className="text-xs text-destructive transition-colors hover:text-destructive/80">
            remove from collection
          </button>
        )}
      </div>
    </div>
  );
}

export default function BookDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [book, setBook] = useState(null);
  const [notFound, setNotFound] = useState(false);
  const [error, setError] = useState(null);

  function load() {
    setError(null);
    setNotFound(false);
    booksApi.get(id)
      .then(setBook)
      .catch((err) => {
        if (err instanceof ApiError && err.status === 404) setNotFound(true);
        else setError(err.message);
      });
  }

  useEffect(load, [id]);

  if (notFound) {
    return (
      <div className="mx-auto flex w-full max-w-3xl flex-1 flex-col items-center justify-center px-4 py-24 text-center sm:px-6">
        <BookOpen className="mb-4 h-10 w-10 text-muted-foreground/40" />
        <p className="font-heading text-base font-medium">book not found</p>
        <p className="mt-1 text-sm text-muted-foreground">ISBN: {id}</p>
      </div>
    );
  }

  if (error) return <div className="mx-auto w-full max-w-3xl px-4 py-8 sm:px-6"><ErrorBox message={error} onRetry={load} /></div>;
  if (!book) return <Loading />;

  return <CollectionMode book={book} setBook={setBook} navigate={navigate} />;
}
