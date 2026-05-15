"use client";

import { Check, Inbox, X } from "lucide-react";
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

type LeaveStatus = "pending" | "approved" | "rejected";

interface LeaveRow {
  id: string;
  employee_id: string;
  employee_code: string | null;
  employee_full_name: string | null;
  start_date: string;
  end_date: string;
  reason: string;
  status: LeaveStatus;
  created_at: string;
  decided_at: string | null;
  decided_by_user_id: string | null;
}

const STATUS_VARIANT: Record<LeaveStatus, "default" | "secondary" | "destructive"> = {
  pending: "secondary",
  approved: "default",
  rejected: "destructive",
};

function formatDate(iso: string): string {
  try {
    return new Date(iso + "T00:00:00Z").toLocaleDateString(undefined, {
      year: "numeric",
      month: "short",
      day: "numeric",
    });
  } catch {
    return iso;
  }
}

export default function LeaveRequestsPage() {
  const [filter, setFilter] = useState<LeaveStatus | "">("pending");
  const [items, setItems] = useState<LeaveRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [pendingId, setPendingId] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      const result = await api.listLeaveRequests(filter || undefined);
      setItems(result.items);
    } catch (err) {
      toast.error("Failed to load leave requests", {
        description: err instanceof Error ? err.message : String(err),
      });
    } finally {
      setLoading(false);
    }
  }, [filter]);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const decide = async (row: LeaveRow, decision: "approved" | "rejected") => {
    setPendingId(row.id);
    try {
      await api.decideLeaveRequest(row.id, decision);
      toast.success(
        `${decision === "approved" ? "Approved" : "Rejected"} ${row.employee_full_name ?? row.employee_id}`,
      );
      await refresh();
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      toast.error("Could not decide", {
        description: /409/.test(message)
          ? "This request was already decided. The list will refresh."
          : message,
      });
      if (/409/.test(message)) await refresh();
    } finally {
      setPendingId(null);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Leave requests</h1>
        <p className="text-sm text-muted-foreground">
          Approve or reject submissions from your team. Decisions are final.
        </p>
      </div>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between gap-2 space-y-0">
          <div className="flex items-center gap-3">
            <span className="grid h-9 w-9 place-items-center rounded-md bg-muted text-muted-foreground">
              <Inbox className="h-5 w-5" />
            </span>
            <div>
              <CardTitle>All requests</CardTitle>
              <CardDescription>
                Filter by status. Newest first.
              </CardDescription>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <label htmlFor="filter" className="text-sm text-muted-foreground">
              Status
            </label>
            <select
              id="filter"
              value={filter}
              onChange={(e) => setFilter(e.target.value as LeaveStatus | "")}
              className="h-9 rounded-md border bg-background px-3 text-sm"
            >
              <option value="">all</option>
              <option value="pending">pending</option>
              <option value="approved">approved</option>
              <option value="rejected">rejected</option>
            </select>
          </div>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="space-y-2">
              <Skeleton className="h-10 w-full" />
              <Skeleton className="h-10 w-full" />
            </div>
          ) : items.length === 0 ? (
            <p className="text-sm text-muted-foreground">
              No requests match this filter.
            </p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Employee</TableHead>
                  <TableHead>Dates</TableHead>
                  <TableHead>Reason</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="w-[180px] text-right"></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {items.map((row) => (
                  <TableRow key={row.id}>
                    <TableCell className="font-medium">
                      {row.employee_full_name ?? "Unknown employee"}
                      <span className="ml-1 font-mono text-xs text-muted-foreground">
                        #{row.employee_code ?? "?"}
                      </span>
                    </TableCell>
                    <TableCell className="text-sm">
                      {formatDate(row.start_date)} – {formatDate(row.end_date)}
                    </TableCell>
                    <TableCell className="max-w-sm truncate text-sm">
                      {row.reason}
                    </TableCell>
                    <TableCell>
                      <Badge variant={STATUS_VARIANT[row.status]}>{row.status}</Badge>
                    </TableCell>
                    <TableCell className="text-right">
                      {row.status === "pending" ? (
                        <div className="flex justify-end gap-2">
                          <Button
                            size="sm"
                            onClick={() => decide(row, "approved")}
                            disabled={pendingId === row.id}
                          >
                            <Check className="mr-1 h-4 w-4" />
                            Approve
                          </Button>
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => decide(row, "rejected")}
                            disabled={pendingId === row.id}
                          >
                            <X className="mr-1 h-4 w-4" />
                            Reject
                          </Button>
                        </div>
                      ) : (
                        <span className="text-xs text-muted-foreground">
                          decided
                        </span>
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
