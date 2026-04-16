"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import { Bell, Command as CommandIcon, Menu, Moon, Search, Settings, Sun, User } from "lucide-react";
import { useTheme } from "next-themes";

import { NotificationItem } from "@/components/dashboard/NotificationItem";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
  CommandSeparator,
  CommandShortcut
} from "@/components/ui/command";
import { Dialog, DialogContent } from "@/components/ui/dialog";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger
} from "@/components/ui/dropdown-menu";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { Sheet, SheetContent, SheetTitle, SheetTrigger } from "@/components/ui/sheet";
import { useAuth } from "@/context/AuthContext";
import { useDashboardFeed } from "@/hooks/useDashboardFeed";
import { useDashboardStore } from "@/lib/store";

const previewModeEnabled =
  process.env.NEXT_PUBLIC_PREVIEW_MODE === "true" || process.env.PREVIEW_MODE === "true";

const commandActions = [
  { label: "Brand Dashboard", href: "/dashboard/brand", shortcut: "G B" },
  { label: "Content Dashboard", href: "/dashboard/content", shortcut: "G C" },
  { label: "Create Post", href: "/dashboard/create", shortcut: "G P" },
  { label: "Analytics", href: "/dashboard/analytics", shortcut: "G A" },
  { label: "Posts", href: "/dashboard/posts", shortcut: "G O" },
  { label: "Scheduler", href: "/dashboard/scheduler", shortcut: "G S" },
  { label: "Settings", href: "/dashboard/settings", shortcut: "G T" }
] as const;

const getInitials = (name: string | null | undefined): string => {
  if (!name) {
    return "AR";
  }
  return name
    .split(" ")
    .map((token) => token[0])
    .join("")
    .slice(0, 2)
    .toUpperCase();
};

