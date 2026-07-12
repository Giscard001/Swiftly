"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { ArrowRight, ShieldCheck, Zap, Trash2, Sparkles } from "lucide-react";
import { Dropzone } from "@/components/Dropzone";
import { FormatSelector } from "@/components/FormatSelector";
import { detectExt, formatBytes } from "@/lib/utils";
import { getCapabilities, createJob, createBatch, type Capabilities } from "@/lib/converter-client";
import { cacheJobFile, cacheBatchFiles } from "@/lib/upload-cache";

export default function HomePage() {
  const router = useRouter();
  const [caps, setCaps] = useState<Capabilities | null>(null);
  const [files, setFiles] = useState<File[]>([]);
  const [sourceExt, setSourceExt] = useState<string>("");
  const [target, setTarget] = useState<string | null>(null);
  const [category, setCategory] = useState<string | null>(null);
  const [useOcr, setUseOcr] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    getCapabilities().then(setCaps).catch(() => setCaps(null));
  }, []);

  const primaryFile = files[0];

  useEffect(() => {
    if (primaryFile) {
      setSourceExt(detectExt(primaryFile.name));
      setTarget(null);
      setCategory(null);
    } else {
      setSourceExt("");
    }
  }, [primaryFile]);

  useEffect(() => {
    setUseOcr(false);
  }, [target]);

  const ready = files.length > 0 && target && category && !loading;

  const ocrAvailable = !!caps?.binaries?.tesseract && !!caps?.binaries?.pdftoppm;
  const showOcr = sourceExt === "pdf" && target === "txt";
  const options = useOcr ? { ocr: true } : undefined;

  async function launch() {
    if (!target || !files.length) return;
    setLoading(true);
    setError(null);
    try {
      if (files.length > 1) {
        const r = await createBatch(files, target, {
          category: category ?? undefined,
          options,
        });
        cacheBatchFiles(r.batch_id, files, r.jobs);
        router.push(`/convert?batch=${r.batch_id}`);
      } else {
        const r = await createJob(files[0], target, {
          category: category ?? undefined,
          options,
        });
        cacheJobFile(r.job_id, files[0]);
        router.push(`/convert?job=${r.job_id}`);
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erreur lors de l'envoi");
      setLoading(false);
    }
  }

  const limit = useMemo(() => caps?.limit ?? 0, [caps]);

  return (
    <div className="relative">
      {/* halo decor */}
      <div className="pointer-events-none absolute inset-x-0 top-0 -z-10 h-[420px] overflow-hidden">
        <div className="absolute left-1/2 top-[-180px] h-[420px] w-[820px] -translate-x-1/2 rounded-full bg-gradient-to-tr from-brand-500/25 via-violet-400/15 to-transparent blur-3xl" />
      </div>

      <div className="mx-auto max-w-6xl px-4 pb-20 pt-14 sm:px-6">
        <section className="mx-auto max-w-3xl text-center animate-fade-in-up">
          <span className="badge bg-brand-50 text-brand-700 ring-brand-200/60 dark:bg-brand-500/10 dark:text-brand-300 dark:ring-brand-500/20">
            <Sparkles className="mr-1 h-3.5 w-3.5" />
            Sans inscription · Self-hosted
          </span>
          <h1 className="mt-5 text-4xl font-bold tracking-tight sm:text-5xl">
            Convertissez vos fichiers,
            <span className="block bg-gradient-to-r from-brand-600 to-violet-600 bg-clip-text text-transparent">
              simplement et en privé.
            </span>
          </h1>
          <p className="mt-5 text-lg leading-relaxed text-gray-600 dark:text-gray-300">
            Documents, images, audio, vidéo, archives et données.
            Sélection intelligente des formats selon votre fichier.
          </p>
        </section>

        <section className="mx-auto mt-12 max-w-3xl" style={{ animationDelay: "60ms" }}>
          <Dropzone onFiles={(arr) => setFiles((prev) => [...prev, ...arr])} />

          {primaryFile && (
            <div className="card mt-6 p-6 animate-fade-in-up">
              <div className="mb-5 flex flex-wrap items-center gap-3">
                <span className="text-sm text-gray-500 dark:text-gray-400">
                  Fichier détecté :
                </span>
                <span className="badge bg-brand-50 font-semibold text-brand-700 ring-brand-200/60 dark:bg-brand-500/10 dark:text-brand-300 dark:ring-brand-500/20">
                  .{sourceExt || "?"}
                </span>
                {files.length > 1 && (
                  <span className="text-xs text-gray-400">
                    {files.length} fichiers — devez tous être du même type (.{sourceExt || "?"}) pour le batch
                  </span>
                )}
              </div>

              <FormatSelector
                sourceExt={sourceExt}
                capabilities={caps}
                selected={target}
                onSelect={(t, c) => {
                  setTarget(t);
                  setCategory(c);
                }}
              />

              <div className="mt-7 flex flex-wrap items-center justify-between gap-4">
                <p className="text-xs text-gray-400 dark:text-gray-500">
                  {limit > 0 && <>Taille max : {formatBytes(limit)} / fichier</>}
                </p>
                <button
                  type="button"
                  disabled={!ready}
                  onClick={launch}
                  className="btn-primary px-6 py-3 text-[15px]"
                >
                  {files.length > 1 ? `Convertir tout (${files.length})` : "Convertir"}
                  <ArrowRight className="h-4 w-4" />
                </button>
              </div>

              {error && (
                <pre className="mt-4 overflow-auto rounded-lg bg-rose-50 p-3 text-xs text-rose-700 dark:bg-rose-500/10 dark:text-rose-300">
                  {error}
                </pre>
              )}
            </div>
          )}

          <div className="mt-12 grid grid-cols-1 gap-4 sm:grid-cols-3">
            {[
              { icon: Zap, t: "Rapide", d: "Conversions en arrière-plan, progression en temps réel" },
              { icon: ShieldCheck, t: "Privé", d: "Transfert chiffré, stockage hors-ligne web" },
              { icon: Trash2, t: "Éphémère", d: "Suppression automatique des fichiers après 1h" },
            ].map((f) => (
              <div key={f.t} className="card card-hover p-5">
                <span className="grid h-11 w-11 place-items-center rounded-xl bg-brand-50 text-brand-600 dark:bg-brand-500/10 dark:text-brand-400">
                  <f.icon className="h-5 w-5" />
                </span>
                <p className="mt-4 font-semibold">{f.t}</p>
                <p className="mt-1 text-sm leading-relaxed text-gray-500 dark:text-gray-400">{f.d}</p>
              </div>
            ))}
          </div>
        </section>
      </div>
    </div>
  );
}
