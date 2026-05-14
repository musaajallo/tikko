"use client";

import { Download, FileBarChart, Play } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { toast } from "sonner";

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
import { api, type AttendanceReport } from "@/lib/api";
import type { Employee } from "@tikko/shared-types";

function currentMonth(): string {
  const now = new Date();
  return `${now.getUTCFullYear()}-${String(now.getUTCMonth() + 1).padStart(2, "0")}`;
}

function formatMinutes(min: number): string {
  if (min === 0) return "0m";
  const h = Math.floor(min / 60);
  const m = min % 60;
  return h ? `${h}h ${m}m` : `${m}m`;
}

export default function ReportsPage() {
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [employeeId, setEmployeeId] = useState<string>("");
  const [month, setMonth] = useState(currentMonth());

  const [report, setReport] = useState<AttendanceReport | null>(null);
  const [loadingEmployees, setLoadingEmployees] = useState(true);
  const [runningReport, setRunningReport] = useState(false);
  const [downloading, setDownloading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const { items } = await api.listEmployees();
        if (cancelled) return;
        setEmployees(items);
        if (items.length > 0) setEmployeeId(items[0].id);
      } catch (err) {
        if (cancelled) return;
        toast.error("Failed to load employees", {
          description: err instanceof Error ? err.message : String(err),
        });
      } finally {
        if (!cancelled) setLoadingEmployees(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const runReport = useCallback(async () => {
    if (!employeeId || !month) return;
    setRunningReport(true);
    setError(null);
    setReport(null);
    try {
      const result = await api.attendanceReport(employeeId, month);
      setReport(result);
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      // The API returns 422 with "employee has no assigned shift rule" when the
      // employee isn't bound to a ShiftRule. Surface the situation in plain words
      // rather than the raw "422 …" string from request<T>.
      if (/no assigned shift rule|shift rule/i.test(message)) {
        setError(
          "This employee has no assigned shift rule. Assign one on the Employees page and try again.",
        );
      } else {
        setError(message);
      }
    } finally {
      setRunningReport(false);
    }
  }, [employeeId, month]);

  const downloadCsv = useCallback(async () => {
    if (!employeeId || !month) return;
    setDownloading(true);
    try {
      const { blob, filename } = await api.downloadAttendanceCsv(employeeId, month);
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
    } catch (err) {
      toast.error("Download failed", {
        description: err instanceof Error ? err.message : String(err),
      });
    } finally {
      setDownloading(false);
    }
  }, [employeeId, month]);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Reports</h1>
        <p className="text-sm text-muted-foreground">
          Per-employee monthly attendance. Late / early-out / overtime are computed against the
          employee&apos;s shift rule.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Filters</CardTitle>
          <CardDescription>
            Pick an employee and a month, then run the report or download CSV.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form
            onSubmit={(e) => {
              e.preventDefault();
              void runReport();
            }}
            className="grid gap-4 md:grid-cols-[1fr_180px_auto_auto]"
          >
            <div className="grid gap-2">
              <Label htmlFor="employee">Employee</Label>
              {loadingEmployees ? (
                <Skeleton className="h-10 w-full" />
              ) : (
                <select
                  id="employee"
                  value={employeeId}
                  onChange={(e) => setEmployeeId(e.target.value)}
                  className="h-10 rounded-md border bg-background px-3 text-sm"
                >
                  {employees.map((e) => (
                    <option key={e.id} value={e.id}>
                      {e.full_name} (#{e.employee_code})
                    </option>
                  ))}
                </select>
              )}
            </div>
            <div className="grid gap-2">
              <Label htmlFor="month">Month</Label>
              <Input
                id="month"
                type="month"
                value={month}
                onChange={(e) => setMonth(e.target.value)}
                required
              />
            </div>
            <div className="flex items-end">
              <Button type="submit" disabled={runningReport || !employeeId}>
                <Play className="mr-1 h-4 w-4" />
                {runningReport ? "Running…" : "Run report"}
              </Button>
            </div>
            <div className="flex items-end">
              <Button
                type="button"
                variant="outline"
                onClick={downloadCsv}
                disabled={downloading || !employeeId}
              >
                <Download className="mr-1 h-4 w-4" />
                {downloading ? "Downloading…" : "Download CSV"}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>

      {error && (
        <Card>
          <CardContent className="py-6">
            <p role="alert" className="text-sm text-destructive">
              {error}
            </p>
          </CardContent>
        </Card>
      )}

      {report && (
        <>
          <Card>
            <CardHeader>
              <CardTitle>Totals</CardTitle>
              <CardDescription>
                {report.employee.full_name} (#{report.employee.employee_code}) — {report.month}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 gap-4 md:grid-cols-3 lg:grid-cols-6">
                <Kpi label="Days worked" value={String(report.totals.days_worked)} />
                <Kpi label="Days absent" value={String(report.totals.days_absent)} />
                <Kpi label="Worked" value={formatMinutes(report.totals.worked_minutes)} />
                <Kpi label="Late" value={formatMinutes(report.totals.late_minutes)} />
                <Kpi label="Early out" value={formatMinutes(report.totals.early_out_minutes)} />
                <Kpi label="Overtime" value={formatMinutes(report.totals.overtime_minutes)} />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center gap-2 space-y-0">
              <FileBarChart className="h-4 w-4 text-muted-foreground" />
              <CardTitle>Daily breakdown</CardTitle>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Date</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Worked</TableHead>
                    <TableHead>Late</TableHead>
                    <TableHead>Early out</TableHead>
                    <TableHead>Overtime</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {report.days.map((d) => (
                    <TableRow key={d.date}>
                      <TableCell className="font-mono text-xs">{d.date}</TableCell>
                      <TableCell className="text-muted-foreground">
                        {d.is_workday
                          ? d.is_absent
                            ? "Absent"
                            : "Present"
                          : "Weekend"}
                      </TableCell>
                      <TableCell>{formatMinutes(d.worked_minutes)}</TableCell>
                      <TableCell>{formatMinutes(d.late_minutes)}</TableCell>
                      <TableCell>{formatMinutes(d.early_out_minutes)}</TableCell>
                      <TableCell>{formatMinutes(d.overtime_minutes)}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
}

function Kpi({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border bg-muted/30 p-3">
      <p className="text-xs uppercase tracking-wide text-muted-foreground">{label}</p>
      <p className="mt-1 text-lg font-semibold">{value}</p>
    </div>
  );
}
