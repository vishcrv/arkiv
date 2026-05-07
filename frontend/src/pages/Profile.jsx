import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import {
  BookOpen, BookCheck, Eye, FileText,
  Users, MessageSquare, ArrowRightLeft, Heart,
} from "lucide-react";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { profileApi, statsApi } from "@/lib/api";
import { Loading, ErrorBox } from "@/components/states";
import { useAuth } from "@/lib/auth";
import { ThemeToggle } from "@/components/theme-toggle";

function formatMemberSince(isoDate) {
  if (!isoDate || isoDate.startsWith("1970")) return null;
  return new Date(isoDate)
    .toLocaleDateString("en-US", { month: "long", year: "numeric" })
    .toLowerCase();
}

// ── Stat card — clickable, routes to filtered view ────────────────────────────

function StatCard({ icon: Icon, label, value, to }) {
  const navigate = useNavigate();
  return (
    <button
      onClick={() => to && navigate(to)}
      className={`flex items-center gap-3 rounded-xl border border-border bg-card p-4 shadow-sm dark:shadow-none text-left transition-colors ${to ? "hover:border-primary/40 cursor-pointer" : "cursor-default"}`}
    >
      <Icon className="h-4 w-4 shrink-0 text-muted-foreground" />
      <div className="flex flex-col">
        <span className="text-lg font-semibold text-foreground">{value}</span>
        <span className="text-xs text-muted-foreground">{label}</span>
      </div>
    </button>
  );
}

// ── Genre breakdown ───────────────────────────────────────────────────────────

function GenreBreakdown({ breakdown }) {
  const navigate = useNavigate();
  const entries = Object.entries(breakdown).sort((a, b) => b[1] - a[1]);
  if (entries.length === 0) return null;
  const max = entries[0][1];

  return (
    <div className="rounded-xl border border-border bg-card p-5 shadow-sm dark:shadow-none">
      <h2 className="mb-4 font-heading text-sm font-semibold text-foreground">genre breakdown</h2>
      <div className="flex flex-col gap-2.5">
        {entries.map(([genre, count]) => (
          <button key={genre} onClick={() => navigate(`/?genres=${encodeURIComponent(genre)}`)}
            className="flex items-center gap-3 text-left group">
            <span className="w-28 shrink-0 truncate text-xs text-muted-foreground group-hover:text-foreground transition-colors">
              {genre}
            </span>
            <div className="flex flex-1 items-center gap-2">
              <div className="h-2 flex-1 overflow-hidden rounded-full bg-muted">
                <div className="h-full rounded-full bg-primary/50 group-hover:bg-primary transition-colors"
                  style={{ width: `${(count / max) * 100}%` }} />
              </div>
              <span className="w-6 shrink-0 text-right text-xs text-muted-foreground">{count}</span>
            </div>
          </button>
        ))}
      </div>
    </div>
  );
}

// ── Settings section ──────────────────────────────────────────────────────────

