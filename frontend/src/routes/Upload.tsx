import { Button } from "@/components/ui/button";
import { Card, CardBody, CardTitle } from "@/components/ui/card";
import { Input, Label, Select } from "@/components/ui/input";
import { api } from "@/services/api";
import { useMutation, useQuery } from "@tanstack/react-query";
import { useNavigate } from "@tanstack/react-router";
import { FolderUp, UploadCloud } from "lucide-react";
import { useState } from "react";

const SUPPORTED = [".pdf", ".jpg", ".jpeg", ".png", ".tiff", ".tif", ".bmp"];
const isSupported = (name: string) => SUPPORTED.some((e) => name.toLowerCase().endsWith(e));

export function Upload() {
  const navigate = useNavigate();
  const { data: providers } = useQuery({ queryKey: ["providers"], queryFn: api.providers });
  const [folderPath, setFolderPath] = useState("");
  const [provider, setProvider] = useState("");
  const [model, setModel] = useState("");
  const [dragging, setDragging] = useState(false);

  const llm = provider && model ? { provider, model } : undefined;

  const goJobs = () => navigate({ to: "/jobs" });

  const uploadFile = useMutation({ mutationFn: (f: File) => api.upload(f), onSuccess: goJobs });
  const processFolder = useMutation({
    mutationFn: () => api.processFolder(folderPath, llm),
    onSuccess: goJobs,
  });
  const uploadFolder = useMutation({
    mutationFn: ({ files, name }: { files: File[]; name: string }) => api.uploadFolder(files, name),
    onSuccess: goJobs,
    onError: (e) => alert(`Folder upload failed: ${e instanceof Error ? e.message : e}`),
  });

  const onPickFolder = (e: React.ChangeEvent<HTMLInputElement>) => {
    const all = Array.from(e.target.files ?? []);
    e.target.value = ""; // allow re-selecting the same folder
    if (all.length === 0) return;
    const files = all.filter((f) => isSupported(f.name));
    if (files.length === 0) {
      alert(`Folder has ${all.length} files but none are supported (PDF/JPG/PNG/TIFF/BMP).`);
      return;
    }
    const rel = (all[0] as File & { webkitRelativePath?: string }).webkitRelativePath ?? "";
    const name = rel.split("/")[0] || "upload";
    uploadFolder.mutate({ files, name });
  };

  const activeProvider = providers?.providers.find((p) => p.provider === (provider || providers.active.provider));

  return (
    <div className="max-w-2xl">
      <h1 className="mb-6 font-display text-[32px] font-bold text-text-primary">Upload Documents</h1>

      {/* Drag & drop / ZIP upload */}
      <Card className="mb-6">
        <CardBody>
          <CardTitle>Upload File or ZIP</CardTitle>
          <div
            onDragOver={(e) => {
              e.preventDefault();
              setDragging(true);
            }}
            onDragLeave={() => setDragging(false)}
            onDrop={(e) => {
              e.preventDefault();
              setDragging(false);
              const f = e.dataTransfer.files[0];
              if (f) uploadFile.mutate(f);
            }}
            className={`mt-4 flex flex-col items-center justify-center rounded-xl border-2 border-dashed p-10 text-center transition-colors ${
              dragging ? "border-primary bg-primary/5" : "border-border"
            }`}
          >
            <UploadCloud className="mb-3 text-neutral" size={36} />
            <p className="font-body text-sm text-text-secondary">Drag & drop a document or ZIP here</p>
            <label className="mt-3 cursor-pointer font-body text-sm font-semibold text-primary">
              or browse
              <input
                type="file"
                className="hidden"
                onChange={(e) => e.target.files?.[0] && uploadFile.mutate(e.target.files[0])}
              />
            </label>
          </div>
        </CardBody>
      </Card>

      {/* Folder upload (browser, webkitdirectory) — 1 folder = 1 person */}
      <Card className="mb-6">
        <CardBody>
          <CardTitle>Upload Folder</CardTitle>
          <p className="mt-1 font-body text-sm text-text-secondary">
            Pick a folder of one person's documents (KTP, ijazah, employment letter). All files become one job.
          </p>
          <label className="mt-4 flex cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed border-border p-10 text-center hover:border-primary">
            <FolderUp className="mb-3 text-neutral" size={36} />
            <span className="font-body text-sm font-semibold text-primary">
              {uploadFolder.isPending ? "Uploading…" : "Choose a folder"}
            </span>
            <input
              type="file"
              className="hidden"
              // @ts-expect-error webkitdirectory is non-standard (folder selection)
              webkitdirectory=""
              onChange={onPickFolder}
            />
          </label>
        </CardBody>
      </Card>

      {/* LLM selector (per-job override) */}
      <Card className="mb-6">
        <CardBody>
          <CardTitle>LLM Provider (optional override)</CardTitle>
          <div className="mt-4 grid grid-cols-2 gap-4">
            <div>
              <Label>Provider</Label>
              <Select
                value={provider}
                onChange={(e) => {
                  setProvider(e.target.value);
                  setModel("");
                }}
              >
                <option value="">Use default ({providers?.active.provider})</option>
                {providers?.providers.map((p) => (
                  <option key={p.provider} value={p.provider} disabled={!p.configured}>
                    {p.provider}
                    {p.offline ? " (offline)" : ""}
                    {p.configured ? "" : " — not configured"}
                  </option>
                ))}
              </Select>
            </div>
            <div>
              <Label>Model</Label>
              <Select value={model} onChange={(e) => setModel(e.target.value)} disabled={!provider}>
                <option value="">Select model</option>
                {activeProvider?.models.map((m) => (
                  <option key={m} value={m}>
                    {m}
                  </option>
                ))}
              </Select>
            </div>
          </div>
        </CardBody>
      </Card>

      {/* Folder path */}
      <Card>
        <CardBody>
          <CardTitle>Process Server Folder</CardTitle>
          <div className="mt-4">
            <Label>Folder path</Label>
            <Input
              placeholder="/data/input"
              value={folderPath}
              onChange={(e) => setFolderPath(e.target.value)}
            />
          </div>
          <div className="mt-6 flex justify-end">
            <Button
              size="lg"
              disabled={!folderPath || processFolder.isPending}
              onClick={() => processFolder.mutate()}
            >
              Start Processing
            </Button>
          </div>
        </CardBody>
      </Card>
    </div>
  );
}
