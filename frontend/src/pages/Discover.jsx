import { useState, useEffect, useRef } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { Search, Plus, ArrowLeft, BookOpen, ExternalLink, ShoppingCart } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { booksApi, authorsApi, wishlistApi, genresApi, ApiError } from "@/lib/api";

const OL_SEARCH = "https://openlibrary.org/search.json";
const FORMATS = ["paperback", "hardcover", "kindle", "epub", "pdf"];

// ── OpenLibrary helpers ──────────────────────────────────────────────────────

async function searchOpenLibrary(query) {
  const clean = query.trim().replace(/-/g, "");
  const isISBN = /^\d{10,13}$/.test(clean);
  const params = isISBN
    ? { isbn: clean, limit: 10 }
    : { q: query.trim(), limit: 20, fields: "title,author_name,first_publish_year,isbn,cover_i,subject,number_of_pages_median,key" };
  const res = await fetch(`${OL_SEARCH}?${new URLSearchParams(params)}`);
  const data = await res.json();
  return (data.docs || []).filter((d) => d.title);
}

function olCoverUrl(coverId, size = "M") {
  return coverId ? `https://covers.openlibrary.org/b/id/${coverId}-${size}.jpg` : null;
}

function olToForm(doc) {
  const isbn = (doc.isbn || []).find((i) => i.length === 13) || (doc.isbn || [])[0] || "";
  const genres = (doc.subject || []).slice(0, 6).map((s) =>
    s.split(" ").map((w) => w[0]?.toUpperCase() + w.slice(1)).join(" ")
  );
  return {
    isbn,
    title: doc.title || "",
    author_name: doc.author_name?.[0] || "",
    year: String(doc.first_publish_year || ""),
    pages: String(doc.number_of_pages_median || ""),
    cover_url: olCoverUrl(doc.cover_i) || "",
    genres,
    publisher: "",
    description: "",
    format: "paperback",
    buy_url: isbn
      ? `https://www.amazon.com/s?k=${encodeURIComponent((doc.title || "") + " " + (doc.author_name?.[0] || ""))}`
      : "",
    ol_key: doc.key || "",
  };
}

// ── Genre tag picker ──────────────────────────────────────────────────────────

function GenrePicker({ selected, onChange, suggestions = [] }) {
  const [input, setInput] = useState("");
  const all = [...new Set([...suggestions, ...selected])];

  function toggle(g) {
    onChange(selected.includes(g) ? selected.filter((x) => x !== g) : [...selected, g]);
  }

  function addCustom(e) {
    if (e.key === "Enter" && input.trim()) {
      e.preventDefault();
      const g = input.trim();
      if (!selected.includes(g)) onChange([...selected, g]);
      setInput("");
    }
  }

  return (
    <div className="flex flex-col gap-2">
      <div className="flex flex-wrap gap-1.5">
        {all.map((g) => (
          <button key={g} type="button" onClick={() => toggle(g)}
            className={`rounded-full px-2.5 py-0.5 text-xs font-medium transition-colors border ${
              selected.includes(g)
                ? "border-primary bg-primary/10 text-primary"
                : "border-border text-muted-foreground hover:border-primary/50 hover:text-foreground"
            }`}>
            {g}
          </button>
        ))}
      </div>
      <Input
        type="text"
        placeholder="type genre + enter to add…"
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyDown={addCustom}
        className="h-7 text-xs"
      />
    </div>
  );
}

// ── Add Author Modal ──────────────────────────────────────────────────────────

function AddAuthorModal({ onClose, onCreated, defaultName = "" }) {
  const [name, setName] = useState(defaultName);
  const [country, setCountry] = useState("");
  const [dob, setDob] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);

  async function handleSubmit(e) {
    e.preventDefault();
    setSaving(true);
    setError(null);
    try {
      const created = await authorsApi.create({ name, country, dob, awards: [] });
      onCreated(created);
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-6">
      <form onSubmit={handleSubmit}
        className="flex w-full max-w-sm flex-col gap-4 rounded-xl border border-border bg-card p-6 shadow-lg">
        <h2 className="font-heading text-base font-semibold">new author</h2>
        <label className="flex flex-col gap-1">
          <span className="text-xs text-muted-foreground">name</span>
          <Input value={name} onChange={(e) => setName(e.target.value)} required />
        </label>
        <label className="flex flex-col gap-1">
          <span className="text-xs text-muted-foreground">country</span>
          <Input value={country} onChange={(e) => setCountry(e.target.value)} />
        </label>
        <label className="flex flex-col gap-1">
          <span className="text-xs text-muted-foreground">date of birth</span>
          <Input type="date" value={dob} onChange={(e) => setDob(e.target.value)} />
        </label>
        {error && <p className="text-sm text-destructive">{error}</p>}
        <div className="flex justify-end gap-2">
          <Button type="button" variant="ghost" size="sm" onClick={onClose}>cancel</Button>
          <Button type="submit" size="sm" disabled={saving || !name}>
            {saving ? "…" : "create"}
          </Button>
        </div>
      </form>
    </div>
  );
}

