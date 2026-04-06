import { Link } from "react-router-dom";
import {
  BookOpen,
  BookCheck,
  Eye,
  FileText,
  Users,
  MessageSquare,
  ArrowRightLeft,
  Heart,
} from "lucide-react";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";

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
      <span className="mt-0.5 shrink-0 text-xs text-muted-foreground w-16">
        {item.when}
      </span>
      <span className="text-sm text-foreground">
        {item.action}{" "}
        {item.bookId && (
          <Link
            to={`/book/${item.bookId}`}
            className="font-medium text-primary hover:underline"
          >
            "{item.bookTitle}"
          </Link>
        )}
        {item.extra && (
          <span className="text-muted-foreground"> {item.extra}</span>
        )}
      </span>
    </div>
  );
}

export default function Profile() {
  // TODO: calculate from real store data
  const stats = {
    booksOwned: 0,
    booksRead: 0,
    currentlyReading: 0,
    pagesRead: 0,
    authors: 0,
    reviews: 0,
    lentOut: 0,
    wishlist: 0,
  };

  // TODO: generate from real activity log
  const activity = [];

  return (
    <div className="mx-auto flex w-full max-w-3xl flex-1 flex-col gap-8 px-6 py-8">
      {/* Profile Header */}
      <div className="flex items-center gap-4">
        <Avatar className="h-16 w-16">
          <AvatarFallback className="bg-primary/10 text-lg font-semibold text-primary">
            V
          </AvatarFallback>
        </Avatar>
        <div className="flex flex-col">
          <h1 className="font-heading text-xl font-bold text-foreground">
            vishcrv
          </h1>
          <span className="text-sm text-muted-foreground">
            member since march 2026
          </span>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <StatCard icon={BookOpen} label="books owned" value={stats.booksOwned} />
        <StatCard icon={BookCheck} label="books read" value={stats.booksRead} />
        <StatCard icon={Eye} label="currently reading" value={stats.currentlyReading} />
        <StatCard icon={FileText} label="pages read" value={stats.pagesRead.toLocaleString()} />
        <StatCard icon={Users} label="authors" value={stats.authors} />
        <StatCard icon={MessageSquare} label="reviews" value={stats.reviews} />
        <StatCard icon={ArrowRightLeft} label="lent out" value={stats.lentOut} />
        <StatCard icon={Heart} label="wishlist" value={stats.wishlist} />
      </div>

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
