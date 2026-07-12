export const IMG_EXTS = new Set([
  "png", "jpg", "jpeg", "webp", "gif", "bmp", "tiff", "tif", "heic",
]);

export function isImageExt(ext: string | null | undefined): boolean {
  return !!ext && IMG_EXTS.has(ext.toLowerCase());
}

export function extOf(name: string | null | undefined): string {
  if (!name) return "";
  const n = name.toLowerCase();
  const i = n.lastIndexOf(".");
  return i >= 0 ? n.slice(i + 1) : "";
}
