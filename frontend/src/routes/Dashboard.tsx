import { Card, CardBody } from "@/components/ui/card";
import { api } from "@/services/api";
import { useQuery } from "@tanstack/react-query";

const cards = [
  { key: "total", label: "Total Documents", color: "text-text-primary" },
  { key: "successful", label: "Successful", color: "text-success" },
  { key: "failed", label: "Failed", color: "text-error" },
  { key: "processing", label: "Processing", color: "text-warning" },
] as const;

export function Dashboard() {
  const { data } = useQuery({ queryKey: ["metrics"], queryFn: api.metrics, refetchInterval: 3000 });

  return (
    <div>
      <h1 className="mb-6 font-display text-[32px] font-bold text-text-primary">Dashboard</h1>
      <div className="grid grid-cols-2 gap-6 md:grid-cols-4">
        {cards.map((c) => (
          <Card key={c.key}>
            <CardBody>
              <p className="font-body text-xs font-semibold uppercase tracking-wide text-neutral">{c.label}</p>
              <p className={`mt-2 font-display text-[40px] font-extrabold ${c.color}`}>
                {data?.[c.key] ?? 0}
              </p>
            </CardBody>
          </Card>
        ))}
      </div>
    </div>
  );
}
