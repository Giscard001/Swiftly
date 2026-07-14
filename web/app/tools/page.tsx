"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { FilePlus2, Scissors, Minimize2, ArrowRight } from "lucide-react";
import { Dropzone } from "@/components/Dropzone";
import { createOperation } from "@/lib/converter-client";
import { detectExt } from "@/lib/utils";

type Tool = "merge" | "split" | "compress";

const TOOLS: { id: Tool; title: string; desc: string; icon: typeof FilePlus2; accept: string }[] = [
  { id: "merge", title: "Fusionner des PDF", desc: "Assemblez plusieurs PDF en un seul.", icon: FilePlus2, accept: ".pdf" },
  { id: "split", title: "Découper un PDF", desc: "Un PDF → une archive ZIP avec une page par fichier.", icon: Scissors, accept: ".pdf" },
  { id: "compress", title: "Compresser", desc: "Réduisez la taille d'un PDF ou d'une image.", icon: Minimize2, accept: ".pdf,.png,.jpg,.jpeg,.webp" },
];

export default function ToolsPage() {
  const router = useRouter();
  const [active, setActive] = useState<Tool | null>(null);
  const [files, setFiles] = useState<File[]>([]);
  const [err, setErr] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  function pick(tool: Tool) {
    setActive(tool);
    setFiles([]);
    setErr(null);
  }

  function validate(tool: Tool, fs: File[]): string | null {
    for (const f of fs) {
      const ext = detectExt(f.name);
      if (tool === "merge" && ext !== "pdf") return "La fusion n'accepte que des PDF.";
      if (tool === "split" && ext !== "pdf") return "Le découpage n'accepte qu'un PDF.";
      if (tool === "compress" && !["pdf", "png", "jpg", "jpeg", "webp"].includes(ext))
        return "Compression supporte PDF, PNG, JPG, WEBP.";
    }
    if (tool === "split" && fs.length !== 1) return "Le découpage accepte exactement un fichier.";
    if (tool === "compress" && fs.length !== 1) return "La compression accepte exactement un fichier.";
    return null;
  }

  async function run() {
    if (!active || !files.length) return;
    const v = validate(active, files);
    if (v) {
      setErr(v);
      return;
    }
    setErr(null);
    setLoading(true);
    try {
      const r = await createOperation(active, files);
      router.push(`/convert?job=${r.job_id}`);
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Erreur lors de l'envoi");
      setLoading(false);
    }
  }

  const tool = TOOLS.find((t) => t.id === active);

  return (
    <div className="mx-auto max-w-4xl px-4 py-12 sm:px-6">
      <h1 className="text-3xl font-bold tracking-tight">Outils PDF</h1>
      <p className="mt-1.5 text-gray-500 dark:text-gray-400">
        Fusion, découpage et compression — sans inscription, fichiers supprimés après 1h.
      </p>

      {!active && (
        <div className="mt-8 grid grid-cols-1 gap-4 sm:grid-cols-3">
          {TOOLS.map((t) => (
            <button
              key={t.id}
              onClick={() => pick(t.id)}
              className="card card-hover p-5 text-left"
            >
              <span className="grid h-11 w-11 place-items-center rounded-xl bg-brand-50 text-brand-600 dark:bg-brand-500/10 dark:text-brand-400">
                <t.icon className="h-5 w-5" />
              </span>
              <p className="mt-4 font-semibold">{t.title}</p>
              <p className="mt-1 text-sm leading-relaxed text-gray-500 dark:text-gray-400">{t.desc}</p>
            </button>
          ))}
        </div>
      )}

      {tool && (
        <div className="mt-8">
          <button onClick={() => setActive(null)} className="btn-ghost -ml-2 mb-4">
            <ArrowRight className="h-4 w-4 rotate-180" /> Retour aux outils
          </button>
          <div className="card p-6">
            <div className="mb-5 flex items-center gap-3">
              <span className="grid h-10 w-10 place-items-center rounded-xl bg-brand-50 text-brand-600 dark:bg-brand-500/10 dark:text-brand-400">
                <tool.icon className="h-5 w-5" />
              </span>
              <div>
                <p className="font-semibold">{tool.title}</p>
                <p className="text-sm text-gray-500 dark:text-gray-400">{tool.desc}</p>
              </div>
            </div>

            <Dropzone
              files={files}
              onFilesChange={setFiles}
              multiple={tool.id === "merge"}
              accept={tool.accept}
            />

            <div className="mt-6 flex items-center justify-between">
              <p className="text-xs text-gray-400">
                {tool.id === "merge"
                  ? "Ajoutez 2 PDF ou plus"
                  : tool.id === "split"
                  ? "1 PDF → une page par fichier (ZIP)"
                  : "1 PDF ou image"}
              </p>
              <button
                disabled={!files.length || loading}
                onClick={run}
                className="btn-primary px-5 py-2.5"
              >
                {tool.id === "merge" ? "Fusionner" : tool.id === "split" ? "Découper" : "Compresser"}
                <ArrowRight className="h-4 w-4" />
              </button>
            </div>

            {err && (
              <pre className="mt-4 overflow-auto rounded-lg bg-rose-50 p-3 text-xs text-rose-700 dark:bg-rose-500/10 dark:text-rose-300">
                {err}
              </pre>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
