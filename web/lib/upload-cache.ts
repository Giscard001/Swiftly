type Entry = File;

const byJob = new Map<string, Entry>();
const byBatch = new Map<string, Entry[]>();

export function cacheJobFile(jobId: string, file: File) {
  byJob.set(jobId, file);
  if (byJob.size > 200) {
    const first = byJob.keys().next().value;
    if (first) byJob.delete(first);
  }
}

export function cacheBatchFiles(batchId: string, files: File[], jobs: { job_id: string }[]) {
  byBatch.set(batchId, files);
  files.forEach((f, i) => {
    const jid = jobs[i]?.job_id;
    if (jid) cacheJobFile(jid, f);
  });
}

export function getJobFile(jobId: string): File | undefined {
  return byJob.get(jobId);
}

export function getBatchFiles(batchId: string): File[] | undefined {
  return byBatch.get(batchId);
}
