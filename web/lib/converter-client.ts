export const CONVERTER_URL =
  process.env.NEXT_PUBLIC_CONVERTER_URL || "http://127.0.0.1:8000";

export type CapabilityTarget = {
  category: string;
  target: string;
  engine: string;
  label: string;
};

export type Capabilities = {
  categories: string[];
  by_source: Record<string, CapabilityTarget[]>;
  routes: { category: string; source: string; target: string; engine: string; label: string }[];
  binaries: Record<string, string | null>;
  libs: Record<string, boolean>;
  limit: number;
  retention_seconds: number;
};

export type JobStatus = "queued" | "processing" | "completed" | "failed" | "expired";

export type Job = {
  id: string;
  kind: "convert" | "operation";
  operation: string | null;
  batch_id: string | null;
  category: string | null;
  source: string | null;
  target: string | null;
  status: JobStatus;
  progress: number;
  message: string | null;
  input_name: string | null;
  output_name: string | null;
  error: string | null;
  user_email: string | null;
  plan: string;
  size_bytes: number;
  created_at: number;
  updated_at: number;
  expires_at: number;
};

export type BatchJobItem = { job_id: string; input_name: string; target: string };
export type BatchResult = {
  batch_id: string;
  count: number;
  jobs: BatchJobItem[];
  expires_at: number;
};

async function req(path: string, init?: RequestInit): Promise<Response> {
  return fetch(`${CONVERTER_URL}${path}`, init);
}

export async function getCapabilities(): Promise<Capabilities> {
  const r = await req("/capabilities");
  if (!r.ok) throw new Error("Capacites indisponibles");
  return (await r.json()) as Capabilities;
}

export async function createJob(file: File | Blob, target: string, opts?: {
  category?: string;
  options?: Record<string, unknown>;
}): Promise<{ job_id: string; status: string; expires_at: number }> {
  const fd = new FormData();
  const filename = (file as File).name || "file";
  fd.append("file", file, filename);
  fd.append("target", target);
  if (opts?.category) fd.append("category", opts.category);
  if (opts?.options) fd.append("options", JSON.stringify(opts.options));
  const r = await req("/convert", { method: "POST", body: fd });
  if (!r.ok) {
    const t = await r.text().catch(() => "");
    throw new Error(t || `Erreur ${r.status}`);
  }
  return (await r.json()) as { job_id: string; status: string; expires_at: number };
}

export async function createBatch(
  files: File[],
  target: string,
  opts?: { category?: string; options?: Record<string, unknown> }
): Promise<BatchResult> {
  const fd = new FormData();
  for (const f of files) fd.append("files", f, f.name);
  fd.append("target", target);
  if (opts?.category) fd.append("category", opts.category);
  if (opts?.options) fd.append("options", JSON.stringify(opts.options));
  const r = await req("/convert/batch", { method: "POST", body: fd });
  if (!r.ok) {
    const t = await r.text().catch(() => "");
    throw new Error(t || `Erreur ${r.status}`);
  }
  return (await r.json()) as BatchResult;
}

export async function listBatch(batchId: string): Promise<Job[]> {
  const r = await req(`/jobs?batch_id=${encodeURIComponent(batchId)}&limit=200`);
  if (!r.ok) throw new Error("Batch introuvable");
  const data = (await r.json()) as { jobs: Job[] };
  return data.jobs;
}

export async function createOperation(
  op: "merge" | "split" | "compress",
  files: File[],
  opts?: { options?: Record<string, unknown> }
): Promise<{ job_id: string; status: string; expires_at: number }> {
  const fd = new FormData();
  for (const f of files) fd.append("files", f, f.name);
  if (opts?.options) fd.append("options", JSON.stringify(opts.options));
  const r = await req(`/operations/${op}`, { method: "POST", body: fd });
  if (!r.ok) {
    const t = await r.text().catch(() => "");
    throw new Error(t || `Erreur ${r.status}`);
  }
  return (await r.json()) as { job_id: string; status: string; expires_at: number };
}

export async function getJob(jobId: string): Promise<Job> {
  const r = await req(`/jobs/${jobId}`);
  if (!r.ok) throw new Error("Job introuvable");
  return (await r.json()) as Job;
}

export async function listJobs(limit = 50): Promise<Job[]> {
  const r = await req(`/jobs?limit=${limit}`);
  if (!r.ok) throw new Error("Historique indisponible");
  const data = (await r.json()) as { jobs: Job[] };
  return data.jobs;
}

export function jobDownloadUrl(jobId: string): string {
  return `${CONVERTER_URL}/jobs/${jobId}/download`;
}
