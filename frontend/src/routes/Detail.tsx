import { StatusBadge } from "@/components/ui/badge";
import { Card, CardBody, CardTitle } from "@/components/ui/card";
import { api } from "@/services/api";
import { confidenceColor } from "@/lib/utils";
import { useQuery } from "@tanstack/react-query";
import { useParams } from "@tanstack/react-router";

export function Detail() {
  const { id } = useParams({ from: "/results/$id" });
  const { data } = useQuery({ queryKey: ["result", id], queryFn: () => api.resultDetail(id) });

  if (!data) return <p className="text-text-secondary">Loading…</p>;
  const { document: doc, result } = data;
  const isPdf = doc.filename.toLowerCase().endsWith(".pdf");

  return (
    <div>
      <div className="mb-6 flex items-center gap-3">
        <h1 className="font-display text-[32px] font-bold text-text-primary">{doc.filename}</h1>
        <StatusBadge status={doc.status} />
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Document preview */}
        <Card>
          <CardBody>
            <CardTitle>Document Preview</CardTitle>
            <div className="mt-4 overflow-hidden rounded-lg border border-border">
              {isPdf ? (
                <iframe title="preview" src={api.fileUrl(id)} className="h-[480px] w-full" />
              ) : (
                <img src={api.fileUrl(id)} alt={doc.filename} className="w-full" />
              )}
            </div>
          </CardBody>
        </Card>

        {/* Extracted data + confidence */}
        <div className="space-y-6">
          <Card>
            <CardBody>
              <CardTitle>Extracted Data</CardTitle>
              <dl className="mt-4 space-y-2">
                {Object.entries(result.fields)
                  .filter(([, v]) => v != null)
                  .map(([k, v]) => (
                    <div key={k} className="flex justify-between border-b border-border py-2">
                      <dt className="font-body text-sm text-text-secondary">{k}</dt>
                      <dd className="font-body text-sm font-semibold text-text-primary">{v}</dd>
                    </div>
                  ))}
              </dl>
            </CardBody>
          </Card>

          <Card>
            <CardBody>
              <CardTitle>Confidence Scores</CardTitle>
              <div className="mt-4 space-y-2">
                {Object.entries(result.field_confidence)
                  .filter(([, c]) => c > 0)
                  .map(([k, c]) => (
                    <div key={k} className="flex justify-between">
                      <span className="font-body text-sm text-text-secondary">{k}</span>
                      <span className={`font-mono text-sm font-semibold ${confidenceColor(c)}`}>
                        {Math.round(c * 100)}%
                      </span>
                    </div>
                  ))}
              </div>
            </CardBody>
          </Card>

          <Card>
            <CardBody>
              <CardTitle>JSON</CardTitle>
              <pre className="mt-4 overflow-x-auto rounded-lg bg-surface p-4 font-mono text-xs text-text-primary">
                {JSON.stringify(result, null, 2)}
              </pre>
            </CardBody>
          </Card>
        </div>
      </div>
    </div>
  );
}
