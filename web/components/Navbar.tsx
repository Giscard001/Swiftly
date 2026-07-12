"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Layers } from "lucide-react";
import { ThemeToggle } from "./ThemeToggle";
import { cn } from "@/lib/utils";

const NAV = [
  { href: "/", label: "Convertir" },
  { href: "/tools", label: "Outils" },
  { href: "/dashboard", label: "Historique" },
  { href: "/api-docs", label: "API" },
];

export function Navbar() {
  const pathname = usePathname();
  return (
    <header className="sticky top-0 z-40 border-b border-black/5 bg-white/70 backdrop-blur-xl dark:border-white/10 dark:bg-[#0a0e1a]/70">
      <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-4 sm:px-6">
        <Link href="/" className="group flex items-center gap-2.5 font-semibold">
          <span className="grid h-9 w-9 place-items-center rounded-xl bg-gradient-to-br from-brand-500 to-brand-700 text-white shadow-lg shadow-brand-600/25 transition group-hover:shadow-brand-600/40">
            <Layers className="h-5 w-5" />
          </span>
          <span className="text-[15px] tracking-tight">FilesConvert</span>
        </Link>
        <nav className="flex items-center gap-0.5">
          {NAV.map((item) => {
            const active = pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "relative h-9 rounded-lg px-3.5 text-sm font-medium transition",
                  active
                    ? "text-brand-600 dark:text-brand-400"
                    : "text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-gray-100"
                )}
              >
                {item.label}
                {active && (
                  <span className="absolute inset-x-3 -bottom-px h-0.5 rounded-full bg-brand-600 dark:bg-brand-400" />
                )}
              </Link>
            );
          })}
          <div className="ml-2 h-6 w-px bg-black/10 dark:bg-white/10" />
          <ThemeToggle />
        </nav>
      </div>
    </header>
  );
}
