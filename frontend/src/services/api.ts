import type {
  DocumentOut,
  Job,
  LLMProviders,
  Metrics,
  ResultDetail,
} from "@/types";

const BASE = "/api";

async function http<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  return res.json() as Promise<T>;
}

export interface LLMSelection {
  provider: string;
  model: string;
}

export const api = {
  metrics: () => http<Metrics>("/metrics"),
  jobs: () => http<Job[]>("/jobs"),
  cancelJob: (id: string) => http<Job>(`/jobs/${id}/cancel`, { method: "POST" }),
  deleteJob: (id: string) => http<{ deleted: string }>(`/jobs/${id}`, { method: "DELETE" }),
  results: () => http<DocumentOut[]>("/results"),
  resultDetail: (id: string) => http<ResultDetail>(`/results/${id}`),
  fileUrl: (id: string) => `${BASE}/results/${id}/file`,
  providers: () => http<LLMProviders>("/llm/providers"),

  setDefaultLLM: (sel: LLMSelection) =>
    http<LLMSelection>("/settings/llm", {
      method: "PUT",
      body: JSON.stringify(sel),
    }),

  processFolder: (path: string, llm?: LLMSelection) =>
    http<Job>("/process-folder", {
      method: "POST",
      body: JSON.stringify({ path, llm }),
    }),

  processZip: (path: string, llm?: LLMSelection) =>
    http<Job>("/process-zip", {
      method: "POST",
      body: JSON.stringify({ path, llm }),
    }),

  upload: async (file: File): Promise<Job> => {
    const form = new FormData();
    form.append("file", file);
    const res = await fetch(`${BASE}/upload`, { method: "POST", body: form });
    if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
    return res.json();
  },

  exportJson: () => http<unknown>("/export/json"),
};
