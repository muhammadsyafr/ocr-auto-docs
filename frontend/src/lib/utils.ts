import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/** Status -> Coral Stay color (Completed=green, Processing=orange, Failed=red, Queued=gray). */
export function statusColor(status: string): string {
  switch (status) {
    case "completed":
      return "text-success border-success/30 bg-success/10";
    case "processing":
      return "text-warning border-warning/30 bg-warning/10";
    case "failed":
      return "text-error border-error/30 bg-error/10";
    default:
      return "text-neutral border-border bg-surface";
  }
}

/** Confidence -> color (high green / mid orange / low red). */
export function confidenceColor(conf: number): string {
  if (conf >= 0.85) return "text-success";
  if (conf >= 0.6) return "text-warning";
  return "text-error";
}