function Settings({ profile }) {
  const { updateUser, logout } = useAuth();
  const navigate = useNavigate();
  const [username, setUsername] = useState(profile.username || "");
  const [saving, setSaving]     = useState(false);
  const [saved, setSaved]       = useState(false);
  const [error, setError]       = useState(null);

  async function handleSaveUsername(e) {
    e.preventDefault();
    if (!username.trim()) return;
    setSaving(true);
    setError(null);
    try {
      await profileApi.update({ username: username.trim() });
      updateUser({ username: username.trim() });
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
    } catch (e) {
      setError(e.message);
    } finally {
      setSaving(false);
    }
  }

  async function handleExport() {
    try {
      const token = localStorage.getItem("arkiv_token");
      const res = await fetch("/api/books", { headers: { Authorization: `Bearer ${token}` } });
      const books = await res.json();
      const blob = new Blob([JSON.stringify(books, null, 2)], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `arkiv-library-${new Date().toISOString().slice(0, 10)}.json`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (e) {
      alert("Export failed: " + e.message);
    }
  }

  function handleLogout() {
    logout();
    navigate("/login");
  }

  return (
    <div className="flex flex-col gap-5">
      {/* Username */}
      <div className="rounded-xl border border-border bg-card p-5 shadow-sm dark:shadow-none">
        <h2 className="mb-4 font-heading text-sm font-semibold text-foreground">profile</h2>
        <div className="flex flex-col gap-3">
          <div className="flex flex-col gap-1">
            <label className="text-xs text-muted-foreground">username</label>
            <form onSubmit={handleSaveUsername} className="flex gap-2">
              <Input value={username} onChange={(e) => setUsername(e.target.value)} className="h-8 text-sm" />
              <Button type="submit" size="sm" disabled={saving}>
                {saved ? "saved!" : saving ? "…" : "save"}
              </Button>
            </form>
            {error && <p className="text-xs text-destructive">{error}</p>}
          </div>
          <div className="flex flex-col gap-1">
            <label className="text-xs text-muted-foreground">email</label>
            <p className="text-sm text-foreground">{profile.email}</p>
          </div>
          {formatMemberSince(profile.created_at) && (
            <div className="flex flex-col gap-1">
              <label className="text-xs text-muted-foreground">member since</label>
              <p className="text-sm text-foreground">{formatMemberSince(profile.created_at)}</p>
            </div>
          )}
        </div>
      </div>

      {/* Appearance */}
      <div className="rounded-xl border border-border bg-card p-5 shadow-sm dark:shadow-none">
        <h2 className="mb-4 font-heading text-sm font-semibold text-foreground">appearance</h2>
        <div className="flex items-center justify-between">
          <span className="text-sm text-foreground">theme</span>
          <ThemeToggle />
        </div>
      </div>

      {/* Data */}
      <div className="rounded-xl border border-border bg-card p-5 shadow-sm dark:shadow-none">
        <h2 className="mb-4 font-heading text-sm font-semibold text-foreground">data</h2>
        <div className="flex flex-col gap-3">
          <div className="flex items-center justify-between">
            <div className="flex flex-col">
              <span className="text-sm text-foreground">export library</span>
              <span className="text-xs text-muted-foreground">download your books as JSON</span>
            </div>
            <Button variant="outline" size="sm" onClick={handleExport}>export</Button>
          </div>
        </div>
      </div>

      {/* Session */}
      <div className="rounded-xl border border-border bg-card p-5 shadow-sm dark:shadow-none">
        <h2 className="mb-4 font-heading text-sm font-semibold text-foreground">session</h2>
        <Button variant="destructive" size="sm" onClick={handleLogout}>sign out</Button>
      </div>
    </div>
  );
}

// ── Main page ─────────────────────────────────────────────────────────────────

export default function Profile() {
  const { user } = useAuth();
  const navigate  = useNavigate();

  const [profile, setProfile] = useState(null);
  const [stats, setStats]     = useState(null);
  const [tab, setTab]         = useState("stats");
  const [error, setError]     = useState(null);

  function load() {
    setError(null);
    Promise.all([profileApi.get(), statsApi.get()])
      .then(([p, s]) => { setProfile(p); setStats(s); })
      .catch((e) => setError(e.message));
  }

  useEffect(load, []);

  if (error) return (
    <div className="mx-auto w-full max-w-3xl px-4 py-8 sm:px-6"><ErrorBox message={error} onRetry={load} /></div>
  );

  if (!profile) return <Loading />;

  const initial = profile.username?.[0]?.toUpperCase() ?? "?";

  return (
    <div className="mx-auto flex w-full max-w-3xl flex-1 flex-col gap-8 px-4 py-6 sm:px-6 sm:py-8">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Avatar className="h-16 w-16">
          <AvatarFallback className="bg-primary/10 text-lg font-semibold text-primary">
            {initial}
          </AvatarFallback>
        </Avatar>
        <div className="flex flex-col">
          <h1 className="font-heading text-xl font-bold text-foreground">{profile.username}</h1>
          {formatMemberSince(profile.created_at) && (
            <span className="text-sm text-muted-foreground">member since {formatMemberSince(profile.created_at)}</span>
          )}
        </div>
      </div>

      {/* Tab toggle */}
      <div className="flex w-fit items-center gap-1 rounded-full border border-border bg-card p-1">
        {["stats", "settings"].map((t) => (
          <button key={t} onClick={() => setTab(t)}
            className={`rounded-full px-4 py-1.5 text-xs font-medium transition-colors ${
              tab === t ? "bg-primary text-primary-foreground" : "text-muted-foreground hover:text-foreground"
            }`}>
            {t}
          </button>
        ))}
      </div>

      {/* Stats tab */}
      {tab === "stats" && stats && (
        <div className="flex flex-col gap-6">
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
            <StatCard icon={BookOpen}       label="books owned"       value={stats.books_owned}                to="/?status=available" />
            <StatCard icon={BookCheck}      label="books read"        value={stats.books_read}                 to="/?status=read" />
            <StatCard icon={Eye}            label="currently reading" value={stats.currently_reading}          to="/?status=reading" />
            <StatCard icon={FileText}       label="pages read"        value={stats.pages_read.toLocaleString()} />
            <StatCard icon={Users}          label="authors"           value={stats.authors_in_collection} />
            <StatCard icon={MessageSquare}  label="reviews"           value={stats.reviews_logged} />
            <StatCard icon={ArrowRightLeft} label="lent out"          value={stats.books_lent}                 to="/?status=lent" />
            <StatCard icon={Heart}          label="wishlist"          value={stats.wishlist_count} />
          </div>

          {stats.genre_breakdown && Object.keys(stats.genre_breakdown).length > 0 && (
            <GenreBreakdown breakdown={stats.genre_breakdown} />
          )}
        </div>
      )}

      {/* Settings tab */}
      {tab === "settings" && <Settings profile={profile} />}
    </div>
  );
}
