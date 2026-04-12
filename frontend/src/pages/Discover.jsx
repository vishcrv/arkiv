import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Plus } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { booksApi, authorsApi, wishlistApi, ApiError } from "@/lib/api";

const GENRES = [
  "Fiction", "Non-Fiction", "Sci-Fi", "Fantasy", "Mystery",
  "Biography", "History", "Self-Help", "Other",
];
const FORMATS = ["paperback", "kindle", "epub", "pdf"];

function Field({ label, children }) {
  return (
    <label className="flex flex-col gap-1">
      <span className="text-xs text-muted-foreground">{label}</span>
      {children}
    </label>
  );
}

function AddAuthorModal({ onClose, onCreated }) {
  const [name, setName] = useState("");
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
      <form
        onSubmit={handleSubmit}
        className="flex w-full max-w-sm flex-col gap-4 rounded-xl border border-border bg-card p-6 shadow-lg"
      >
        <h2 className="font-heading text-base font-semibold text-foreground">new author</h2>
        <Field label="Name">
          <Input value={name} onChange={(e) => setName(e.target.value)} required />
        </Field>
        <Field label="Country">
          <Input value={country} onChange={(e) => setCountry(e.target.value)} />
        </Field>
        <Field label="Date of birth">
          <Input type="date" value={dob} onChange={(e) => setDob(e.target.value)} />
        </Field>
        {error && <p className="text-sm text-destructive">{error}</p>}
        <div className="flex justify-end gap-2">
          <Button type="button" variant="ghost" size="sm" onClick={onClose}>cancel</Button>
          <Button type="submit" size="sm" disabled={saving || !name}>
            {saving ? "..." : "create"}
          </Button>
        </div>
      </form>
    </div>
  );
}

export default function Discover() {
  const navigate = useNavigate();
  const [mode, setMode] = useState("library"); // "library" | "wishlist"
  const [authors, setAuthors] = useState([]);
  const [showAddAuthor, setShowAddAuthor] = useState(false);
  const [error, setError] = useState(null);
  const [saving, setSaving] = useState(false);

  const [form, setForm] = useState({
    isbn: "", title: "", author_id: "", pages: "", year: "",
    genre: "", publisher: "", description: "", format: "paperback", cover_url: "",
  });

  useEffect(() => {
    authorsApi.list().then(setAuthors).catch((e) => setError(e.message));
  }, []);

  function set(field) {
    return (e) => setForm({ ...form, [field]: e.target.value });
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setError(null);
    setSaving(true);
    try {
      if (mode === "library") {
        if (!form.author_id) throw new Error("pick an author first");
        const created = await booksApi.create({
          isbn: form.isbn,
          title: form.title,
          author_id: form.author_id,
          pages: parseInt(form.pages) || 0,
          year: parseInt(form.year) || 0,
          genre: form.genre,
          publisher: form.publisher,
          description: form.description || null,
          format: form.format,
          cover_url: form.cover_url || null,
        });
        navigate(`/book/${created.isbn}`);
      } else {
        await wishlistApi.add({
          isbn: form.isbn,
          title: form.title,
          author_name: authors.find((a) => a.id === form.author_id)?.name || "",
          year: parseInt(form.year) || 0,
          genre: form.genre,
        });
        navigate("/");
      }
    } catch (err) {
      setError(err instanceof ApiError ? err.message : String(err));
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="mx-auto flex w-full max-w-2xl flex-1 flex-col gap-6 px-6 py-8">
      <h1 className="font-heading text-2xl font-bold text-foreground">add a book</h1>

      {/* Mode toggle */}
      <div className="flex w-fit items-center gap-1 rounded-full border border-border bg-card p-1">
        <button
          type="button"
          onClick={() => setMode("library")}
          className={`rounded-full px-4 py-1.5 text-xs font-medium transition-colors ${
            mode === "library"
              ? "bg-primary text-primary-foreground"
              : "text-muted-foreground hover:text-foreground"
          }`}
        >
          to library
        </button>
        <button
          type="button"
          onClick={() => setMode("wishlist")}
          className={`rounded-full px-4 py-1.5 text-xs font-medium transition-colors ${
            mode === "wishlist"
              ? "bg-primary text-primary-foreground"
              : "text-muted-foreground hover:text-foreground"
          }`}
        >
          to wishlist
        </button>
      </div>

      <form onSubmit={handleSubmit} className="flex flex-col gap-4">
        <Field label="ISBN">
          <Input value={form.isbn} onChange={set("isbn")} required />
        </Field>
        <Field label="Title">
          <Input value={form.title} onChange={set("title")} required />
        </Field>

        <Field label="Author">
          <div className="flex gap-2">
            <select
              value={form.author_id}
              onChange={set("author_id")}
              className="h-9 flex-1 rounded-md border border-input bg-card px-2 text-sm text-foreground outline-none focus:border-ring"
              required={mode === "library"}
            >
              <option value="">— pick author —</option>
              {authors.map((a) => (
                <option key={a.id} value={a.id}>{a.name}</option>
              ))}
            </select>
            <Button type="button" size="sm" variant="outline" onClick={() => setShowAddAuthor(true)}>
              <Plus className="h-4 w-4" /> new
            </Button>
          </div>
        </Field>

        <div className="grid grid-cols-2 gap-4">
          <Field label="Year">
            <Input type="number" value={form.year} onChange={set("year")} />
          </Field>
          <Field label="Pages">
            <Input type="number" value={form.pages} onChange={set("pages")} />
          </Field>
        </div>

        <Field label="Genre">
          <select
            value={form.genre}
            onChange={set("genre")}
            className="h-9 rounded-md border border-input bg-card px-2 text-sm text-foreground outline-none focus:border-ring"
          >
            <option value="">—</option>
            {GENRES.map((g) => <option key={g} value={g}>{g}</option>)}
          </select>
        </Field>

        {mode === "library" && (
          <>
            <Field label="Publisher">
              <Input value={form.publisher} onChange={set("publisher")} />
            </Field>
            <Field label="Format">
              <select
                value={form.format}
                onChange={set("format")}
                className="h-9 rounded-md border border-input bg-card px-2 text-sm text-foreground outline-none focus:border-ring"
              >
                {FORMATS.map((f) => <option key={f} value={f}>{f}</option>)}
              </select>
            </Field>
            <Field label="Cover URL (optional)">
              <Input
                value={form.cover_url}
                onChange={set("cover_url")}
                placeholder="https://..."
              />
            </Field>
            <Field label="Description (optional)">
              <textarea
                value={form.description}
                onChange={set("description")}
                className="min-h-[80px] w-full resize-none rounded-md border border-input bg-transparent px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground outline-none focus:border-ring"
              />
            </Field>
          </>
        )}

        {error && <p className="text-sm text-destructive">{error}</p>}

        <Button type="submit" disabled={saving} className="self-end">
          {saving ? "saving..." : mode === "library" ? "add to library" : "add to wishlist"}
        </Button>
      </form>

      {showAddAuthor && (
        <AddAuthorModal
          onClose={() => setShowAddAuthor(false)}
          onCreated={(newAuthor) => {
            setAuthors([...authors, newAuthor]);
            setForm({ ...form, author_id: newAuthor.id });
            setShowAddAuthor(false);
          }}
        />
      )}
    </div>
  );
}
