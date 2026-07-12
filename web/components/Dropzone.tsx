"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { UploadCloud, X } from "lucide-react";
import { detectExt, formatBytes } from "@/lib/utils";
import { isImageExt } from "@/lib/media";

type Props = {
  onFiles: (files: File[]) => void;
  multiple?: boolean;
  accept?: string;
};

export function Dropzone({ onFiles, multiple = true, accept }: Props) {
  const [drag, setDrag] = useState(false);
  const [files, setFiles] = useState<File[]>([]);
  const inputRef = useRef<HTMLInputElement>(null);

  const handle = useCallback(
    (list: FileList | null) => {
      if (!list || list.length === 0) return;
      const arr = Array.from(list);
      setFiles((prev) => (multiple ? [...prev, ...arr] : [arr[0]]));
      onFiles(arr);
    },
    [multiple, onFiles]
  );

  const remove = (i: number) => {
    setFiles((prev) => prev.filter((_, idx) => idx !== i));
  };

  return (
    <div>
      <div
        onDragOver={(e) => {
          e.preventDefault();
          setDrag(true);
        }}
        onDragLeave={() => setDrag(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDrag(false);
          handle(e.dataTransfer.files);
        }}
        onClick={() => inputRef.current?.click()}
        className={`group relative flex cursor-pointer flex-col items-center justify-center gap-4 overflow-hidden rounded-2xl border-2 border-dashed p-12 text-center transition-all duration-200 ${
          drag
            ? "scale-[1.01] border-brand-500 bg-brand-50/60 dark:bg-brand-500/10"
            : "border-gray-300 hover:border-brand-400 hover:bg-gray-50/60 dark:border-white/15 dark:hover:border-brand-400/70 dark:hover:bg-white/[0.02]"
        }`}
      >
        <div
          className={`grid h-16 w-16 place-items-center rounded-2xl transition-all duration-200 ${
            drag
              ? "scale-110 bg-brand-600 text-white"
              : "bg-brand-50 text-brand-600 group-hover:scale-105 dark:bg-brand-500/10 dark:text-brand-400"
          }`}
        >
          <UploadCloud className="h-8 w-8" />
        </div>
        <div>
          <p className="text-base font-semibold">Glissez-déposez vos fichiers ici</p>
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
            ou cliquez pour parcourir — détection automatique du format
          </p>
        </div>
        <input
          ref={inputRef}
          type="file"
          className="hidden"
          multiple={multiple}
          accept={accept}
          onChange={(e) => {
            handle(e.target.files);
            e.currentTarget.value = "";
          }}
        />
      </div>

      {files.length > 0 && (
        <ul className="mt-4 space-y-2">
          {files.map((f, i) => (
            <li
              key={`${f.name}-${i}`}
              className="card flex items-center justify-between px-3.5 py-2.5 animate-fade-in-up"
            >
              <div className="flex min-w-0 items-center gap-3">
                <Thumb file={f} />
                <span className="badge bg-brand-50 font-semibold text-brand-700 ring-brand-200/60 dark:bg-brand-500/10 dark:text-brand-300 dark:ring-brand-500/20">
                  .{detectExt(f.name) || "?"}
                </span>
                <span className="truncate text-sm font-medium">{f.name}</span>
                <span className="text-xs text-gray-400">{formatBytes(f.size)}</span>
              </div>
              <button
                type="button"
                onClick={() => remove(i)}
                className="grid h-7 w-7 place-items-center rounded-full text-gray-400 transition hover:bg-rose-50 hover:text-rose-600 dark:hover:bg-rose-500/10"
                aria-label="Retirer"
              >
                <X className="h-4 w-4" />
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

export function useDropzoneFiles() {
  const [files, setFiles] = useState<File[]>([]);
  const onFiles = useCallback((arr: File[]) => setFiles(arr), []);
  return { files, onFiles };
}

function Thumb({ file }: { file: File }) {
  const src = useObjectUrl(file);
  const ext = detectExt(file.name);
  if (!isImageExt(ext) || !src) {
    return <span className="h-9 w-9 shrink-0 rounded-md bg-gray-100 dark:bg-white/10" />;
  }
  return (
    // eslint-disable-next-line @next/next/no-img-element -- blob: URL not optimizable by next/image
    <img
      src={src}
      alt={file.name}
      className="h-9 w-9 shrink-0 rounded-md object-cover ring-1 ring-black/5 dark:ring-white/10"
    />
  );
}

function useObjectUrl(file: File): string | null {
  const [url, setUrl] = useState<string | null>(null);
  useEffect(() => {
    if (typeof URL === "undefined") return;
    if (!(file instanceof File)) return;
    const u = URL.createObjectURL(file);
    setUrl(u);
    return () => URL.revokeObjectURL(u);
  }, [file]);
  return url;
}