// ── Search Step ───────────────────────────────────────────────────────────────

function SearchStep({ onSelect, onManual }) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);
  const [coverErrors, setCoverErrors] = useState({});

  async function doSearch(e) {
    e.preventDefault();
    if (!query.trim()) return;
    setLoading(true);
    setSearched(true);
    try {
      const docs = await searchOpenLibrary(query);
      setResults(docs);
    } catch {
      setResults([]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex flex-col gap-5">
      <form onSubmit={doSearch} className="flex gap-2">
        <Input
          placeholder="search by title, author, or ISBN…"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          className="h-10 text-sm"
          autoFocus
        />
        <Button type="submit" className="h-10 px-4" disabled={loading}>
          <Search className="h-4 w-4" />
        </Button>
      </form>

      {loading && (
        <div className="flex justify-center py-10">
          <div className="h-6 w-6 animate-spin rounded-full border-2 border-primary border-t-transparent" />
        </div>
      )}

      {searched && !loading && results.length === 0 && (
        <div className="py-10 text-center text-sm text-muted-foreground">
          no results — try a different query or{" "}
          <button onClick={onManual} className="font-medium text-primary hover:underline">add manually</button>
        </div>
      )}

      {results.length > 0 && (
        <div className="flex flex-col gap-2">
          {results.map((doc, i) => {
            const coverId = doc.cover_i;
            const coverUrl = olCoverUrl(coverId, "S");
            return (
              <button key={i} onClick={() => onSelect(olToForm(doc))}
                className="flex items-center gap-3 rounded-lg border border-border bg-card p-3 text-left transition-colors hover:border-primary/40 hover:bg-muted/50">
                <div className="h-14 w-10 shrink-0 overflow-hidden rounded">
                  {coverUrl && !coverErrors[i] ? (
                    <img src={coverUrl} alt={doc.title}
                      className="h-full w-full object-cover"
                      onError={() => setCoverErrors((e) => ({ ...e, [i]: true }))} />
                  ) : (
                    <div className="flex h-full w-full items-center justify-center bg-muted">
                      <BookOpen className="h-4 w-4 text-muted-foreground/40" />
                    </div>
                  )}
                </div>
                <div className="flex flex-1 flex-col gap-0.5 min-w-0">
                  <span className="truncate text-sm font-medium text-foreground">{doc.title}</span>
                  <span className="text-xs text-muted-foreground">
                    {doc.author_name?.[0]}{doc.first_publish_year ? ` · ${doc.first_publish_year}` : ""}
                  </span>
                  {doc.isbn?.[0] && (
                    <span className="text-xs text-muted-foreground/60">ISBN {doc.isbn[0]}</span>
                  )}
                </div>
              </button>
            );
          })}
        </div>
      )}

      <div className="flex items-center gap-3 pt-2">
        <div className="h-px flex-1 bg-border" />
        <button onClick={onManual} className="text-xs text-muted-foreground hover:text-foreground transition-colors">
          add manually instead
        </button>
        <div className="h-px flex-1 bg-border" />
      </div>
    </div>
  );
}

// ── Add Form ─────────────────────────────────────────────────────────────────

function AddForm({ prefillOL, prefillWishlist, authors, allGenres, onBack }) {
  const navigate = useNavigate();
  const [mode, setMode] = useState("library");
  const [showAddAuthor, setShowAddAuthor] = useState(false);
  const [authorList, setAuthorList] = useState(authors);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);

  const [form, setForm] = useState(() => {
    const p = prefillOL || prefillWishlist || {};
    return {
      isbn:        p.isbn        || "",
      title:       p.title       || "",
      author_id:   "",
      pages:       p.pages       || "",
      year:        p.year ? String(p.year) : "",
      genres:      p.genres      || [],
      publisher:   "",
      description: "",
      format:      "paperback",
      cover_url:   p.cover_url   || "",
      buy_url:     p.buy_url     || "",
    };
  });

  // Auto-match author name from OL or wishlist
  useEffect(() => {
    const nameHint = prefillOL?.author_name || prefillWishlist?.author_name;
    if (nameHint) {
      const match = authorList.find((a) => a.name.toLowerCase() === nameHint.toLowerCase());
      if (match) setForm((f) => ({ ...f, author_id: match.id }));
    }
  }, [authorList, prefillOL, prefillWishlist]);

  function set(field) {
    return (e) => setForm((f) => ({ ...f, [field]: e.target.value }));
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setError(null);
    setSaving(true);
    try {
      if (mode === "library") {
        let authorId = form.author_id;
        if (!authorId) {
          const nameHint = prefillOL?.author_name || prefillWishlist?.author_name;
          if (!nameHint) throw new Error("pick an author first");
          const newAuthor = await authorsApi.create({ name: nameHint, country: "", dob: "", awards: [] });
          setAuthorList((prev) => [...prev, newAuthor]);
          setForm((f) => ({ ...f, author_id: newAuthor.id }));
          authorId = newAuthor.id;
        }
        const created = await booksApi.create({
          isbn:        form.isbn,
          title:       form.title,
          author_id:   authorId,
          pages:       parseInt(form.pages) || 0,
          year:        parseInt(form.year) || 0,
          genres:      form.genres,
          publisher:   form.publisher,
          description: form.description || null,
          format:      form.format,
          cover_url:   form.cover_url || null,
        });
        navigate(`/book/${created.isbn}`);
      } else {
        await wishlistApi.add({
          isbn:        form.isbn,
          title:       form.title,
          author_name: authorList.find((a) => a.id === form.author_id)?.name || prefillOL?.author_name || "",
          year:        parseInt(form.year) || 0,
          genres:      form.genres,
          cover_url:   form.cover_url || null,
          buy_url:     form.buy_url || null,
        });
        navigate("/");
      }
    } catch (err) {
      setError(err instanceof ApiError ? err.message : String(err));
    } finally {
      setSaving(false);
    }
  }

  const suggestedGenres = allGenres.map((g) => g.name);

  return (
    <>
      {onBack && (
        <button onClick={onBack}
          className="mb-4 flex items-center gap-1.5 text-xs text-muted-foreground hover:text-foreground transition-colors">
          <ArrowLeft className="h-3.5 w-3.5" /> back to search
        </button>
      )}

      {/* Preview header when from OL */}
      {prefillOL && (
        <div className="mb-5 flex items-center gap-3 rounded-lg border border-border bg-card p-3">
          {form.cover_url ? (
            <img src={form.cover_url} alt={form.title}
              className="h-16 w-11 shrink-0 rounded object-cover" />
          ) : (
            <div className="flex h-16 w-11 shrink-0 items-center justify-center rounded bg-muted">
              <BookOpen className="h-5 w-5 text-muted-foreground/40" />
            </div>
          )}
          <div className="flex flex-col gap-0.5 min-w-0">
            <span className="truncate font-medium text-foreground">{form.title}</span>
            <span className="text-sm text-muted-foreground">{prefillOL.author_name}</span>
            {prefillOL.ol_key && (
              <a href={`https://openlibrary.org${prefillOL.ol_key}`} target="_blank" rel="noopener noreferrer"
                className="flex items-center gap-1 text-xs text-primary hover:underline">
                open on OpenLibrary <ExternalLink className="h-3 w-3" />
              </a>
            )}
            {form.buy_url && (
              <a href={form.buy_url} target="_blank" rel="noopener noreferrer"
                className="flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground">
                <ShoppingCart className="h-3 w-3" /> find to buy
              </a>
            )}
          </div>
        </div>
      )}

      {/* Mode toggle */}
      <div className="mb-5 flex w-fit items-center gap-1 rounded-full border border-border bg-card p-1">
        {["library", "wishlist"].map((m) => (
          <button key={m} type="button" onClick={() => setMode(m)}
            className={`rounded-full px-4 py-1.5 text-xs font-medium transition-colors ${
              mode === m ? "bg-primary text-primary-foreground" : "text-muted-foreground hover:text-foreground"
            }`}>
            to {m}
          </button>
        ))}
      </div>

      <form onSubmit={handleSubmit} className="flex flex-col gap-4">
        <label className="flex flex-col gap-1">
          <span className="text-xs text-muted-foreground">isbn</span>
          <Input value={form.isbn} onChange={set("isbn")} required />
        </label>

        <label className="flex flex-col gap-1">
          <span className="text-xs text-muted-foreground">title</span>
          <Input value={form.title} onChange={set("title")} required />
        </label>

        <div className="flex flex-col gap-1">
          <span className="text-xs text-muted-foreground">author</span>
          <div className="flex gap-2">
            <select value={form.author_id} onChange={set("author_id")}
              required={mode === "library"}
              className="h-9 flex-1 rounded-md border border-input bg-card px-2 text-sm text-foreground outline-none focus:border-ring">
              <option value="">— pick author —</option>
              {authorList.map((a) => <option key={a.id} value={a.id}>{a.name}</option>)}
            </select>
            <Button type="button" size="sm" variant="outline" onClick={() => setShowAddAuthor(true)}>
              <Plus className="h-4 w-4" /> new
            </Button>
          </div>
          {prefillOL?.author_name && !form.author_id && (
            <p className="text-xs text-amber-600 dark:text-amber-400">
              author "{prefillOL.author_name}" not found — create them above or pick from list
            </p>
          )}
        </div>

        <div className="grid grid-cols-2 gap-4">
          <label className="flex flex-col gap-1">
            <span className="text-xs text-muted-foreground">year</span>
            <Input type="number" value={form.year} onChange={set("year")} />
          </label>
          <label className="flex flex-col gap-1">
            <span className="text-xs text-muted-foreground">pages</span>
            <Input type="number" value={form.pages} onChange={set("pages")} />
          </label>
        </div>

        <div className="flex flex-col gap-1">
          <span className="text-xs text-muted-foreground">genres</span>
          <GenrePicker
            selected={form.genres}
            onChange={(genres) => setForm((f) => ({ ...f, genres }))}
            suggestions={suggestedGenres}
          />
        </div>

        {mode === "library" && (
          <>
            <label className="flex flex-col gap-1">
              <span className="text-xs text-muted-foreground">publisher</span>
              <Input value={form.publisher} onChange={set("publisher")} />
            </label>
            <label className="flex flex-col gap-1">
              <span className="text-xs text-muted-foreground">format</span>
              <select value={form.format} onChange={set("format")}
                className="h-9 rounded-md border border-input bg-card px-2 text-sm text-foreground outline-none focus:border-ring">
                {FORMATS.map((f) => <option key={f} value={f}>{f}</option>)}
              </select>
            </label>
            <label className="flex flex-col gap-1">
              <span className="text-xs text-muted-foreground">cover url</span>
              <Input value={form.cover_url} onChange={set("cover_url")} placeholder="https://…" />
            </label>
            <label className="flex flex-col gap-1">
              <span className="text-xs text-muted-foreground">description</span>
              <textarea value={form.description} onChange={set("description")}
                className="min-h-[80px] w-full resize-none rounded-md border border-input bg-transparent px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground outline-none focus:border-ring"
                placeholder="optional…" />
            </label>
          </>
        )}

        {mode === "wishlist" && (
          <label className="flex flex-col gap-1">
            <span className="text-xs text-muted-foreground">buy link (optional)</span>
            <Input value={form.buy_url} onChange={set("buy_url")} placeholder="https://…" />
          </label>
        )}

        {error && <p className="text-sm text-destructive">{error}</p>}

        <Button type="submit" disabled={saving} className="self-end">
          {saving ? "saving…" : mode === "library" ? "add to library" : "add to wishlist"}
        </Button>
      </form>

      {showAddAuthor && (
        <AddAuthorModal
          onClose={() => setShowAddAuthor(false)}
          defaultName={!form.author_id ? (prefillOL?.author_name || prefillWishlist?.author_name || "") : ""}
          onCreated={(newAuthor) => {
            setAuthorList((prev) => [...prev, newAuthor]);
            setForm((f) => ({ ...f, author_id: newAuthor.id }));
            setShowAddAuthor(false);
          }}
        />
      )}
    </>
  );
}

