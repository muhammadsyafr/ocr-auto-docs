import { Button } from "@/components/ui/button";
import { Card, CardBody, CardTitle } from "@/components/ui/card";
import { Label, Select } from "@/components/ui/input";
import { api } from "@/services/api";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Check, WifiOff } from "lucide-react";
import { useEffect, useState } from "react";

export function SettingsPage() {
  const qc = useQueryClient();
  const { data } = useQuery({ queryKey: ["providers"], queryFn: api.providers });
  const [provider, setProvider] = useState("");
  const [model, setModel] = useState("");

  useEffect(() => {
    if (data) {
      setProvider(data.active.provider);
      setModel(data.active.model);
    }
  }, [data]);

  const save = useMutation({
    mutationFn: () => api.setDefaultLLM({ provider, model }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["providers"] }),
  });

  const current = data?.providers.find((p) => p.provider === provider);

  return (
    <div className="max-w-2xl">
      <h1 className="mb-6 font-display text-[32px] font-bold text-text-primary">Settings</h1>

      <Card className="mb-6">
        <CardBody>
          <CardTitle>Default LLM Provider</CardTitle>
          <p className="mt-1 font-body text-sm text-text-secondary">
            API keys are configured server-side and never shown here.
          </p>
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
                {data?.providers.map((p) => (
                  <option key={p.provider} value={p.provider} disabled={!p.configured}>
                    {p.provider}
                    {p.configured ? "" : " — not configured"}
                  </option>
                ))}
              </Select>
            </div>
            <div>
              <Label>Model</Label>
              <Select value={model} onChange={(e) => setModel(e.target.value)}>
                {current?.models.map((m) => (
                  <option key={m} value={m}>
                    {m}
                  </option>
                ))}
              </Select>
            </div>
          </div>
          <div className="mt-6 flex items-center justify-between">
            <span className="font-body text-sm text-success">
              {save.isSuccess ? "Saved." : ""}
            </span>
            <Button disabled={!provider || !model || save.isPending} onClick={() => save.mutate()}>
              Save Default
            </Button>
          </div>
        </CardBody>
      </Card>

      <Card>
        <CardBody>
          <CardTitle>Configured Providers</CardTitle>
          <div className="mt-4 space-y-2">
            {data?.providers.map((p) => (
              <div key={p.provider} className="flex items-center justify-between border-b border-border py-2">
                <span className="font-body text-sm font-semibold capitalize text-text-primary">
                  {p.provider}
                </span>
                <span className="flex items-center gap-3 font-body text-xs">
                  {p.offline && (
                    <span className="flex items-center gap-1 text-secondary">
                      <WifiOff size={14} /> offline
                    </span>
                  )}
                  {p.configured ? (
                    <span className="flex items-center gap-1 text-success">
                      <Check size={14} /> configured
                    </span>
                  ) : (
                    <span className="text-neutral">not configured</span>
                  )}
                </span>
              </div>
            ))}
          </div>
        </CardBody>
      </Card>
    </div>
  );
}
