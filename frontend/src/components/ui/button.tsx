import { cn } from "@/lib/utils";
import type { ButtonHTMLAttributes } from "react";

type Variant = "primary" | "secondary" | "ghost";

interface Props extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
  size?: "md" | "lg";
}

// Coral Stay buttons (DESIGN.md): coral primary reserved for primary CTAs.
const variants: Record<Variant, string> = {
  primary: "bg-primary text-white hover:bg-primary-hover",
  secondary: "border border-text-primary text-text-primary hover:bg-surface",
  ghost: "text-text-primary hover:bg-surface",
};

export function Button({ variant = "primary", size = "md", className, ...props }: Props) {
  return (
    <button
      className={cn(
        "inline-flex items-center justify-center gap-2 rounded font-body font-semibold transition-colors duration-150 disabled:opacity-50 disabled:pointer-events-none",
        size === "lg" ? "h-12 px-8 text-base" : "h-10 px-4 text-sm",
        variants[variant],
        className,
      )}
      {...props}
    />
  );
}
