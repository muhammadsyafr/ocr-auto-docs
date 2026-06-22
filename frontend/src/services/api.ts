import type {
  DocumentOut,
  Job,
  LLMProviders,
  Metrics,
  Person,
  ResultDetail,
  WorkSession,
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

  uploadFolder: async (files: File[], folderName: string): Promise<Job> => {
    const form = new FormData();
    files.forEach((f) => form.append("files", f));
    form.append("folder_name", folderName);
    const res = await fetch(`${BASE}/upload-folder`, { method: "POST", body: form });
    if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
    return res.json();
  },

  exportJson: () => http<unknown>("/export/json"),

  // Master document (1 ZIP = 1 person)
  pushToDoc: (jobId: string) => http<Person>(`/doc/push/${jobId}`, { method: "POST" }),
  people: () => http<Person[]>("/doc/people"),
  updatePerson: (jobId: string, patch: Partial<Person>) =>
    http<Person>(`/doc/people/${jobId}`, { method: "PATCH", body: JSON.stringify(patch) }),
  removePerson: (jobId: string) =>
    http<{ removed: string }>(`/doc/people/${jobId}`, { method: "DELETE" }),
  personPhotoUrl: (jobId: string) => `${BASE}/doc/people/${jobId}/photo`,
  docInfo: () => http<{ rows: number }>("/doc/info"),
  docDownloadUrl: () => `${BASE}/doc/download`,

  // Sessions (workspaces)
  sessions: () => http<WorkSession[]>("/sessions"),
  createSession: (name: string) =>
    http<WorkSession>("/sessions", { method: "POST", body: JSON.stringify({ name }) }),
  activateSession: (id: string) =>
    http<WorkSession>(`/sessions/${id}/activate`, { method: "PUT" }),
  deleteSession: (id: string) =>
    http<{ deleted: string; active: string }>(`/sessions/${id}`, { method: "DELETE" }),
};
