import { getCapabilities } from "@/lib/converter-client";

export const dynamic = "force-dynamic";

export default async function ApiDocsPage() {
  let caps;
  try {
    caps = await getCapabilities();
  } catch {
    caps = null;
  }

  return (
    <div className="mx-auto max-w-3xl px-4 py-12">
      <h1 className="text-3xl font-bold">Documentation API</h1>
      <p className="mt-2 text-gray-500 dark:text-gray-400">
        API REST du microservice de conversion. Base URL :{" "}
        <code className="font-mono text-brand-600">http://127.0.0.1:8000</code> (via le proxy BFF{" "}
        <code className="font-mono">/api/*</code> côté Next.js).
      </p>

      <Section title="GET /capabilities">
        <p>Liste les conversions disponibles selon les binaires/libs détectés.</p>
        <Code>{`{
  "categories": ["archive","data","document","image"],
  "by_source": { "png": [{"category":"image","target":"jpg",...}, ...] },
  "binaries": { "libreoffice": null, "ffmpeg": null, "tesseract": null },
  "libs": { "PIL": true, "py7zr": false, ... },
  "limit": 2147483648,
  "retention_seconds": 3600
}`}</Code>
      </Section>

      <Section title="POST /convert">
        <p>multipart/form-data : <code>file</code>, <code>target</code>, <code>category?</code>,{" "}
        <code>options?</code> (JSON).</p>
        <Code>{`curl -F file=@photo.png -F target=jpg \\
  http://127.0.0.1:8000/convert
# => {"job_id":"...","status":"queued","expires_at":...}`}</Code>
      </Section>

      <Section title="POST /operations/{op}">
        <p>op ∈ <code>merge</code> · <code>split</code> · <code>compress</code>. multipart :
        <code> files</code> (multi), <code>options?</code>.</p>
        <Code>{`curl -F files=@a.pdf -F files=@b.pdf \\
  http://127.0.0.1:8000/operations/merge`}</Code>
      </Section>

      <Section title="GET /jobs/{id}">
        <p>Statut + progression d’une conversion.</p>
        <Code>{`{ "status":"completed","progress":100,"output_name":"output.jpg",... }`}</Code>
      </Section>

      <Section title="GET /jobs/{id}/download">
        <p>Retourne le fichier converti (binaire).         Disponible uniquement si status ={" "}
        <code>completed</code> et avant expiration (1h).</p>
      </Section>

      <Section title="GET /health">
        <p>Healthcheck du service.</p>
      </Section>

      {caps && (
        <div className="card mt-8 p-5">
          <p className="font-medium">État actuel détecté</p>
          <p className="mt-2 text-sm">Catégories actives : {caps.categories.join(", ")}</p>
          <p className="text-sm">
            Binaires :{" "}
            {Object.entries(caps.binaries)
              .map(([k, v]) => `${k}=${v ? "oui" : "non"}`)
              .join(" · ")}
          </p>
          <p className="text-sm text-gray-500 dark:text-gray-400">
            Astuce : installez LibreOffice / FFmpeg / Tesseract pour activer Office / Vidéo / OCR.
          </p>
        </div>
      )}
    </div>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="card mt-6 p-5">
      <p className="font-mono text-sm font-semibold text-brand-600">{title}</p>
      <div className="mt-2 space-y-2 text-sm text-gray-700 dark:text-gray-300">{children}</div>
    </div>
  );
}

function Code({ children }: { children: React.ReactNode }) {
  return (
    <pre className="mt-2 overflow-auto rounded-lg bg-gray-900 p-3 text-xs text-gray-100">
      {children}
    </pre>
  );
}
