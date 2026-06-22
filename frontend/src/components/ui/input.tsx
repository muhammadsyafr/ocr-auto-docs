import { cn } from "@/lib/utils";
import type { InputHTMLAttributes, SelectHTMLAttributes } from "react";

// Coral Stay input: 48px, 1px border, focus 2px #222.
export function Input({ className, ...props }: InputHTMLAttributes<HTMLInputElement>) {
  return (
    <input
      className={cn(
        "h-12 w-full rounded border border-border px-3 font-body text-sm text-text-primary outline-none focus:border-2 focus:border-text-primary",
        className,
      )}
      {...props}
    />
  );
}

export function Select({ className, children, ...props }: SelectHTMLAttributes<HTMLSelectElement>) {
  return (
    <select
      className={cn(
        "h-12 w-full rounded border border-border px-3 font-body text-sm text-text-primary outline-none focus:border-2 focus:border-text-primary bg-white",
        className,
      )}
      {...props}
    >
      {children}
    </select>
  );
}

export function Label({ children }: { children: React.ReactNode }) {
  return <label className="mb-1 block font-body text-xs font-semibold text-text-primary">{children}</label>;
}