export function TopBar() {
  const pathname = usePathname();
  const router = useRouter();
  const { setTheme, resolvedTheme } = useTheme();

  const { user, logout } = useAuth();

  const commandPaletteOpen = useDashboardStore((state) => state.commandPaletteOpen);
  const setCommandPaletteOpen = useDashboardStore((state) => state.setCommandPaletteOpen);

  const { notifications, unreadCount } = useDashboardFeed();
  const markNotificationRead = useDashboardStore((state) => state.markNotificationRead);
  const markAllNotificationsRead = useDashboardStore((state) => state.markAllNotificationsRead);
  const dismissNotification = useDashboardStore((state) => state.dismissNotification);

  const [previewVisible, setPreviewVisible] = useState(true);

  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k") {
        event.preventDefault();
        setCommandPaletteOpen(true);
      }
    };

    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [setCommandPaletteOpen]);

  const crumbs = useMemo(() => {
    const segments = pathname
      .split("/")
      .filter(Boolean)
      .map((segment) => segment.replace(/-/g, " "));
    return segments;
  }, [pathname]);

  const isDark = resolvedTheme === "dark";

  return (
    <>
      <header className="sticky top-0 z-30 border-b border-[var(--border)] bg-[color-mix(in_srgb,var(--bg-surface)_86%,transparent)] backdrop-blur">
        {previewModeEnabled && previewVisible ? (
          <div className="flex items-center justify-between border-b border-amber-500/30 bg-amber-500/10 px-4 py-2 text-xs text-amber-700">
            <span>Preview mode is enabled. Data is static and does not persist.</span>
            <Button variant="ghost" size="sm" onClick={() => setPreviewVisible(false)} className="h-7 px-2 text-amber-700">
              Dismiss
            </Button>
          </div>
        ) : null}

        <div className="flex h-16 items-center justify-between gap-3 px-4">
          <div className="flex items-center gap-3">
            <Sheet>
              <SheetTrigger asChild>
                <Button variant="ghost" size="icon" className="lg:hidden" aria-label="Open navigation">
                  <Menu className="h-5 w-5" />
                </Button>
              </SheetTrigger>
              <SheetContent side="left" className="w-[280px]">
                <SheetTitle className="text-transparent bg-gradient-to-r from-teal-500 to-sky-500 bg-clip-text">ARIA</SheetTitle>
                <nav className="mt-6 space-y-2">
                  {commandActions.map((item) => (
                    <Link key={item.href} href={item.href} className="block rounded-lg px-3 py-2 text-sm text-[var(--text-secondary)] hover:bg-[var(--bg-elevated)]">
                      {item.label}
                    </Link>
                  ))}
                </nav>
              </SheetContent>
            </Sheet>

            <div>
              <p className="text-xs text-[var(--text-muted)]">Dashboard</p>
              <p className="text-sm font-semibold capitalize text-[var(--text-primary)]">{crumbs.join(" / ") || "overview"}</p>
            </div>
          </div>

          <div className="flex items-center gap-1 sm:gap-2">
            <Button variant="outline" size="sm" onClick={() => setCommandPaletteOpen(true)} className="hidden sm:inline-flex">
              <Search className="h-4 w-4" />
              Search
              <span className="ml-1 inline-flex items-center rounded border border-[var(--border)] px-1 py-0.5 text-[10px] text-[var(--text-muted)]">
                <CommandIcon className="h-2.5 w-2.5" />K
              </span>
            </Button>

            <Popover>
              <PopoverTrigger asChild>
                <Button variant="ghost" size="icon" className="relative">
                  <Bell className="h-5 w-5" />
                  {unreadCount > 0 ? (
                    <span className="absolute right-1 top-1 grid h-4 min-w-4 place-items-center rounded-full bg-[var(--danger)] px-1 text-[10px] font-semibold text-white">
                      {unreadCount}
                    </span>
                  ) : null}
                </Button>
              </PopoverTrigger>
              <PopoverContent align="end" className="w-[360px] p-0">
                <div className="flex items-center justify-between border-b border-[var(--border)] px-4 py-3">
                  <p className="text-sm font-semibold">Notifications</p>
                  <Button variant="ghost" size="sm" onClick={markAllNotificationsRead}>
                    Mark all as read
                  </Button>
                </div>
                <div className="max-h-[340px] space-y-2 overflow-y-auto p-3">
                  {notifications.length ? (
                    notifications.map((item) => (
                      <NotificationItem
                        key={item.id}
                        notification={item}
                        onRead={markNotificationRead}
                        onDismiss={dismissNotification}
                      />
                    ))
                  ) : (
                    <p className="py-10 text-center text-sm text-[var(--text-muted)]">No notifications</p>
                  )}
                </div>
              </PopoverContent>
            </Popover>

            <Button
              variant="ghost"
              size="icon"
              onClick={() => setTheme(isDark ? "light" : "dark")}
              aria-label="Toggle theme"
            >
              {isDark ? <Sun className="h-5 w-5" /> : <Moon className="h-5 w-5" />}
            </Button>

            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" size="icon" className="rounded-full">
                  <Avatar className="h-8 w-8">
                    <AvatarFallback>{getInitials(user?.name)}</AvatarFallback>
                  </Avatar>
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-48">
                <DropdownMenuItem>
                  <User className="mr-2 h-4 w-4" />
                  Profile
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => router.push("/dashboard/settings")}>
                  <Settings className="mr-2 h-4 w-4" />
                  Settings
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={logout}>Logout</DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </div>
      </header>

      <Dialog open={commandPaletteOpen} onOpenChange={setCommandPaletteOpen}>
        <DialogContent className="p-0">
          <Command>
            <CommandInput placeholder="Type a command or search page..." />
            <CommandList>
              <CommandEmpty>No results found.</CommandEmpty>
              <CommandGroup heading="Navigate">
                {commandActions.map((item) => (
                  <CommandItem
                    key={item.href}
                    onSelect={() => {
                      setCommandPaletteOpen(false);
                      router.push(item.href);
                    }}
                  >
                    {item.label}
                    <CommandShortcut>{item.shortcut}</CommandShortcut>
                  </CommandItem>
                ))}
              </CommandGroup>
              <CommandSeparator />
              <CommandGroup heading="Quick">
                <CommandItem
                  onSelect={() => {
                    setTheme(isDark ? "light" : "dark");
                  }}
                >
                  Toggle Theme
                  <CommandShortcut>{isDark ? "Dark" : "Light"}</CommandShortcut>
                </CommandItem>
              </CommandGroup>
            </CommandList>
          </Command>
        </DialogContent>
      </Dialog>
    </>
  );
}