// ── Main Page ────────────────────────────────────────────────────────────────

export default function Discover() {
  const location = useLocation();
  const wishlistPrefill = location.state?.prefill;

  const [authors, setAuthors] = useState([]);
  const [allGenres, setAllGenres] = useState([]);
  const [step, setStep] = useState(wishlistPrefill ? "form" : "search");
  const [selectedOL, setSelectedOL] = useState(null);

  useEffect(() => {
    Promise.all([authorsApi.list(), genresApi.list()])
      .then(([a, g]) => { setAuthors(a); setAllGenres(g); })
      .catch(() => {});
  }, []);

  function handleOLSelect(olForm) {
    setSelectedOL(olForm);
    setStep("form");
  }

  return (
    <div className="mx-auto flex w-full max-w-2xl flex-1 flex-col gap-6 px-4 py-6 sm:px-6 sm:py-8">
      <h1 className="font-heading text-2xl font-bold text-foreground">discover</h1>

      {step === "search" && (
        <SearchStep onSelect={handleOLSelect} onManual={() => setStep("form")} />
      )}

      {step === "form" && (
        <AddForm
          prefillOL={selectedOL}
          prefillWishlist={wishlistPrefill}
          authors={authors}
          allGenres={allGenres}
          onBack={!wishlistPrefill ? () => { setStep("search"); setSelectedOL(null); } : null}
        />
      )}
    </div>
  );
}
