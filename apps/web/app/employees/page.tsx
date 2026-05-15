"use client";

import { MoreHorizontal, Plus, Upload, Users } from "lucide-react";
import NextLink from "next/link";
import { useCallback, useEffect, useState } from "react";
import { toast } from "sonner";

import { KpiCards } from "@/components/kpi-cards";
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
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
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
import {
  api,
  type Department,
  type EmployeeImportResult,
} from "@/lib/api";
import type { Device, Employee, EmployeeSyncEntry } from "@tikko/shared-types";

const STATUS_VARIANT: Record<Employee["status"], "default" | "secondary" | "destructive"> = {
  active: "default",
  inactive: "secondary",
  terminated: "destructive",
};

export default function EmployeesPage() {
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [devices, setDevices] = useState<Device[]>([]);
  const [departments, setDepartments] = useState<Department[]>([]);
  const [loading, setLoading] = useState(true);

  const [addOpen, setAddOpen] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [code, setCode] = useState("");
  const [name, setName] = useState("");
  const [addDepartmentId, setAddDepartmentId] = useState<string>("");

  const [syncTarget, setSyncTarget] = useState<Employee | null>(null);
  const [selectedDevices, setSelectedDevices] = useState<Record<string, boolean>>({});
  const [syncing, setSyncing] = useState(false);

  // Edit dialog
  const [editTarget, setEditTarget] = useState<Employee | null>(null);
  const [editName, setEditName] = useState("");
  const [editStatus, setEditStatus] = useState<Employee["status"]>("active");
  const [editDepartmentId, setEditDepartmentId] = useState<string>("");
  const [editSubmitting, setEditSubmitting] = useState(false);

  // Delete confirm dialog
  const [deleteTarget, setDeleteTarget] = useState<Employee | null>(null);
  const [deleteSubmitting, setDeleteSubmitting] = useState(false);

  // Manual punch
  const [punchTarget, setPunchTarget] = useState<Employee | null>(null);
  const [punchDateTime, setPunchDateTime] = useState("");
  const [punchNote, setPunchNote] = useState("");
  const [punchSubmitting, setPunchSubmitting] = useState(false);

  // Bulk CSV import
  const [importOpen, setImportOpen] = useState(false);
  const [importFile, setImportFile] = useState<File | null>(null);
  const [importSubmitting, setImportSubmitting] = useState(false);
  const [importResult, setImportResult] = useState<EmployeeImportResult | null>(
    null,
  );

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      const [{ items: emps }, { items: devs }, depts] = await Promise.all([
        api.listEmployees(),
        api.listDevices(),
        // Best-effort: managers without view_departments still get the page.
        api
          .listDepartments()
          .then((r) => r.items)
          .catch(() => [] as Department[]),
      ]);
      setEmployees(emps);
      setDevices(devs);
      setDepartments(depts);
    } catch (err) {
      toast.error("Failed to load employees", {
        description: err instanceof Error ? err.message : String(err),
      });
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const onAdd = async (event: React.FormEvent) => {
    event.preventDefault();
    setSubmitting(true);
    try {
      await api.createEmployee({
        employee_code: code,
        full_name: name,
        department_id: addDepartmentId === "" ? null : addDepartmentId,
      });
      toast.success(`Added ${name}`);
      setCode("");
      setName("");
      setAddDepartmentId("");
      setAddOpen(false);
      await refresh();
    } catch (err) {
      toast.error("Could not add employee", {
        description: err instanceof Error ? err.message : String(err),
      });
    } finally {
      setSubmitting(false);
    }
  };

  const openEdit = (employee: Employee) => {
    setEditTarget(employee);
    setEditName(employee.full_name);
    setEditStatus(employee.status);
    setEditDepartmentId(employee.department_id ?? "");
  };
  const closeEdit = () => setEditTarget(null);

  const onEditSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!editTarget) return;
    setEditSubmitting(true);
    try {
      await api.updateEmployee(editTarget.id, {
        full_name: editName,
        status: editStatus,
        department_id: editDepartmentId === "" ? null : editDepartmentId,
      });
      toast.success(`Updated ${editName}`);
      closeEdit();
      await refresh();
    } catch (err) {
      toast.error("Could not update employee", {
        description: err instanceof Error ? err.message : String(err),
      });
    } finally {
      setEditSubmitting(false);
    }
  };

  const deptName = (id: string | null | undefined): string => {
    if (!id) return "—";
    return departments.find((d) => d.id === id)?.name ?? "—";
  };

  const openPunch = (employee: Employee) => {
    setPunchTarget(employee);
    // Default to "now" local-time, formatted for <input type="datetime-local">.
    const now = new Date();
    const pad = (n: number) => String(n).padStart(2, "0");
    setPunchDateTime(
      `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}T${pad(
        now.getHours(),
      )}:${pad(now.getMinutes())}`,
    );
    setPunchNote("");
  };
  const closePunch = () => setPunchTarget(null);

  const onPunchSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!punchTarget) return;
    setPunchSubmitting(true);
    try {
      // datetime-local gives a tz-naive local string; convert to ISO UTC.
      const punchedAt = new Date(punchDateTime).toISOString();
      await api.createManualPunch({
        employee_id: punchTarget.id,
        punched_at: punchedAt,
        note: punchNote.trim() || null,
      });
      toast.success(`Added punch for ${punchTarget.full_name}`);
      closePunch();
    } catch (err) {
      toast.error("Could not add manual punch", {
        description: err instanceof Error ? err.message : String(err),
      });
    } finally {
      setPunchSubmitting(false);
    }
  };

  const openImport = () => {
    setImportFile(null);
    setImportResult(null);
    setImportOpen(true);
  };

  const closeImport = () => {
    setImportOpen(false);
    setImportFile(null);
    setImportResult(null);
  };

  const onImportSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!importFile) return;
    setImportSubmitting(true);
    try {
      const result = await api.importEmployees(importFile);
      setImportResult(result);
      toast.success(
        `Imported ${result.created} of ${result.created + result.skipped + result.failed} rows`,
      );
      await refresh();
    } catch (err) {
      toast.error("Import failed", {
        description: err instanceof Error ? err.message : String(err),
      });
    } finally {
      setImportSubmitting(false);
    }
  };

  const onConfirmDelete = async () => {
    if (!deleteTarget) return;
    setDeleteSubmitting(true);
    try {
      await api.deleteEmployee(deleteTarget.id);
      toast.success(`Removed ${deleteTarget.full_name}`);
      setDeleteTarget(null);
      await refresh();
    } catch (err) {
      toast.error("Could not delete employee", {
        description: err instanceof Error ? err.message : String(err),
      });
    } finally {
      setDeleteSubmitting(false);
    }
  };

  const openSync = (employee: Employee) => {
    setSyncTarget(employee);
    setSelectedDevices(Object.fromEntries(devices.map((d) => [d.id, true])));
  };

  const closeSync = () => {
    setSyncTarget(null);
    setSelectedDevices({});
  };

  const onSync = async () => {
    if (!syncTarget) return;
    const deviceIds = Object.entries(selectedDevices)
      .filter(([, on]) => on)
      .map(([id]) => id);
    if (deviceIds.length === 0) {
      toast.error("Pick at least one device to sync to.");
      return;
    }
    setSyncing(true);
    try {
      const { results } = await api.syncEmployee(syncTarget.id, deviceIds);
      summarizeSync(results, devices);
      closeSync();
    } catch (err) {
      toast.error("Sync failed", {
        description: err instanceof Error ? err.message : String(err),
      });
    } finally {
      setSyncing(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Employees</h1>
        <p className="text-sm text-muted-foreground">
          Enroll people on the system, then push them to one or more terminals.
        </p>
      </div>

      <KpiCards />

      <Card>
        <CardHeader className="flex flex-row items-center justify-between gap-2 space-y-0">
          <div>
            <CardTitle>All employees</CardTitle>
            <CardDescription>
              People who can punch in on a registered terminal.
            </CardDescription>
          </div>
          <div className="flex items-center gap-2">
            <Button variant="outline" onClick={openImport}>
              <Upload className="mr-1 h-4 w-4" /> Import CSV
            </Button>
          <Dialog open={addOpen} onOpenChange={setAddOpen}>
            <DialogTrigger asChild>
              <Button>
                <Plus className="mr-1 h-4 w-4" /> Add employee
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Add employee</DialogTitle>
                <DialogDescription>
                  Employee code must be digits only — it becomes the user id on the terminal.
                </DialogDescription>
              </DialogHeader>
              <form onSubmit={onAdd} className="grid gap-4">
                <div className="grid gap-2">
                  <Label htmlFor="employee_code">Employee code</Label>
                  <Input
                    id="employee_code"
                    inputMode="numeric"
                    pattern="\d+"
                    placeholder="1042"
                    value={code}
                    onChange={(e) => setCode(e.target.value)}
                    required
                  />
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="full_name">Full name</Label>
                  <Input
                    id="full_name"
                    placeholder="Ada Lovelace"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    required
                  />
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="add_department">Department</Label>
                  <select
                    id="add_department"
                    aria-label="department"
                    value={addDepartmentId}
                    onChange={(e) => setAddDepartmentId(e.target.value)}
                    className="h-10 rounded-md border bg-background px-3 text-sm"
                  >
                    <option value="">— none —</option>
                    {departments.map((d) => (
                      <option key={d.id} value={d.id}>
                        {d.name}
                      </option>
                    ))}
                  </select>
                </div>
                <DialogFooter>
                  <Button type="submit" disabled={submitting}>
                    {submitting ? "Adding…" : "Add employee"}
                  </Button>
                </DialogFooter>
              </form>
            </DialogContent>
          </Dialog>
          </div>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="space-y-2">
              <Skeleton className="h-10 w-full" />
              <Skeleton className="h-10 w-full" />
              <Skeleton className="h-10 w-full" />
            </div>
          ) : employees.length === 0 ? (
            <div className="grid place-items-center gap-2 py-12 text-center">
              <Users className="h-10 w-10 text-muted-foreground" />
              <h3 className="text-base font-semibold">No employees yet</h3>
              <p className="max-w-sm text-sm text-muted-foreground">
                Add your first employee to start enrolling fingerprints on the terminals.
              </p>
              <Button className="mt-2" onClick={() => setAddOpen(true)}>
                <Plus className="mr-1 h-4 w-4" /> Add employee
              </Button>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Name</TableHead>
                  <TableHead>Code</TableHead>
                  <TableHead>Department</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="w-[80px]"></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {employees.map((e) => (
                  <TableRow key={e.id}>
                    <TableCell className="font-medium">{e.full_name}</TableCell>
                    <TableCell className="font-mono text-xs">{e.employee_code}</TableCell>
                    <TableCell className="text-xs text-muted-foreground">
                      {deptName(e.department_id)}
                    </TableCell>
                    <TableCell>
                      <Badge variant={STATUS_VARIANT[e.status]}>{e.status}</Badge>
                    </TableCell>
                    <TableCell>
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button
                            variant="ghost"
                            size="icon"
                            className="h-8 w-8"
                            aria-label="Open menu"
                          >
                            <MoreHorizontal className="h-4 w-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuItem onClick={() => openEdit(e)}>
                            Edit
                          </DropdownMenuItem>
                          <DropdownMenuItem onClick={() => openSync(e)}>
                            Sync to devices…
                          </DropdownMenuItem>
                          <DropdownMenuItem onClick={() => openPunch(e)}>
                            Add manual punch…
                          </DropdownMenuItem>
                          <DropdownMenuItem asChild>
                            <NextLink href={`/employees/${e.id}/templates`}>
                              Manage templates…
                            </NextLink>
                          </DropdownMenuItem>
                          <DropdownMenuItem
                            onClick={() => setDeleteTarget(e)}
                            className="text-destructive focus:text-destructive"
                          >
                            Delete
                          </DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      <Dialog open={syncTarget !== null} onOpenChange={(open) => !open && closeSync()}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>
              Sync {syncTarget?.full_name ?? ""} to devices
            </DialogTitle>
            <DialogDescription>
              Push this employee&apos;s user record to the selected terminals.
            </DialogDescription>
          </DialogHeader>
          {devices.length === 0 ? (
            <p className="text-sm text-muted-foreground">
              No devices registered yet — add one on the Devices page first.
            </p>
          ) : (
            <div className="grid gap-2">
              {devices.map((d) => (
                <label key={d.id} className="flex items-center gap-2 text-sm">
                  <Checkbox
                    id={`device-${d.id}`}
                    checked={!!selectedDevices[d.id]}
                    onCheckedChange={(checked) =>
                      setSelectedDevices((prev) => ({
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
          )}
          <DialogFooter>
            <Button variant="outline" onClick={closeSync}>
              Cancel
            </Button>
            <Button onClick={onSync} disabled={syncing || devices.length === 0}>
              {syncing ? "Syncing…" : "Sync"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={editTarget !== null} onOpenChange={(open) => !open && closeEdit()}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Edit employee</DialogTitle>
            <DialogDescription>
              Employee code is permanent; change name or status.
            </DialogDescription>
          </DialogHeader>
          <form onSubmit={onEditSubmit} className="grid gap-4">
            <div className="grid gap-2">
              <Label htmlFor="edit_full_name">Full name</Label>
              <Input
                id="edit_full_name"
                value={editName}
                onChange={(e) => setEditName(e.target.value)}
                required
              />
            </div>
            <div className="grid gap-2">
              <Label htmlFor="edit_status">Status</Label>
              <select
                id="edit_status"
                value={editStatus}
                onChange={(e) => setEditStatus(e.target.value as Employee["status"])}
                className="h-10 rounded-md border bg-background px-3 text-sm"
              >
                <option value="active">active</option>
                <option value="inactive">inactive</option>
                <option value="terminated">terminated</option>
              </select>
            </div>
            <div className="grid gap-2">
              <Label htmlFor="edit_department">Department</Label>
              <select
                id="edit_department"
                aria-label="department"
                value={editDepartmentId}
                onChange={(e) => setEditDepartmentId(e.target.value)}
                className="h-10 rounded-md border bg-background px-3 text-sm"
              >
                <option value="">— none —</option>
                {departments.map((d) => (
                  <option key={d.id} value={d.id}>
                    {d.name}
                  </option>
                ))}
              </select>
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={closeEdit}>
                Cancel
              </Button>
              <Button type="submit" disabled={editSubmitting}>
                {editSubmitting ? "Saving…" : "Save changes"}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      <Dialog
        open={deleteTarget !== null}
        onOpenChange={(open) => !open && setDeleteTarget(null)}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete employee?</DialogTitle>
            <DialogDescription>
              This removes {deleteTarget?.full_name ?? "the employee"} (#
              {deleteTarget?.employee_code ?? "?"}) from the system. Their attendance
              history stays on the linked device(s) until you clear it there.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDeleteTarget(null)}>
              Cancel
            </Button>
            <Button
              variant="destructive"
              onClick={onConfirmDelete}
              disabled={deleteSubmitting}
            >
              {deleteSubmitting ? "Deleting…" : "Delete"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={punchTarget !== null} onOpenChange={(open) => !open && closePunch()}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>
              Manual punch for {punchTarget?.full_name ?? ""}
            </DialogTitle>
            <DialogDescription>
              Use this to fix a missed clock-in / clock-out. The row is stored
              with source=manual and a null device_id so reports can tell it
              apart from real terminal traffic.
            </DialogDescription>
          </DialogHeader>
          <form onSubmit={onPunchSubmit} className="grid gap-4">
            <div className="grid gap-2">
              <Label htmlFor="punch_datetime">Punched at</Label>
              <Input
                id="punch_datetime"
                type="datetime-local"
                value={punchDateTime}
                onChange={(e) => setPunchDateTime(e.target.value)}
                required
              />
            </div>
            <div className="grid gap-2">
              <Label htmlFor="punch_note">Reason (optional)</Label>
              <Input
                id="punch_note"
                value={punchNote}
                onChange={(e) => setPunchNote(e.target.value)}
                placeholder="e.g. terminal was offline at 8:30am"
              />
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={closePunch}>
                Cancel
              </Button>
              <Button type="submit" disabled={punchSubmitting || !punchDateTime}>
                {punchSubmitting ? "Saving…" : "Save punch"}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      <Dialog open={importOpen} onOpenChange={(open) => !open && closeImport()}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Import employees from CSV</DialogTitle>
            <DialogDescription>
              Required columns: <code>employee_code</code>, <code>full_name</code>.
              Optional: <code>status</code> (active / inactive / terminated),
              <code> department_id</code> or <code>department_name</code>. Existing{" "}
              <code>employee_code</code> values are skipped.
            </DialogDescription>
          </DialogHeader>

          {importResult === null ? (
            <form onSubmit={onImportSubmit} className="grid gap-4">
              <div className="grid gap-2">
                <Label htmlFor="import_file">CSV file</Label>
                <Input
                  id="import_file"
                  type="file"
                  accept=".csv,text/csv"
                  onChange={(e) => setImportFile(e.target.files?.[0] ?? null)}
                  required
                />
              </div>
              <DialogFooter>
                <Button type="button" variant="outline" onClick={closeImport}>
                  Cancel
                </Button>
                <Button type="submit" disabled={importSubmitting || !importFile}>
                  {importSubmitting ? "Importing…" : "Import"}
                </Button>
              </DialogFooter>
            </form>
          ) : (
            <div className="space-y-4">
              <div className="grid grid-cols-3 gap-3 text-sm">
                <div className="rounded-md border p-3">
                  <div className="text-xs uppercase text-muted-foreground">Created</div>
                  <div className="text-2xl font-semibold">{importResult.created}</div>
                </div>
                <div className="rounded-md border p-3">
                  <div className="text-xs uppercase text-muted-foreground">Skipped</div>
                  <div className="text-2xl font-semibold">{importResult.skipped}</div>
                </div>
                <div className="rounded-md border p-3">
                  <div className="text-xs uppercase text-muted-foreground">Failed</div>
                  <div className="text-2xl font-semibold text-destructive">
                    {importResult.failed}
                  </div>
                </div>
              </div>
              {importResult.rows.some((r) => r.status !== "created") && (
                <div className="max-h-[260px] overflow-auto rounded-md border">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead className="w-[60px]">Row</TableHead>
                        <TableHead className="w-[100px]">Code</TableHead>
                        <TableHead className="w-[100px]">Status</TableHead>
                        <TableHead>Detail</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {importResult.rows
                        .filter((r) => r.status !== "created")
                        .map((r) => (
                          <TableRow key={r.row}>
                            <TableCell className="font-mono text-xs">{r.row}</TableCell>
                            <TableCell className="font-mono text-xs">
                              {r.employee_code ?? "—"}
                            </TableCell>
                            <TableCell>
                              <Badge
                                variant={
                                  r.status === "failed" ? "destructive" : "secondary"
                                }
                              >
                                {r.status}
                              </Badge>
                            </TableCell>
                            <TableCell className="text-xs text-muted-foreground">
                              {r.error ?? "—"}
                            </TableCell>
                          </TableRow>
                        ))}
                    </TableBody>
                  </Table>
                </div>
              )}
              <DialogFooter>
                <Button onClick={closeImport}>Done</Button>
              </DialogFooter>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}

function summarizeSync(results: EmployeeSyncEntry[], devices: Device[]): void {
  const synced = results.filter((r) => r.status === "synced");
  const failed = results.filter((r) => r.status === "failed");
  const byId = new Map(devices.map((d) => [d.id, d.name]));

  if (failed.length === 0) {
    toast.success(`Synced to ${synced.length} device${synced.length === 1 ? "" : "s"}`);
    return;
  }

  const failNames = failed
    .map((r) => `${byId.get(r.device_id) ?? r.device_id}: ${r.error ?? "failed"}`)
    .join("; ");
  toast.error(
    `Synced ${synced.length} / ${results.length}; ${failed.length} failed`,
    { description: failNames },
  );
}
