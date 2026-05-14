"use client";

import { MoreHorizontal, Plus, Users } from "lucide-react";
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
import { api } from "@/lib/api";
import type { Device, Employee, EmployeeSyncEntry } from "@tikko/shared-types";

const STATUS_VARIANT: Record<Employee["status"], "default" | "secondary" | "destructive"> = {
  active: "default",
  inactive: "secondary",
  terminated: "destructive",
};

export default function EmployeesPage() {
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [devices, setDevices] = useState<Device[]>([]);
  const [loading, setLoading] = useState(true);

  const [addOpen, setAddOpen] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [code, setCode] = useState("");
  const [name, setName] = useState("");

  const [syncTarget, setSyncTarget] = useState<Employee | null>(null);
  const [selectedDevices, setSelectedDevices] = useState<Record<string, boolean>>({});
  const [syncing, setSyncing] = useState(false);

  // Edit dialog
  const [editTarget, setEditTarget] = useState<Employee | null>(null);
  const [editName, setEditName] = useState("");
  const [editStatus, setEditStatus] = useState<Employee["status"]>("active");
  const [editSubmitting, setEditSubmitting] = useState(false);

  // Delete confirm dialog
  const [deleteTarget, setDeleteTarget] = useState<Employee | null>(null);
  const [deleteSubmitting, setDeleteSubmitting] = useState(false);

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      const [{ items: emps }, { items: devs }] = await Promise.all([
        api.listEmployees(),
        api.listDevices(),
      ]);
      setEmployees(emps);
      setDevices(devs);
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
      await api.createEmployee({ employee_code: code, full_name: name });
      toast.success(`Added ${name}`);
      setCode("");
      setName("");
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
                <DialogFooter>
                  <Button type="submit" disabled={submitting}>
                    {submitting ? "Adding…" : "Add employee"}
                  </Button>
                </DialogFooter>
              </form>
            </DialogContent>
          </Dialog>
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
                  <TableHead>Status</TableHead>
                  <TableHead className="w-[80px]"></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {employees.map((e) => (
                  <TableRow key={e.id}>
                    <TableCell className="font-medium">{e.full_name}</TableCell>
                    <TableCell className="font-mono text-xs">{e.employee_code}</TableCell>
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
