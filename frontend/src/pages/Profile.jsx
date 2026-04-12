import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import {
  BookOpen, BookCheck, Eye, FileText,
  Users, MessageSquare, ArrowRightLeft, Heart,
} from "lucide-react";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { profileApi, activityApi } from "@/lib/api";
import { Loading, ErrorBox } from "@/components/states";

function formatWhen(timestamp) {
  const diffMs = Date.now() - new Date(timestamp).getTime();
  const days = Math.floor(diffMs / 86400000);
  if (days === 0) return "today";
  if (days === 1) return "1d ago";
  if (days < 30) return `${days}d ago`;
  if (days < 365) return `${Math.floor(days / 30)}mo ago`;
  return `${Math.floor(days / 365)}y ago`;
}

function formatMemberSince(isoDate) {
  if (!isoDate || isoDate.startsWith("1970")) return null;
  return new Date(isoDate)
    .toLocaleDateString("en-US", { month: "long", year: "numeric" })
    .toLowerCase();
}

function StatCard({ icon: Icon, label, value }) {
  return (
    <div className="flex items-center gap-3 rounded-xl border border-border bg-card p-4 shadow-[0_1px_3px_0_rgba(44,37,32,0.04),0_0_0_1px_rgba(44,37,32,0.02)] dark:shadow-none">
      <Icon className="h-4 w-4 text-muted-foreground" />
      <div className="flex flex-col">
        <span className="text-lg font-semibold text-foreground">{value}</span>
        <span className="text-xs text-muted-foreground">{label}</span>
      </div>
    </div>
  );
}

function ActivityItem({ item }) {
  return (
    <div className="flex items-start gap-3 py-2">
      <span className="mt-0.5 w-16 shrink-0 text-xs text-muted-foreground">
        {formatWhen(item.timestamp)}
      </span>
      <span className="text-sm text-foreground">
        {item.isbn ? (
          <Link
            to={`/book/${item.isbn}`}
            className="font-medium text-primary hover:underline"
          >
            {item.detail}
          </Link>
        ) : (
          item.detail
        )}
      </span>
    </div>
  );
}

export default function Profile() {
  const [profile, setProfile] = useState(null);
  const [stats, setStats] = useState(null);
  const [activity, setActivity] = useState([]);
  const [error, setError] = useState(null);

  function load() {
    setError(null);
    Promise.all([profileApi.get(), activityApi.get()])
      .then(([p, a]) => {
        setProfile(p);
        setStats(p.stats);
        setActivity(a);
      })
      .catch((e) => setError(e.message));
  }

  useEffect(load, []);

  if (error) {
    return (
      <div className="mx-auto flex w-full max-w-3xl flex-1 flex-col px-6 py-8">
        <ErrorBox message={error} onRetry={load} />
      </div>
    );
  }

  if (!profile) return <Loading />;

  const memberSince = formatMemberSince(profile.created_at);
  const initial = profile.username?.[0]?.toUpperCase() ?? "?";

  return (
    <div className="mx-auto flex w-full max-w-3xl flex-1 flex-col gap-8 px-6 py-8">
      {/* Profile Header */}
      <div className="flex items-center gap-4">
        <Avatar className="h-16 w-16">
          <AvatarFallback className="bg-primary/10 text-lg font-semibold text-primary">
            {initial}
          </AvatarFallback>
        </Avatar>
        <div className="flex flex-col">
          <h1 className="font-heading text-xl font-bold text-foreground">
            {profile.username}
          </h1>
          {memberSince && (
            <span className="text-sm text-muted-foreground">
              member since {memberSince}
            </span>
          )}
        </div>
      </div>

      {/* Stats Grid */}
      {stats && (
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          <StatCard icon={BookOpen}        label="books owned"       value={stats.books_owned} />
          <StatCard icon={BookCheck}       label="books read"        value={stats.books_read} />
          <StatCard icon={Eye}             label="currently reading" value={stats.currently_reading} />
          <StatCard icon={FileText}        label="pages read"        value={stats.pages_read.toLocaleString()} />
          <StatCard icon={Users}           label="authors"           value={stats.authors_in_collection} />
          <StatCard icon={MessageSquare}   label="reviews"           value={stats.reviews_logged} />
          <StatCard icon={ArrowRightLeft}  label="lent out"          value={stats.books_lent} />
          <StatCard icon={Heart}           label="wishlist"          value={stats.wishlist_count} />
        </div>
      )}

      {/* Recent Activity */}
      <div className="rounded-xl border border-border bg-card p-5 shadow-[0_1px_3px_0_rgba(44,37,32,0.04),0_0_0_1px_rgba(44,37,32,0.02)] dark:shadow-none">
        <h2 className="mb-3 font-heading text-sm font-semibold text-foreground">
          recent activity
        </h2>
        {activity.length === 0 ? (
          <p className="py-6 text-center text-sm text-muted-foreground">
            no activity yet — start adding books to your collection
          </p>
        ) : (
          <div className="flex flex-col divide-y divide-border">
            {activity.map((item, i) => (
              <ActivityItem key={i} item={item} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
