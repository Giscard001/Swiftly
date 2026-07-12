"use client";

import { Suspense, useEffect, useState } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { ConversionProgress } from "@/components/ConversionProgress";
import { ArrowLeft } from "lucide-react";
import Link from "next/link";
import { listBatch, type Job } from "@/lib/converter-client";
import { getJobFile, getBatchFiles } from "@/lib/upload-cache";

function ConvertInner() {
  const params = useSearchParams();
  const router = useRouter();
  const jobId = params.get("job");
  const batchId = params.get("batch");

  const [batchJobs, setBatchJobs] = useState<Job[] | null>(null);

  useEffect(() => {
    if (!batchId) return;
    let alive = true;
    listBatch(batchId)
      .then((j) => alive && setBatchJobs(j))
      .catch(() => alive && setBatchJobs([]));
    return () => {
      alive = false;
    };
  }, [batchId]);

  const missing = !jobId && !batchId;
  if (missing) {
    return (
      <div className="mx-auto max-w-2xl px-4 py-20 text-center">
        <p className="text-gray-500">Aucune conversion en cours.</p>
        <Link href="/" className="btn-primary mt-6 inline-flex">
          <ArrowLeft className="h-4 w-4" /> Nouvelle conversion
        </Link>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-3xl px-4 py-12">
      <button onClick={() => router.push("/")} className="btn-ghost -ml-2 mb-6">
        <ArrowLeft className="h-4 w-4" /> Retour
      </button>

      <h1 className="text-2xl font-bold">
        {batchId ? "Conversion par lot" : "Conversion en cours"}
      </h1>
      <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
        Suivi en temps réel · fichier{batchId ? "s" : ""} supprimé{batchId ? "s" : ""} après 1h
      </p>

      <div className="mt-6 space-y-3">
        {jobId && <ConversionProgress jobId={jobId} previewFile={getJobFile(jobId)} />}
        {batchId && (
          <>
            {batchJobs === null ? (
              <div className="card p-5 text-sm text-gray-500">Chargement du lot…</div>
            ) : batchJobs.length === 0 ? (
              <div className="card p-5 text-sm text-gray-500">Lot introuvable ou expiré.</div>
            ) : (
              <>
                <BatchSummary jobs={batchJobs} />
                {(() => {
                  const cached = getBatchFiles(batchId);
                  return batchJobs.map((j, i) => (
                    <ConversionProgress
                      key={j.id}
                      jobId={j.id}
                      previewFile={cached?.[i]}
                    />
                  ));
                })()}
              </>
            )}
          </>
        )}
      </div>
    </div>
  );
}

function BatchSummary({ jobs }: { jobs: Job[] }) {
  const done = jobs.filter((j) => j.status === "completed").length;
  const failed = jobs.filter((j) => j.status === "failed" || j.status === "expired").length;
  const active = jobs.length - done - failed;
  return (
    <div className="card flex items-center justify-between p-4 text-sm">
      <span className="font-medium">
        {jobs.length} fichier{jobs.length > 1 ? "s" : ""}
      </span>
      <span className="flex gap-3 text-xs">
        <span className="text-emerald-600 dark:text-emerald-400">{done} terminé{done > 1 ? "s" : ""}</span>
        {active > 0 && <span className="text-brand-600 dark:text-brand-400">{active} en cours</span>}
        {failed > 0 && <span className="text-rose-600 dark:text-rose-400">{failed} échec{failed > 1 ? "s" : ""}</span>}
      </span>
    </div>
  );
}

export default function ConvertPage() {
  return (
    <Suspense fallback={<div className="px-4 py-20 text-center text-gray-500">Chargement…</div>}>
      <ConvertInner />
    </Suspense>
  );
}
