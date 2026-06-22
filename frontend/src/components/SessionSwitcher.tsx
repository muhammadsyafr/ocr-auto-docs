import { api } from "@/services/api";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Check, ChevronsUpDown, Layers, Plus, Trash2 } from "lucide-react";
import { useEffect, useRef, useState } from "react";

// Switching/creating/deleting a session changes what every page shows.
const SCOPED_KEYS = ["jobs", "results", "metrics", "people", "docInfo"];

export function SessionSwitcher() {
  const qc = useQueryClient();
  const { data: sessions } = useQuery({ queryKey: ["sessions"], queryFn: api.sessions, refetchInterval: 5000 });
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const onClick = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener("mousedown", onClick);
    return () => document.removeEventListener("mousedown", onClick);
  }, []);

  const invalidateAll = () => {
    qc.invalidateQueries({ queryKey: ["sessions"] });
    SCOPED_KEYS.forEach((k) => qc.invalidateQueries({ queryKey: [k] }));
  };

  const activate = useMutation({ mutationFn: api.activateSession, onSuccess: invalidateAll });
  const create = useMutation({ mutationFn: api.createSession, onSuccess: invalidateAll });
  const remove = useMutation({ mutationFn: api.deleteSession, onSuccess: invalidateAll });

  const active = sessions?.find((s) => s.active);

  const onNew = () => {
    const name = prompt("New session name?");
    if (name && name.trim()) {
      create.mutate(name.trim());
      setOpen(false);
    }
  };

  return (
    <div className="relative" ref={ref}>
      <button
        onClick={() => setOpen((o) => !o)}
        className="flex items-center gap-2 rounded-full border border-border bg-white px-3 py-2 font-body text-sm font-semibold text-text-primary hover:bg-surface"
      >
        <Layers size={16} className="text-primary" />
        <span className="max-w-[140px] truncate">{active?.name ?? "Session"}</span>
        <ChevronsUpDown size={14} className="text-neutral" />
      </button>

      {open && (
        <div className="absolute right-0 z-20 mt-2 w-72 rounded-xl border border-border bg-white p-2 shadow-lvl2">
          <p className="px-2 py-1 font-body text-xs font-semibold uppercase tracking-wide text-neutral">
            Sessions
          </p>
          <div className="max-h-72 overflow-y-auto">
            {sessions?.map((s) => (
              <div
                key={s.id}
                className={`group flex items-center gap-2 rounded px-2 py-2 ${
                  s.active ? "bg-surface" : "hover:bg-surface"
                }`}
              >
                <button
                  onClick={() => {
                    if (!s.active) activate.mutate(s.id);
                    setOpen(false);
                  }}
                  className="flex flex-1 items-center gap-2 text-left"
                >
                  <span className="w-4">{s.active && <Check size={14} className="text-success" />}</span>
                  <span className="flex-1">
                    <span className="block font-body text-sm font-semibold text-text-primary">{s.name}</span>
                    <span className="block font-body text-xs text-text-secondary">
                      {s.jobs} jobs · {s.people} people
                    </span>
                  </span>
                </button>
                {sessions.length > 1 && (
                  <button
                    title="Delete session"
                    onClick={() => {
                      if (confirm(`Delete session "${s.name}" and all its data?`)) remove.mutate(s.id);
                    }}
                    className="rounded p-1 text-neutral opacity-0 hover:bg-error/10 hover:text-error group-hover:opacity-100"
                  >
                    <Trash2 size={14} />
                  </button>
                )}
              </div>
            ))}
          </div>
          <button
            onClick={onNew}
            className="mt-1 flex w-full items-center gap-2 rounded px-2 py-2 font-body text-sm font-semibold text-primary hover:bg-primary/5"
          >
            <Plus size={16} /> New session
          </button>
        </div>
      )}
    </div>
  );
}
