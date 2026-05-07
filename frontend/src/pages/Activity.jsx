import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import {
  BookPlus, Heart, HeartOff, BookOpen, BookCheck,
  Star, ArrowRightLeft, Tag, User, Activity as ActivityIcon,
} from "lucide-react";
import { activityApi } from "@/lib/api";
import { Loading, ErrorBox } from "@/components/states";

const ACTION_META = {
  added:            { icon: BookPlus,        label: "added to library",    color: "text-primary" },
  wishlist_added:   { icon: Heart,           label: "added to wishlist",   color: "text-rose-500" },
  wishlist_removed: { icon: HeartOff,        label: "removed from wishlist", color: "text-muted-foreground" },
  started_reading:  { icon: BookOpen,        label: "started reading",     color: "text-blue-500" },
  finished_reading: { icon: BookCheck,       label: "finished",            color: "text-green-600" },
  rated:            { icon: Star,            label: "rated",               color: "text-amber-500" },
  lent:             { icon: ArrowRightLeft,  label: "lent",                color: "text-orange-500" },
  returned:         { icon: ArrowRightLeft,  label: "returned",            color: "text-muted-foreground" },
  sold:             { icon: Tag,             label: "sold",                color: "text-purple-500" },
  author_added:     { icon: User,            label: "author added",        color: "text-muted-foreground" },
};

function formatWhen(ts) {
  const diff = Date.now() - new Date(ts).getTime();
  const mins  = Math.floor(diff / 60000);
  const hours = Math.floor(diff / 3600000);
  const days  = Math.floor(diff / 86400000);
  if (mins < 1)   return "just now";
  if (mins < 60)  return `${mins}m ago`;
  if (hours < 24) return `${hours}h ago`;
  if (days === 1) return "yesterday";
  if (days < 30)  return `${days}d ago`;
  if (days < 365) return `${Math.floor(days / 30)}mo ago`;
  return `${Math.floor(days / 365)}y ago`;
}

function formatDate(ts) {
  return new Date(ts).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
}

function groupByDate(items) {
  const groups = {};
  for (const item of items) {
    const key = new Date(item.timestamp).toDateString();
    if (!groups[key]) groups[key] = [];
    groups[key].push(item);
  }
  return Object.entries(groups);
}

function ActivityRow({ item }) {
  const meta = ACTION_META[item.action] || { icon: ActivityIcon, label: item.action, color: "text-muted-foreground" };
  const Icon = meta.icon;

  return (
    <div className="flex items-start gap-3 py-2.5">
      <div className={`mt-0.5 shrink-0 ${meta.color}`}>
        <Icon className="h-4 w-4" />
      </div>
      <div className="flex flex-1 flex-col gap-0.5 min-w-0">
        <span className="text-sm text-foreground">
          {item.isbn ? (
            <Link to={`/book/${item.isbn}`} className="font-medium text-primary hover:underline">
              {item.detail}
            </Link>
          ) : (
            item.detail
          )}
        </span>
        <span className="text-xs text-muted-foreground">{formatWhen(item.timestamp)}</span>
      </div>
    </div>
  );
}

export default function ActivityPage() {
  const [activity, setActivity] = useState([]);
  const [loading, setLoading]   = useState(true);
  const [error, setError]       = useState(null);

  function load() {
    setLoading(true);
    setError(null);
    activityApi.get(200)
      .then(setActivity)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }

  useEffect(load, []);

  if (loading) return (
    <div className="mx-auto w-full max-w-2xl px-4 py-8 sm:px-6"><Loading /></div>
  );

  if (error) return (
    <div className="mx-auto w-full max-w-2xl px-4 py-8 sm:px-6"><ErrorBox message={error} onRetry={load} /></div>
  );

  const groups = groupByDate(activity);

  return (
    <div className="mx-auto flex w-full max-w-2xl flex-1 flex-col gap-6 px-4 py-6 sm:px-6 sm:py-8">
      <div>
        <h1 className="font-heading text-2xl font-bold text-foreground">activity</h1>
        <p className="mt-0.5 text-sm text-muted-foreground">your reading journal</p>
      </div>

      {activity.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-24 text-center">
          <ActivityIcon className="mb-4 h-10 w-10 text-muted-foreground/40" />
          <p className="font-heading text-base font-medium text-foreground">no activity yet</p>
          <p className="mt-1 text-sm text-muted-foreground">start adding books to build your log</p>
        </div>
      ) : (
        <div className="flex flex-col gap-6">
          {groups.map(([dateKey, items]) => (
            <div key={dateKey}>
              <div className="mb-1 text-xs font-medium text-muted-foreground">
                {formatDate(items[0].timestamp)}
              </div>
              <div className="rounded-xl border border-border bg-card px-4 shadow-sm dark:shadow-none divide-y divide-border">
                {items.map((item, i) => (
                  <ActivityRow key={i} item={item} />
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
