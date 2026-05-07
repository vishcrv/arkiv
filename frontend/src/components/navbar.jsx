import { useRef, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Search, BookOpen, X, Menu } from "lucide-react";
import { ThemeToggle } from "@/components/theme-toggle";
import { Input } from "@/components/ui/input";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { useAuth } from "@/lib/auth";

export function Navbar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const [searchOpen, setSearchOpen] = useState(false);
  const [searchQ, setSearchQ]       = useState("");
  const [menuOpen, setMenuOpen]     = useState(false);
  const inputRef = useRef(null);

  const initial = user?.username?.[0]?.toUpperCase() ?? "?";

  function handleSearchSubmit(e) {
    e.preventDefault();
    if (!searchQ.trim()) return;
    navigate(`/?q=${encodeURIComponent(searchQ.trim())}`);
    setSearchOpen(false);
    setSearchQ("");
  }

  function handleLogout() {
    logout();
    navigate("/login");
  }

  return (
    <nav className="sticky top-0 z-50 border-b border-border bg-background/80 backdrop-blur-sm">
      <div className="mx-auto flex h-14 max-w-6xl items-center justify-between px-4 sm:px-6">
        {/* Logo */}
        <Link
          to="/"
          className="flex items-center gap-2 text-foreground transition-opacity hover:opacity-80"
        >
          <BookOpen className="h-5 w-5 text-primary" />
          <span className="font-heading text-lg font-semibold tracking-tight">arkiv</span>
        </Link>

        {/* Center Nav — desktop */}
        <div className="hidden items-center gap-8 sm:flex">
          <Link
            to="/"
            className="text-sm font-medium text-muted-foreground transition-colors hover:text-foreground"
          >
            home
          </Link>
          <Link
            to="/discover"
            className="text-sm font-medium text-muted-foreground transition-colors hover:text-foreground"
          >
            discover
          </Link>
          <Link
            to="/activity"
            className="text-sm font-medium text-muted-foreground transition-colors hover:text-foreground"
          >
            activity
          </Link>
        </div>

        {/* Right Side */}
        <div className="flex items-center gap-2 sm:gap-3">
          {/* Search */}
          {searchOpen ? (
            <form onSubmit={handleSearchSubmit} className="flex items-center gap-2">
              <Input
                ref={inputRef}
                type="text"
                placeholder="search your library…"
                className="h-8 w-40 bg-card text-sm sm:w-56"
                autoFocus
                value={searchQ}
                onChange={(e) => setSearchQ(e.target.value)}
              />
              <button
                type="button"
                onClick={() => { setSearchOpen(false); setSearchQ(""); }}
                className="rounded-md p-1 text-muted-foreground transition-colors hover:text-foreground"
              >
                <X className="h-4 w-4" />
              </button>
            </form>
          ) : (
            <button
              onClick={() => setSearchOpen(true)}
              className="rounded-md p-2 text-muted-foreground transition-colors hover:text-foreground"
            >
              <Search className="h-4 w-4" />
            </button>
          )}

          <ThemeToggle />

          {/* Profile Dropdown — desktop */}
          <div className="hidden sm:block">
            <DropdownMenu>
              <DropdownMenuTrigger className="rounded-full outline-none ring-ring focus-visible:ring-2">
                <Avatar className="h-8 w-8 cursor-pointer">
                  <AvatarFallback className="bg-primary/10 text-xs font-medium text-primary">
                    {initial}
                  </AvatarFallback>
                </Avatar>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-44">
                {user && (
                  <div className="px-2 py-1.5 text-xs text-muted-foreground truncate">
                    {user.username}
                  </div>
                )}
                <DropdownMenuSeparator />
                <DropdownMenuItem render={<Link to="/profile" />}>
                  profile
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem
                  className="text-destructive"
                  onClick={handleLogout}
                >
                  logout
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>

          {/* Hamburger — mobile */}
          <button
            onClick={() => setMenuOpen((o) => !o)}
            className="rounded-md p-2 text-muted-foreground transition-colors hover:text-foreground sm:hidden"
            aria-label="menu"
          >
            {menuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </button>
        </div>
      </div>

      {/* Mobile menu */}
      {menuOpen && (
        <div className="border-t border-border bg-background/95 px-4 py-3 sm:hidden">
          <div className="flex flex-col gap-1">
            <Link
              to="/"
              onClick={() => setMenuOpen(false)}
              className="rounded-md px-3 py-2 text-sm font-medium text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
            >
              home
            </Link>
            <Link
              to="/discover"
              onClick={() => setMenuOpen(false)}
              className="rounded-md px-3 py-2 text-sm font-medium text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
            >
              discover
            </Link>
          <Link
              to="/activity"
              onClick={() => setMenuOpen(false)}
              className="rounded-md px-3 py-2 text-sm font-medium text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
            >
              activity
            </Link>
            <Link
              to="/profile"
              onClick={() => setMenuOpen(false)}
              className="rounded-md px-3 py-2 text-sm font-medium text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
            >
              profile
            </Link>
            <button
              onClick={() => { setMenuOpen(false); handleLogout(); }}
              className="rounded-md px-3 py-2 text-left text-sm font-medium text-destructive transition-colors hover:bg-destructive/10"
            >
              logout
            </button>
          </div>
        </div>
      )}
    </nav>
  );
}
