export const CATEGORY_META: Record<string, { label: string; icon: string; color: string }> = {
  image: { label: "Image", icon: "🖼️", color: "text-emerald-500" },
  document: { label: "Document", icon: "📄", color: "text-blue-500" },
  audio: { label: "Audio", icon: "🎵", color: "text-purple-500" },
  video: { label: "Vidéo", icon: "🎬", color: "text-rose-500" },
  data: { label: "Données", icon: "📊", color: "text-amber-500" },
  archive: { label: "Archive", icon: "🗜️", color: "text-cyan-500" },
};

export function categoryLabel(cat: string): string {
  return CATEGORY_META[cat]?.label ?? cat;
}

export function categoryIcon(cat: string): string {
  return CATEGORY_META[cat]?.icon ?? "📦";
}

export function extLabel(ext: string): string {
  return ext.toUpperCase();
}
