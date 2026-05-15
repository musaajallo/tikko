"use client";

import { History } from "lucide-react";
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
import { Input } from "@/components/ui/input";
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
import { api, type AuditEvent } from "@/lib/api";

const PAGE_SIZE = 25;

function formatTimestamp(iso: string): string {
  try {
    return new Date(iso).toLocaleString();
  } catch {
    return iso;
  }
}

function summarize(value: unknown): string {
  if (value === null || value === undefined) return "—";
  if (typeof value === "string") return value;
  try {
    const json = JSON.stringify(value);
    return json.length > 120 ? `${json.slice(0, 117)}…` : json;
  } catch {
    return String(value);
  }
}

export default function AuditPage() {
  const [events, setEvents] = useState<AuditEvent[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);

  const [resourceType, setResourceType] = useState("");
  const [action, setAction] = useState("");

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      const { items, total } = await api.listAuditLog({
        page,
        pageSize: PAGE_SIZE,
        resourceType: resourceType.trim() || undefined,
        action: action.trim() || undefined,
      });
      setEvents(items);
      setTotal(total);
    } catch (err) {
      toast.error("Failed to load audit log", {
        description: err instanceof Error ? err.message : String(err),
      });
    } finally {
      setLoading(false);
    }
  }, [page, resourceType, action]);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Audit log</h1>
        <p className="text-sm text-muted-foreground">
          Append-only record of every state-changing action. Filter by resource
          or action to narrow the view.
        </p>
      </div>

      <Card>
        <CardHeader className="flex flex-row items-center gap-3 space-y-0">
          <span className="grid h-9 w-9 place-items-center rounded-md bg-muted text-muted-foreground">
            <History className="h-5 w-5" />
          </span>
          <div className="flex-1">
            <CardTitle>Events</CardTitle>
            <CardDescription>
              Showing {events.length} of {total} event{total === 1 ? "" : "s"}.
            </CardDescription>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <form
            onSubmit={(e) => {
              e.preventDefault();
              setPage(1);
              void refresh();
            }}
            className="grid gap-3 sm:grid-cols-[1fr_1fr_auto]"
          >
            <div className="grid gap-1">
              <Label htmlFor="resource_type">Resource type</Label>
              <Input
                id="resource_type"
                placeholder="employee, department, shift_rule…"
                value={resourceType}
                onChange={(e) => setResourceType(e.target.value)}
              />
            </div>
            <div className="grid gap-1">
              <Label htmlFor="action">Action</Label>
              <Input
                id="action"
                placeholder="create_employee, update_role…"
                value={action}
                onChange={(e) => setAction(e.target.value)}
              />
            </div>
            <div className="flex items-end">
              <Button type="submit">Apply</Button>
            </div>
          </form>

          {loading ? (
            <div className="space-y-2">
              <Skeleton className="h-10 w-full" />
              <Skeleton className="h-10 w-full" />
              <Skeleton className="h-10 w-full" />
            </div>
          ) : events.length === 0 ? (
            <p className="text-sm text-muted-foreground">
              No events match the current filters.
            </p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-[180px]">When</TableHead>
                  <TableHead>Action</TableHead>
                  <TableHead>Resource</TableHead>
                  <TableHead>Before</TableHead>
                  <TableHead>After</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {events.map((e) => (
                  <TableRow key={e.id}>
                    <TableCell className="font-mono text-xs">
                      {formatTimestamp(e.created_at)}
                    </TableCell>
                    <TableCell>
                      <Badge variant="secondary">{e.action}</Badge>
                    </TableCell>
                    <TableCell className="text-xs">
                      <div className="font-medium">{e.resource_type}</div>
                      {e.resource_id && (
                        <div className="font-mono text-muted-foreground">
                          {e.resource_id}
                        </div>
                      )}
                    </TableCell>
                    <TableCell className="text-xs text-muted-foreground">
                      {summarize(e.before)}
                    </TableCell>
                    <TableCell className="text-xs text-muted-foreground">
                      {summarize(e.after)}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}

          <div className="flex items-center justify-between text-sm text-muted-foreground">
            <span>
              Page {page} of {totalPages}
            </span>
            <div className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                disabled={page <= 1}
                onClick={() => setPage((p) => Math.max(1, p - 1))}
              >
                Previous
              </Button>
              <Button
                variant="outline"
                size="sm"
                disabled={page >= totalPages}
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              >
                Next
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
