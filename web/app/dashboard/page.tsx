"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Download, History, Loader2 } from "lucide-react";
import { getJob, listJobs, jobDownloadUrl, type Job } from "@/lib/converter-client";
import { categoryIcon, categoryLabel } from "@/lib/formats";
import { formatBytes, timeAgo } from "@/lib/utils";

export default function DashboardPage() {
  const [jobs, setJobs] = useState<Job[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    listJobs(50)
      .then(setJobs)
      .catch(() => {
        setError("Service de conversion indisponible. Lancez l'API (npm run dev:api).");
        setJobs([]);
      });
  }, []);

  return (
    <div className="mx-auto max-w-5xl px-4 py-10">
      <div className="flex items-center gap-3">
        <History className="h-6 w-6 text-brand-600" />
        <h1 className="text-2xl font-bold">Historique des conversions</h1>
      </div>
      <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
        Aucune inscription requise — affichage des 50 dernières conversions. Les fichiers sont
        supprimés automatiquement après 1h.
      </p>

      {jobs === null ? (
        <div className="card mt-6 flex items-center gap-3 p-6">
          <Loader2 className="h-5 w-5 animate-spin text-brand-600" />
          <span className="text-sm">Chargement…</span>
        </div>
      ) : error ? (
        <div className="card mt-6 p-6 text-sm text-amber-600 dark:text-amber-400">{error}</div>
      ) : jobs.length === 0 ? (
        <div className="card mt-6 p-10 text-center">
          <p className="text-gray-500">Aucune conversion pour le moment.</p>
          <Link href="/" className="btn-primary mt-5 inline-flex">
            Lancer une conversion
          </Link>
        </div>
      ) : (
        <div className="card mt-6 overflow-hidden">
          <table className="w-full text-sm">
            <thead className="border-b border-gray-200 text-left text-xs uppercase text-gray-500 dark:border-white/10 dark:text-gray-400">
              <tr>
                <th className="px-4 py-3 font-medium">Fichier</th>
                <th className="px-4 py-3 font-medium">Type</th>
                <th className="px-4 py-3 font-medium">Statut</th>
                <th className="px-4 py-3 font-medium">Taille</th>
                <th className="px-4 py-3 font-medium">Date</th>
                <th className="px-4 py-3 font-medium text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100 dark:divide-white/5">
              {jobs.map((j) => (
                <tr key={j.id}>
                  <td className="px-4 py-3">
                    <div className="font-medium">{j.input_name ?? "—"}</div>
                    <div className="text-xs text-gray-500">
                      {j.kind === "operation" ? `Opération: ${j.operation}` : `→ .${j.target}`}
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    {j.category && (
                      <span className="badge bg-gray-100 text-gray-700 dark:bg-white/10 dark:text-gray-300">
                        {categoryIcon(j.category)} {categoryLabel(j.category)}
                      </span>
                    )}
                  </td>
                  <td className="px-4 py-3">
                    <StatusBadge status={j.status} progress={j.progress} />
                  </td>
                  <td className="px-4 py-3 text-gray-500">{formatBytes(j.size_bytes)}</td>
                  <td className="px-4 py-3 text-gray-500">{timeAgo(j.created_at)}</td>
                  <td className="px-4 py-3 text-right">
                    {j.status === "completed" ? (
                      <a
                        href={jobDownloadUrl(j.id)}
                        onClick={async (e) => {
                          const fresh = await getJob(j.id).catch(() => null);
                          if (!fresh || fresh.status !== "completed") {
                            e.preventDefault();
                            alert("Fichier expiré ou supprimé.");
                          }
                        }}
                        download={j.output_name ?? undefined}
                        className="btn-ghost inline-flex h-8 px-2"
                      >
                        <Download className="h-4 w-4" /> Télécharger
                      </a>
                    ) : (
                      <span className="text-xs text-gray-400">—</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

function StatusBadge({ status, progress }: { status: string; progress: number }) {
  const map: Record<string, string> = {
    queued: "bg-gray-100 text-gray-600 ring-black/5 dark:bg-white/10 dark:text-gray-300 dark:ring-white/10",
    processing: "bg-brand-50 text-brand-700 ring-brand-200/60 dark:bg-brand-500/10 dark:text-brand-300 dark:ring-brand-500/20",
    completed: "bg-emerald-50 text-emerald-700 ring-emerald-200/60 dark:bg-emerald-500/10 dark:text-emerald-300 dark:ring-emerald-500/20",
    failed: "bg-rose-50 text-rose-700 ring-rose-200/60 dark:bg-rose-500/10 dark:text-rose-300 dark:ring-rose-500/20",
    expired: "bg-gray-100 text-gray-500 ring-black/5 dark:bg-white/5 dark:text-gray-400 dark:ring-white/10",
  };
  const label =
    status === "processing" ? `en cours ${progress}%` : status;
  return <span className={`badge ${map[status] ?? ""}`}>{label}</span>;
}
