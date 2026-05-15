"use client";

import { ArrowDownToLine, ArrowUpFromLine, Fingerprint } from "lucide-react";
import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { toast } from "sonner";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { api } from "@/lib/api";
import type { Device, Employee } from "@tikko/shared-types";

interface StoredTemplate {
  id: string;
  employee_id: string;
  source_device_id: string;
  finger_id: number;
  captured_at: string;
}

export default function EmployeeTemplatesClient({
  employeeId,
}: {
  employeeId: string;
}) {
  const [employee, setEmployee] = useState<Employee | null>(null);
  const [devices, setDevices] = useState<Device[]>([]);
  const [templates, setTemplates] = useState<StoredTemplate[]>([]);
  const [loading, setLoading] = useState(true);

  const [pullFromId, setPullFromId] = useState("");
  const [pulling, setPulling] = useState(false);

  const [pushSelection, setPushSelection] = useState<Record<string, boolean>>({});
  const [pushing, setPushing] = useState(false);

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      const [emp, dev, tpl] = await Promise.all([
        api.getEmployee(employeeId),
        api.listDevices(),
        api.listTemplates(employeeId),
      ]);
      setEmployee(emp);
      setDevices(dev.items);
      setTemplates(tpl.items);
      if (dev.items.length > 0 && !pullFromId) {
        setPullFromId(dev.items[0].id);
      }
    } catch (err) {
      toast.error("Failed to load templates", {
        description: err instanceof Error ? err.message : String(err),
      });
    } finally {
      setLoading(false);
    }
  }, [employeeId, pullFromId]);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const onPull = async () => {
    if (!pullFromId) return;
    setPulling(true);
    try {
      const result = await api.pullTemplates(employeeId, pullFromId);
      toast.success(
        result.stored === 0
          ? "No templates found on that device"
          : `Pulled ${result.stored} template${result.stored === 1 ? "" : "s"}`,
        {
          description:
            result.fingers.length > 0
              ? `Fingers: ${result.fingers.join(", ")}`
              : undefined,
        },
      );
      await refresh();
    } catch (err) {
      toast.error("Pull failed", {
        description: err instanceof Error ? err.message : String(err),
      });
    } finally {
      setPulling(false);
    }
  };

  const onPush = async () => {
    const deviceIds = Object.entries(pushSelection)
      .filter(([, on]) => on)
      .map(([id]) => id);
    if (deviceIds.length === 0) {
      toast.error("Pick at least one device to push to.");
      return;
    }
    setPushing(true);
    try {
      const { results } = await api.pushTemplates(employeeId, deviceIds);
      const failed = results.filter((r) => r.status === "failed");
      const synced = results.filter((r) => r.status === "pushed");
      if (failed.length === 0) {
        toast.success(
          `Pushed to ${synced.length} device${synced.length === 1 ? "" : "s"}`,
        );
      } else {
        const byId = new Map(devices.map((d) => [d.id, d.name]));
        const detail = failed
          .map((r) => `${byId.get(r.device_id) ?? r.device_id}: ${r.error ?? "failed"}`)
          .join("; ");
        toast.error(
          `Pushed ${synced.length} / ${results.length}; ${failed.length} failed`,
          { description: detail },
        );
      }
      setPushSelection({});
    } catch (err) {
      toast.error("Push failed", {
        description: err instanceof Error ? err.message : String(err),
      });
    } finally {
      setPushing(false);
    }
  };

  const deviceName = (id: string) =>
    devices.find((d) => d.id === id)?.name ?? id;

  return (
    <div className="space-y-6">
      <div>
        <Link
          href="/employees"
          className="text-sm text-muted-foreground hover:underline"
        >
          ← Employees
        </Link>
        <h1 className="mt-1 text-2xl font-semibold tracking-tight">
          Fingerprint templates
        </h1>
        {loading || !employee ? (
          <Skeleton className="mt-1 h-5 w-72" />
        ) : (
          <p className="text-sm text-muted-foreground">
            {employee.full_name}{" "}
            <span className="font-mono">(#{employee.employee_code})</span>
          </p>
        )}
      </div>

      <Card>
        <CardHeader className="flex flex-row items-center gap-3 space-y-0">
          <span className="grid h-9 w-9 place-items-center rounded-md bg-muted text-muted-foreground">
            <ArrowDownToLine className="h-5 w-5" />
          </span>
          <div>
            <CardTitle>Pull from device</CardTitle>
            <CardDescription>
              Read this employee&apos;s fingerprint templates off a terminal and
              store them.
            </CardDescription>
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-[1fr_auto]">
            <div className="grid gap-2">
              <Label htmlFor="pull_from">Source device</Label>
              <select
                id="pull_from"
                value={pullFromId}
                onChange={(e) => setPullFromId(e.target.value)}
                className="h-10 rounded-md border bg-background px-3 text-sm"
              >
                {devices.map((d) => (
                  <option key={d.id} value={d.id}>
                    {d.name}
                  </option>
                ))}
              </select>
            </div>
            <div className="flex items-end">
              <Button onClick={onPull} disabled={pulling || !pullFromId}>
                {pulling ? "Pulling…" : "Pull"}
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center gap-3 space-y-0">
          <span className="grid h-9 w-9 place-items-center rounded-md bg-muted text-muted-foreground">
            <Fingerprint className="h-5 w-5" />
          </span>
          <div>
            <CardTitle>Stored templates</CardTitle>
            <CardDescription>One row per finger, per source device.</CardDescription>
          </div>
        </CardHeader>
        <CardContent>
          {loading ? (
            <Skeleton className="h-10 w-full" />
          ) : templates.length === 0 ? (
            <p className="text-sm text-muted-foreground">
              No templates stored yet. Pull from a device above to get started.
            </p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Finger</TableHead>
                  <TableHead>Source device</TableHead>
                  <TableHead>Captured</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {templates.map((t) => (
                  <TableRow key={t.id}>
                    <TableCell>
                      <Badge variant="secondary">#{t.finger_id}</Badge>
                    </TableCell>
                    <TableCell>{deviceName(t.source_device_id)}</TableCell>
                    <TableCell className="font-mono text-xs">
                      {t.captured_at}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center gap-3 space-y-0">
          <span className="grid h-9 w-9 place-items-center rounded-md bg-muted text-muted-foreground">
            <ArrowUpFromLine className="h-5 w-5" />
          </span>
          <div>
            <CardTitle>Push to devices</CardTitle>
            <CardDescription>
              Send stored templates to one or more target terminals. Latest
              template per finger wins.
            </CardDescription>
          </div>
        </CardHeader>
        <CardContent>
          {devices.length === 0 ? (
            <p className="text-sm text-muted-foreground">
              No devices registered yet.
            </p>
          ) : (
            <div className="grid gap-3">
              <div className="grid gap-2">
                {devices.map((d) => (
                  <label key={d.id} className="flex items-center gap-2 text-sm">
                    <Checkbox
                      id={`push-${d.id}`}
                      checked={!!pushSelection[d.id]}
                      onCheckedChange={(checked) =>
                        setPushSelection((prev) => ({
                          ...prev,
                          [d.id]: checked === true,
                        }))
                      }
                    />
                    <span>
                      {d.name}{" "}
                      <span className="text-muted-foreground">
                        ({d.host}:{d.port})
                      </span>
                    </span>
                  </label>
                ))}
              </div>
              <div>
                <Button
                  onClick={onPush}
                  disabled={pushing || templates.length === 0}
                >
                  {pushing ? "Pushing…" : "Push to selected"}
                </Button>
                {templates.length === 0 && (
                  <p className="mt-1 text-xs text-muted-foreground">
                    Nothing to push — pull templates first.
                  </p>
                )}
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
