"use client";

import { useEffect, useRef, useState } from "react";
import { CheckCircle2, Download, Loader2, XCircle, Clock, Eye } from "lucide-react";
import { getJob, jobDownloadUrl, CONVERTER_URL, type Job } from "@/lib/converter-client";
import { cn } from "@/lib/utils";
import { isImageExt, extOf } from "@/lib/media";

type Props = { jobId: string; previewFile?: File };

export function ConversionProgress({ jobId, previewFile }: Props) {
  const [job, setJob] = useState<Job | null>(null);
  const [preview, setPreview] = useState(false);
  const timer = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    let alive = true;
    const poll = async () => {
      try {
        const j = await getJob(jobId);
        if (!alive) return;
        setJob(j);
        if (j.status === "completed" || j.status === "failed" || j.status === "expired") {
          if (timer.current) clearInterval(timer.current);
        }
      } catch {
        if (timer.current) clearInterval(timer.current);
      }
    };
    poll();
    timer.current = setInterval(poll, 1500);
    return () => {
      alive = false;
      if (timer.current) clearInterval(timer.current);
    };
  }, [jobId]);

  const done = job?.status === "completed";
  const failed = job?.status === "failed" || job?.status === "expired";
  const queued = job?.status === "queued";
  const targetExt = job?.target || extOf(job?.output_name);

  const srcUrl = useObjectUrl(previewFile);
  const outUrl = useDownloadBlobUrl(jobId, !!done && isImageExt(targetExt));
  const canPreview =
    (srcUrl && isImageExt(extOf(previewFile?.name))) || (outUrl && isImageExt(targetExt));

  if (!job) {
    return (
      <div className="card flex items-center gap-3 p-5">
        <Loader2 className="h-5 w-5 animate-spin text-brand-600" />
        <span className="text-sm">Démarrage…</span>
      </div>
    );
  }

  return (
    <>
      <div className="card overflow-hidden p-6">
        <div className="flex items-center justify-between gap-4">
          <div className="flex min-w-0 items-center gap-3.5">
            {done ? (
              <span className="grid h-11 w-11 shrink-0 place-items-center rounded-xl bg-emerald-50 text-emerald-600 dark:bg-emerald-500/10 dark:text-emerald-400">
                <CheckCircle2 className="h-6 w-6" />
              </span>
            ) : failed ? (
              <span className="grid h-11 w-11 shrink-0 place-items-center rounded-xl bg-rose-50 text-rose-600 dark:bg-rose-500/10 dark:text-rose-400">
                <XCircle className="h-6 w-6" />
              </span>
            ) : queued ? (
              <span className="grid h-11 w-11 shrink-0 place-items-center rounded-xl bg-gray-100 text-gray-500 dark:bg-white/10 dark:text-gray-400">
                <Clock className="h-6 w-6" />
              </span>
            ) : (
              <span className="grid h-11 w-11 shrink-0 place-items-center rounded-xl bg-brand-50 text-brand-600 dark:bg-brand-500/10 dark:text-brand-400">
                <Loader2 className="h-6 w-6 animate-spin" />
              </span>
            )}
            <div className="min-w-0">
              <p className="truncate text-sm font-semibold">
                {done
                  ? "Conversion terminée"
                  : failed
                  ? job.status === "expired"
                    ? "Fichier expiré"
                    : "Échec de la conversion"
                  : queued
                  ? "En file d'attente…"
                  : job.message || "Conversion en cours…"}
              </p>
              <p className="truncate text-xs text-gray-500 dark:text-gray-400">
                {job.input_name} → .{job.target || job.output_name?.split(".").pop()}
              </p>
            </div>
          </div>
          <div className="flex shrink-0 items-center gap-2">
            {canPreview && (
              <button type="button" onClick={() => setPreview(true)} className="btn-ghost">
                <Eye className="h-4 w-4" /> Aperçu
              </button>
            )}
            {done && (
              <a
                href={jobDownloadUrl(jobId)}
                className="btn-primary shrink-0"
                download={job.output_name ?? undefined}
              >
                <Download className="h-4 w-4" />
                Télécharger
              </a>
            )}
          </div>
        </div>

        <div className="mt-5">
          <div className="flex items-center justify-between text-xs text-gray-400">
            <span>Progression</span>
            <span className="tabular-nums">{job.progress}%</span>
          </div>
          <div className="mt-1.5 h-2 w-full overflow-hidden rounded-full bg-gray-200/80 dark:bg-white/10">
            <div
              className={cn(
                "relative h-full rounded-full transition-all duration-300",
                failed ? "bg-rose-500" : done ? "bg-emerald-500" : "bg-brand-600"
              )}
              style={{ width: `${job.progress}%` }}
            >
              {!done && !failed && job.progress > 0 && (
                <span className="progress-shimmer absolute inset-0" />
              )}
            </div>
          </div>
        </div>

        {/* Inline mini side-by-side preview */}
        {srcUrl && outUrl && isImageExt(extOf(previewFile?.name)) && isImageExt(targetExt) && (
          <div className="mt-5 grid grid-cols-2 gap-3">
            <PreviewBox label="Avant" url={srcUrl} alt={job.input_name ?? "source"} />
            <PreviewBox label={done ? "Après" : "En cours…"} url={outUrl} alt={job.output_name ?? "output"} />
          </div>
        )}

        {failed && job.error && (
          <pre className="mt-4 overflow-auto rounded-lg bg-rose-50 p-3 text-xs text-rose-700 dark:bg-rose-500/10 dark:text-rose-300">
            {job.error}
          </pre>
        )}
      </div>

      {preview && (srcUrl || outUrl) && (
        <PreviewModal onClose={() => setPreview(false)} before={srcUrl} after={outUrl}
          beforeLabel={job.input_name ?? "Source"} afterLabel={job.output_name ?? "Résultat"} />
      )}
    </>
  );
}

