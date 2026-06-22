import { cn } from "@/lib/utils";
import type { HTMLAttributes } from "react";

// Coral Stay card: 12px radius, border, Level 1 shadow, hover -> Level 2 + lift.
export function Card({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn(
        "rounded-lg border border-border bg-white shadow-lvl1 transition-all duration-200 hover:shadow-lvl2 hover:-translate-y-0.5",
        className,
      )}
      {...props}
    />
  );
}

export function CardBody({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return <div className={cn("p-6", className)} {...props} />;
}

export function CardTitle({ className, ...props }: HTMLAttributes<HTMLHeadingElement>) {
  return (
    <h3 className={cn("font-display text-[22px] leading-7 font-bold text-text-primary", className)} {...props} />
  );
}
