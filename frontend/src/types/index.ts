export type DocStatus = "queued" | "processing" | "completed" | "failed";

export interface Job {
  id: string;
  source_type: string;
  source_path: string;
  status: DocStatus;
  total: number;
  successful: number;
  failed: number;
  llm_provider?: string;
  llm_model?: string;
  created_at: string;
  completed_at?: string;
}

export interface DocumentOut {
  id: string;
  job_id?: string;
  filename: string;
  document_type?: string;
  status: DocStatus;
  confidence?: number;
  error?: string;
}

export interface UnifiedResult {
  file_name: string;
  document_type?: string;
  confidence?: number;
  fields: Record<string, string | null>;
  field_confidence: Record<string, number>;
}

export interface ResultDetail {
  document: DocumentOut;
  result: UnifiedResult;
}

export interface Metrics {
  total: number;
  successful: number;
  failed: number;
  processing: number;
}

export interface LLMProvider {
  provider: string;
  models: string[];
  configured: boolean;
}

export interface LLMProviders {
  active: { provider: string; model: string };
  providers: LLMProvider[];
}

export interface WorkSession {
  id: string;
  name: string;
  active: boolean;
  jobs: number;
  people: number;
}

export interface Person {
  job_id: string;
  zip_name?: string;
  nik?: string;
  full_name?: string;
  place_of_birth?: string;
  date_of_birth?: string;
  company_name?: string;
  company_address?: string;
  jenis_pelatihan?: string;
  ket?: string;
  photo_path?: string;
}
