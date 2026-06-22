import { Button } from "@/components/ui/button";
import { Input, Label } from "@/components/ui/input";
import { Td, Th } from "@/components/ui/table";
import { api } from "@/services/api";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { FileSpreadsheet, Pencil, Trash2, UserRound, X } from "lucide-react";
import { useState } from "react";
import { createPortal } from "react-dom";
import type { Person } from "@/types";

const EDIT_FIELDS: { key: keyof Person; label: string }[] = [
  { key: "nik", label: "NIK" },
  { key: "full_name", label: "Nama" },
  { key: "jenis_pelatihan", label: "Jenis pelatihan" },
  { key: "place_of_birth", label: "Tempat lahir" },
  { key: "date_of_birth", label: "Tanggal lahir" },
  { key: "company_name", label: "Nama perusahaan" },
  { key: "company_address", label: "Alamat perusahaan" },
  { key: "ket", label: "Keterangan (KET)" },
];

export function Document() {
  const qc = useQueryClient();
  const { data: people } = useQuery({ queryKey: ["people"], queryFn: api.people, refetchInterval: 5000 });
  const [zoom, setZoom] = useState<{ src: string; name: string } | null>(null);
  const [edit, setEdit] = useState<Person | null>(null);
  const [tip, setTip] = useState<{ text: string; x: number; y: number } | null>(null);

  const showTip = (e: React.MouseEvent, text: string) => {
    const r = (e.currentTarget as HTMLElement).getBoundingClientRect();
    setTip({ text, x: r.left, y: r.bottom + 6 });
  };

  const invalidate = () => {
    qc.invalidateQueries({ queryKey: ["people"] });
    qc.invalidateQueries({ queryKey: ["docInfo"] });
  };
  const remove = useMutation({ mutationFn: api.removePerson, onSuccess: invalidate });
  const save = useMutation({
    mutationFn: (p: Person) =>
      api.updatePerson(p.job_id, {
        nik: p.nik ?? "",
        full_name: p.full_name ?? "",
        jenis_pelatihan: p.jenis_pelatihan ?? "",
        place_of_birth: p.place_of_birth ?? "",
        date_of_birth: p.date_of_birth ?? "",
        company_name: p.company_name ?? "",
        company_address: p.company_address ?? "",
        ket: p.ket ?? "",
      }),
    onSuccess: () => {
      invalidate();
      setEdit(null);
    },
  });

  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="font-display text-[32px] font-bold text-text-primary">People Document</h1>
          <p className="font-body text-sm text-text-secondary">
            {people?.length ?? 0} people in the master spreadsheet.
          </p>
        </div>
        <a href={api.docDownloadUrl()}>
          <Button variant="primary" disabled={!people?.length}>
            <FileSpreadsheet size={16} />
            Download Excel
          </Button>
        </a>
      </div>

      <div className="overflow-x-auto rounded-lg border border-border bg-white shadow-lvl1">
        <table className="min-w-max border-collapse whitespace-nowrap text-sm">
          <thead>
            <tr>
              <Th>No</Th>
              <Th>Scan KTP</Th>
              <Th>NIK</Th>
              <Th>Nama</Th>
              <Th>Jenis pelatihan</Th>
              <Th>Tempat lahir</Th>
              <Th>Tanggal lahir</Th>
              <Th>Nama perusahaan</Th>
              <Th>Alamat perusahaan</Th>
              <Th>Ket</Th>
              <Th></Th>
            </tr>
          </thead>
          <tbody>
            {people?.map((p, idx) => (
              <tr key={p.job_id}>
                <Td className="text-center text-text-secondary">{idx + 1}</Td>
                <Td className="w-40">
                  {p.photo_path ? (
                    <img
                      src={api.personPhotoUrl(p.job_id)}
                      alt={p.full_name ?? "photo"}
                      onClick={() =>
                        setZoom({ src: api.personPhotoUrl(p.job_id), name: p.full_name ?? p.zip_name ?? "Photo" })
                      }
                      className="h-20 w-36 cursor-zoom-in rounded border border-border object-contain bg-surface transition-transform hover:scale-105"
                    />
                  ) : (
                    <span className="flex h-20 w-36 items-center justify-center rounded bg-surface text-neutral">
                      <UserRound size={24} />
                    </span>
                  )}
                </Td>
                <Td className="font-mono text-xs">{p.nik ?? "—"}</Td>
                <Td className="font-semibold">{p.full_name ?? "—"}</Td>
                <Td>{p.jenis_pelatihan ?? "—"}</Td>
                <Td>{p.place_of_birth ?? "—"}</Td>
                <Td>{p.date_of_birth ?? "—"}</Td>
                <Td>{p.company_name ?? "—"}</Td>
                <Td className="text-text-secondary">
                  <span
                    className="block max-w-md cursor-help truncate"
                    onMouseEnter={(e) => p.company_address && showTip(e, p.company_address)}
                    onMouseLeave={() => setTip(null)}
                  >
                    {p.company_address ?? "—"}
                  </span>
                </Td>
                <Td className="text-text-secondary">{p.ket ?? "—"}</Td>
                <Td>
                  <div className="flex gap-2">
                    <button
                      onClick={() => setEdit(p)}
                      className="flex items-center gap-1 rounded border border-border px-2 py-1 text-xs font-semibold text-text-primary hover:bg-surface"
                    >
                      <Pencil size={14} /> Edit
                    </button>
                    <button
                      onClick={() => {
                        if (confirm(`Remove ${p.full_name ?? p.zip_name} from the doc?`))
                          remove.mutate(p.job_id);
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
            {!people?.length && (
              <tr>
                <Td colSpan={11} className="text-center text-text-secondary">
                  No people yet. Go to Results and click “Push to doc” on a completed zip.
                </Td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Address tooltip (portal -> escapes the table's overflow clip) */}
      {tip &&
        createPortal(
          <div
            className="pointer-events-none fixed z-[60] max-w-sm rounded-lg border border-border bg-white p-3 text-xs text-text-primary shadow-lvl2"
            style={{ left: tip.x, top: tip.y }}
          >
            {tip.text}
          </div>,
          document.body,
        )}

      {/* Photo lightbox */}
      {zoom && (
        <div
          onClick={() => setZoom(null)}
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-6"
        >
          <div
            onClick={(e) => e.stopPropagation()}
            className="relative max-h-[90vh] max-w-[90vw] rounded-xl bg-white p-3 shadow-lvl3"
          >
            <button
              onClick={() => setZoom(null)}
              className="absolute -right-3 -top-3 rounded-full bg-white p-1 text-text-primary shadow-lvl2 hover:bg-surface"
              aria-label="Close"
            >
              <X size={18} />
            </button>
            <img src={zoom.src} alt={zoom.name} className="max-h-[80vh] max-w-full rounded object-contain" />
            <p className="mt-2 text-center font-body text-sm font-semibold text-text-primary">{zoom.name}</p>
          </div>
        </div>
      )}

      {/* Edit person modal */}
      {edit && (
        <div
          onClick={() => setEdit(null)}
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-6"
        >
          <div
            onClick={(e) => e.stopPropagation()}
            className="w-full max-w-lg rounded-xl bg-white p-6 shadow-lvl3"
          >
            <div className="mb-4 flex items-center justify-between">
              <h2 className="font-display text-xl font-bold text-text-primary">
                Edit {edit.zip_name ?? "person"}
              </h2>
              <button onClick={() => setEdit(null)} className="text-neutral hover:text-text-primary">
                <X size={18} />
              </button>
            </div>
            <div className="grid grid-cols-2 gap-3">
              {EDIT_FIELDS.map((f) => (
                <div key={f.key} className={f.key === "company_address" ? "col-span-2" : ""}>
                  <Label>{f.label}</Label>
                  <Input
                    value={(edit[f.key] as string | undefined) ?? ""}
                    onChange={(e) => setEdit({ ...edit, [f.key]: e.target.value })}
                  />
                </div>
              ))}
            </div>
            <div className="mt-6 flex justify-end gap-3">
              <Button variant="secondary" onClick={() => setEdit(null)}>
                Cancel
              </Button>
              <Button onClick={() => save.mutate(edit)} disabled={save.isPending}>
                {save.isPending ? "Saving…" : "Save"}
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
