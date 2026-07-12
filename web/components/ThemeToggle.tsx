"use client";

import { Moon, Sun } from "lucide-react";
import { useTheme } from "next-themes";
import { useEffect, useState } from "react";

export function ThemeToggle() {
  const { theme, setTheme } = useTheme();
  const [mounted, setMounted] = useState(false);
  useEffect(() => setMounted(true), []);
  if (!mounted) return <span className="h-9 w-9" />;
  const isDark = theme === "dark";
  return (
    <button
      type="button"
      aria-label="Changer de thème"
      onClick={() => setTheme(isDark ? "light" : "dark")}
      className="btn-ghost h-9 w-9 rounded-full p-0"
    >
      {isDark ? <Sun className="h-5 w-5" /> : <Moon className="h-5 w-5" />}
    </button>
  );
}