function PreviewBox({ label, url, alt }: { label: string; url: string; alt: string }) {
  return (
    <div className="overflow-hidden rounded-xl border border-black/5 dark:border-white/10">
      <div className="border-b border-black/5 bg-gray-50 px-3 py-1.5 text-xs font-medium text-gray-500 dark:border-white/10 dark:bg-white/5 dark:text-gray-400">
        {label}
      </div>
      <div className="grid place-items-center bg-[repeating-conic-gradient(#eee_0_25%,transparent_0_50%)] bg-[length:16px_16px] p-2 dark:bg-[repeating-conic-gradient(#1a1f2e_0_25%,transparent_0_50%)]">
        {url ? (
          // eslint-disable-next-line @next/next/no-img-element -- blob: URL not optimizable
          <img src={url} alt={alt} className="max-h-44 w-full object-contain" />
        ) : (
          <Loader2 className="h-5 w-5 animate-spin text-gray-400" />
        )}
      </div>
    </div>
  );
}

function PreviewModal({
  before, after, beforeLabel, afterLabel, onClose,
}: {
  before: string | null; after: string | null;
  beforeLabel: string; afterLabel: string; onClose: () => void;
}) {
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);
  return (
    <div
      onClick={onClose}
      className="fixed inset-0 z-50 grid place-items-center bg-black/60 p-4 backdrop-blur-sm animate-fade-in-up"
    >
      <div
        onClick={(e) => e.stopPropagation()}
        className="card w-full max-w-4xl overflow-hidden p-4"
      >
        <div className="mb-3 flex items-center justify-between">
          <p className="font-semibold">Aperçu avant / après</p>
          <button onClick={onClose} className="btn-ghost h-8 w-8 rounded-full p-0" aria-label="Fermer">
            <XCircle className="h-4 w-4" />
          </button>
        </div>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          {before && <BigBox label={beforeLabel} url={before} />}
          {after && <BigBox label={afterLabel} url={after} />}
        </div>
      </div>
    </div>
  );
}

function BigBox({ label, url }: { label: string; url: string }) {
  return (
    <div className="overflow-hidden rounded-xl border border-black/5 dark:border-white/10">
      <div className="border-b border-black/5 px-3 py-2 text-xs text-gray-500 dark:border-white/10 dark:text-gray-400">
        {label}
      </div>
      <div className="grid max-h-[60vh] place-items-center bg-[repeating-conic-gradient(#eee_0_25%,transparent_0_50%)] bg-[length:16px_16px] p-3 dark:bg-[repeating-conic-gradient(#1a1f2e_0_25%,transparent_0_50%)]">
        {/* eslint-disable-next-line @next/next/no-img-element -- blob: URL not optimizable */}
        <img src={url} alt={label} className="max-h-[56vh] w-auto max-w-full object-contain" />
      </div>
    </div>
  );
}

function useObjectUrl(file?: File | null): string | null {
  const [url, setUrl] = useState<string | null>(null);
  useEffect(() => {
    if (!file || !(file instanceof File)) {
      setUrl(null);
      return;
    }
    const u = URL.createObjectURL(file);
    setUrl(u);
    return () => URL.revokeObjectURL(u);
  }, [file]);
  return url;
}

function useDownloadBlobUrl(jobId: string, when: boolean): string | null {
  const [url, setUrl] = useState<string | null>(null);
  const out = extOf(jobId);
  const didRef = useRef(false);
  useEffect(() => {
    if (!when || didRef.current) return;
    didRef.current = true;
    let alive = true;
    let localUrl: string | null = null;
    fetch(`${CONVERTER_URL}/jobs/${jobId}/download`)
      .then((r) => (r.ok ? r.blob() : Promise.reject(r.status)))
      .then((b) => {
        if (!alive) return;
        localUrl = URL.createObjectURL(b);
        setUrl(localUrl);
      })
      .catch(() => {
        if (alive) didRef.current = false;
      });
    return () => {
      alive = false;
      if (localUrl) URL.revokeObjectURL(localUrl);
    };
  }, [jobId, when]);
  void out;
  return url;
}
