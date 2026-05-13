"use client";

import { Cpu, Radio, Clock, Calendar } from "lucide-react";
import { useEffect, useState } from "react";

import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { api, type Stats } from "@/lib/api";

type KpiVariant = "default" | "blue" | "amber" | "emerald";

interface KpiSpec {
  label: string;
  value: (s: Stats) => string;
  hint: (s: Stats) => string;
  icon: typeof Cpu;
  variant: KpiVariant;
}

const KPI_SPECS: KpiSpec[] = [
  {
    label: "Total devices",
    value: (s) => s.devices.toString(),
    hint: (s) => `${s.devices_enabled} enabled`,
    icon: Cpu,
    variant: "emerald",
  },
  {
    label: "Online",
    value: (s) => s.devices_online.toString(),
    hint: (s) => `of ${s.devices_enabled} enabled`,
    icon: Radio,
    variant: "blue",
  },
  {
    label: "Punches today",
    value: (s) => s.punches_today.toLocaleString(),
    hint: () => "since midnight UTC",
    icon: Clock,
    variant: "amber",
  },
  {
    label: "Last 24h",
    value: (s) => s.punches_24h.toLocaleString(),
    hint: () => "rolling window",
    icon: Calendar,
    variant: "default",
  },
];

const VARIANT_TINT: Record<KpiVariant, string> = {
  default: "bg-muted text-foreground",
  blue: "bg-blue-100 text-blue-700 dark:bg-blue-500/15 dark:text-blue-300",
  amber: "bg-amber-100 text-amber-700 dark:bg-amber-500/15 dark:text-amber-300",
  emerald: "bg-emerald-100 text-emerald-700 dark:bg-emerald-500/15 dark:text-emerald-300",
};

export function KpiCards() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const result = await api.getStats();
        if (!cancelled) setStats(result);
      } catch {
        if (!cancelled) setError(true);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
      {KPI_SPECS.map((spec) => {
        const Icon = spec.icon;
        return (
          <Card key={spec.label}>
            <CardContent className="flex items-start justify-between gap-3 p-5">
              <div className="space-y-1">
                <p className="text-sm font-medium text-muted-foreground">{spec.label}</p>
                {stats ? (
                  <p className="text-3xl font-semibold tracking-tight">
                    {spec.value(stats)}
                  </p>
                ) : error ? (
                  <p className="text-3xl font-semibold tracking-tight text-muted-foreground">
                    —
                  </p>
                ) : (
                  <Skeleton className="h-8 w-16" />
                )}
                <p className="text-xs text-muted-foreground">
                  {stats ? spec.hint(stats) : ""}
                </p>
              </div>
              <span
                className={`grid h-10 w-10 place-items-center rounded-md ${VARIANT_TINT[spec.variant]}`}
              >
                <Icon className="h-5 w-5" />
              </span>
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}
