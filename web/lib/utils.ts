import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatBytes(bytes: number): string {
  if (!bytes) return "0 o";
  const units = ["o", "Ko", "Mo", "Go", "To"];
  const i = Math.floor(Math.log(bytes) / Math.log(1024));
  return `${(bytes / Math.pow(1024, i)).toFixed(i === 0 ? 0 : 1)} ${units[i]}`;
}

export function timeAgo(ts: number): string {
  const s = Math.floor((Date.now() / 1000 - ts));
  if (s < 60) return "il y a quelques secondes";
  const m = Math.floor(s / 60);
  if (m < 60) return `il y a ${m} min`;
  const h = Math.floor(m / 60);
  if (h < 24) return `il y a ${h} h`;
  const d = Math.floor(h / 24);
  return `il y a ${d} j`;
}

export function detectExt(filename: string): string {
  const n = filename.toLowerCase();
  const compound = ["tar.gz", "tar.bz2", "tar.xz"];
  for (const c of compound) if (n.endsWith(c)) return c;
  const i = n.lastIndexOf(".");
  return i >= 0 ? n.slice(i + 1) : "";
}
