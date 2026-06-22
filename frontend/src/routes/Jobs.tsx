import { StatusBadge } from "@/components/ui/badge";
import { Table, Td, Th } from "@/components/ui/table";
import { api } from "@/services/api";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Trash2, Square } from "lucide-react";

export function Jobs() {
  const qc = useQueryClient();
  // PRD §14: 3-second polling.
  const { data } = useQuery({ queryKey: ["jobs"], queryFn: api.jobs, refetchInterval: 3000 });

  const invalidate = () => {
    qc.invalidateQueries({ queryKey: ["jobs"] });
    qc.invalidateQueries({ queryKey: ["results"] });
    qc.invalidateQueries({ queryKey: ["metrics"] });
  };
  const cancel = useMutation({ mutationFn: api.cancelJob, onSuccess: invalidate });
  const remove = useMutation({ mutationFn: api.deleteJob, onSuccess: invalidate });

  const isActive = (s: string) => s === "queued" || s === "processing";

  return (
    <div>
      <h1 className="mb-6 font-display text-[32px] font-bold text-text-primary">Job Monitoring</h1>
      <Table>
        <thead>
          <tr>
            <Th>Job</Th>
            <Th>Source</Th>
            <Th>LLM</Th>
            <Th>Progress</Th>
            <Th>Status</Th>
            <Th>Actions</Th>
          </tr>
        </thead>
        <tbody>
          {data?.map((j) => (
            <tr key={j.id}>
              <Td className="font-mono text-xs">{j.id.slice(0, 8)}</Td>
              <Td>{j.source_type}</Td>
              <Td className="text-text-secondary">
                {j.llm_provider}/{j.llm_model}
              </Td>
              <Td>
                {j.successful + j.failed}/{j.total}
              </Td>
              <Td>
                <StatusBadge status={j.status} />
              </Td>
              <Td>
                <div className="flex gap-2">
                  {isActive(j.status) && (
                    <button
                      title="Stop queue"
                      onClick={() => cancel.mutate(j.id)}
                      disabled={cancel.isPending}
                      className="flex items-center gap-1 rounded border border-border px-2 py-1 text-xs font-semibold text-warning hover:bg-warning/10"
                    >
                      <Square size={14} /> Stop
                    </button>
                  )}
                  <button
                    title="Remove job"
                    onClick={() => {
                      if (confirm("Remove this job and all its results?")) remove.mutate(j.id);
                    }}
                    disabled={remove.isPending}
                    className="flex items-center gap-1 rounded border border-border px-2 py-1 text-xs font-semibold text-error hover:bg-error/10"
                  >
                    <Trash2 size={14} /> Remove
                  </button>
                </div>
              </Td>
            </tr>
          ))}
          {!data?.length && (
            <tr>
              <Td colSpan={6} className="text-center text-text-secondary">
                No jobs yet.
              </Td>
            </tr>
          )}
        </tbody>
      </Table>
    </div>
  );
}
