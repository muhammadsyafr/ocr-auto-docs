import { StatusBadge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Td, Th } from "@/components/ui/table";
import { api } from "@/services/api";
import { useQuery } from "@tanstack/react-query";
import { Link } from "@tanstack/react-router";
import { ChevronDown, ChevronRight, FileArchive, Folder } from "lucide-react";
import { useState } from "react";
import type { DocumentOut, Job } from "@/types";

function basename(p: string): string {
  return p.split("/").filter(Boolean).pop() ?? p;
}

export function Results() {
  const { data: docs } = useQuery({ queryKey: ["results"], queryFn: api.results, refetchInterval: 5000 });
  const { data: jobs } = useQuery({ queryKey: ["jobs"], queryFn: api.jobs, refetchInterval: 5000 });
  const [collapsed, setCollapsed] = useState<Set<string>>(new Set());

  const onExport = async () => {
    const out = await api.exportJson();
    const blob = new Blob([JSON.stringify(out, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "results.json";
    a.click();
    URL.revokeObjectURL(url);
  };

  // Group documents by their job (the upload / zip).
  const jobMap = new Map<string, Job>((jobs ?? []).map((j) => [j.id, j]));
  const groups = new Map<string, DocumentOut[]>();
  for (const d of docs ?? []) {
    const key = d.job_id ?? "ungrouped";
    if (!groups.has(key)) groups.set(key, []);
    groups.get(key)!.push(d);
  }
  // Order groups by job created_at desc (jobs already sorted desc).
  const orderedKeys = [
    ...(jobs ?? []).map((j) => j.id).filter((id) => groups.has(id)),
    ...(groups.has("ungrouped") ? ["ungrouped"] : []),
  ];

  const toggle = (k: string) =>
    setCollapsed((prev) => {
      const next = new Set(prev);
      next.has(k) ? next.delete(k) : next.add(k);
      return next;
    });

  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <h1 className="font-display text-[32px] font-bold text-text-primary">Results</h1>
        <Button variant="secondary" onClick={onExport}>
          Export JSON
        </Button>
      </div>

      {orderedKeys.length === 0 && (
        <Card className="p-6 text-center text-text-secondary">No results yet.</Card>
      )}

      <div className="space-y-4">
        {orderedKeys.map((key) => {
          const job = jobMap.get(key);
          const items = groups.get(key)!;
          const isOpen = !collapsed.has(key);
          const done = items.filter((d) => d.status === "completed").length;
          const failed = items.filter((d) => d.status === "failed").length;
          const label = job ? basename(job.source_path) : "Ungrouped";
          const Icon = job?.source_type === "zip" ? FileArchive : Folder;

          return (
            <Card key={key} className="overflow-hidden hover:translate-y-0 hover:shadow-lvl1">
              {/* Group header */}
              <button
                onClick={() => toggle(key)}
                className="flex w-full items-center gap-3 border-b border-border bg-surface px-4 py-3 text-left"
              >
                {isOpen ? <ChevronDown size={18} /> : <ChevronRight size={18} />}
                <Icon size={18} className="text-primary" />
                <span className="font-display text-base font-bold text-text-primary">{label}</span>
                {job && (
                  <span className="rounded-full border border-border bg-white px-2 py-0.5 text-xs font-semibold uppercase text-neutral">
                    {job.source_type}
                  </span>
                )}
                <span className="ml-auto flex items-center gap-3 font-body text-sm text-text-secondary">
                  <span>{items.length} docs</span>
                  <span className="text-success">{done} ok</span>
                  {failed > 0 && <span className="text-error">{failed} failed</span>}
                  {job && <StatusBadge status={job.status} />}
                </span>
              </button>

              {/* Group rows */}
              {isOpen && (
                <table className="w-full border-collapse text-sm">
                  <thead>
                    <tr>
                      <Th>File</Th>
                      <Th>Type</Th>
                      <Th>Status</Th>
                      <Th>Confidence</Th>
                      <Th></Th>
                    </tr>
                  </thead>
                  <tbody>
                    {items.map((d) => (
                      <tr key={d.id}>
                        <Td>{d.filename}</Td>
                        <Td>{d.document_type ?? "—"}</Td>
                        <Td>
                          <StatusBadge status={d.status} />
                        </Td>
                        <Td>{d.confidence != null ? `${Math.round(d.confidence * 100)}%` : "—"}</Td>
                        <Td>
                          <Link to="/results/$id" params={{ id: d.id }} className="font-semibold text-primary">
                            View
                          </Link>
                        </Td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </Card>
          );
        })}
      </div>
    </div>
  );
}
