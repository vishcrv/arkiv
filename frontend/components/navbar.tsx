"use client";

import { useState } from "react";
import Link from "next/link";
import { Search, BookOpen, X } from "lucide-react";
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

export function Navbar() {
  const [searchOpen, setSearchOpen] = useState(false);

  return (
    <nav className="sticky top-0 z-50 border-b border-border bg-background/80 backdrop-blur-sm">
      <div className="mx-auto flex h-14 max-w-6xl items-center justify-between px-6">
        {/* Logo */}
        <Link
          href="/"
          className="flex items-center gap-2 text-foreground transition-opacity hover:opacity-80"
        >
          <BookOpen className="h-5 w-5 text-primary" />
          <span className="font-heading text-lg font-semibold tracking-tight">
            arkiv
          </span>
        </Link>

        {/* Center Nav */}
        <div className="flex items-center gap-8">
          <Link
            href="/"
            className="text-sm font-medium text-muted-foreground transition-colors hover:text-foreground"
          >
            home
          </Link>
          <Link
            href="/discover"
            className="text-sm font-medium text-muted-foreground transition-colors hover:text-foreground"
          >
            discover
          </Link>
        </div>

        {/* Right Side */}
        <div className="flex items-center gap-3">
          {/* Search Toggle */}
          {searchOpen ? (
            <div className="flex items-center gap-2">
              <Input
                type="text"
                placeholder="search your library..."
                className="h-8 w-56 bg-card text-sm"
                autoFocus
              />
              <button
                onClick={() => setSearchOpen(false)}
                className="rounded-md p-1 text-muted-foreground transition-colors hover:text-foreground"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
          ) : (
            <button
              onClick={() => setSearchOpen(true)}
              className="rounded-md p-2 text-muted-foreground transition-colors hover:text-foreground"
            >
              <Search className="h-4 w-4" />
            </button>
          )}

          {/* Theme Toggle */}
          <ThemeToggle />

          {/* Profile Dropdown */}
          <DropdownMenu>
            <DropdownMenuTrigger className="rounded-full outline-none ring-ring focus-visible:ring-2">
              <Avatar className="h-8 w-8 cursor-pointer">
                <AvatarFallback className="bg-primary/10 text-xs font-medium text-primary">
                  V
                </AvatarFallback>
              </Avatar>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-44">
              <DropdownMenuItem render={<Link href="/profile" />}>
                profile
              </DropdownMenuItem>
              <DropdownMenuItem>settings</DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem className="text-destructive">
                logout
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>
    </nav>
  );
}
