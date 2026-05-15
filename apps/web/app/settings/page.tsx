"use client";

import {
  Building2,
  CalendarDays,
  Clock,
  Pencil,
  Plus,
  Trash2,
  Users2,
} from "lucide-react";
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
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
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
import { PermissionsMatrix } from "@/components/permissions-matrix";
import {
  api,
  type Department,
  type Holiday,
  type ShiftRule,
  type ShiftRuleCreate,
  type UserListItem,
  type UserRole,
} from "@/lib/api";

const ROLES: UserRole[] = ["admin", "manager", "employee"];

const WORK_DAY_LABELS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];

function workDaysToLabel(workDays: string): string {
  return workDays
    .split("")
    .map((bit, i) => (bit === "1" ? WORK_DAY_LABELS[i] : null))
    .filter(Boolean)
    .join(", ") || "None";
}

function emptyRuleForm(): ShiftRuleCreate {
  return {
    name: "",
    start_time: "09:00:00",
    end_time: "17:00:00",
    late_grace_minutes: 0,
    early_out_grace_minutes: 0,
    overtime_threshold_minutes: 30,
    work_days: "1111100",
  };
}

export default function SettingsPage() {
  // Users
  const [users, setUsers] = useState<UserListItem[]>([]);
  const [usersLoading, setUsersLoading] = useState(true);
  const [pendingRoleId, setPendingRoleId] = useState<string | null>(null);

  // Holidays
  const [holidays, setHolidays] = useState<Holiday[]>([]);
  const [holidaysLoading, setHolidaysLoading] = useState(true);
  const [holidayDialog, setHolidayDialog] = useState<{
    mode: "add" | "edit";
    holiday: Holiday | null;
  } | null>(null);
  const [holidayForm, setHolidayForm] = useState<{ date: string; name: string }>({
    date: "",
    name: "",
  });
  const [holidaySubmitting, setHolidaySubmitting] = useState(false);

  // Departments
  const [departments, setDepartments] = useState<Department[]>([]);
  const [departmentsLoading, setDepartmentsLoading] = useState(true);
  const [deptDialog, setDeptDialog] = useState<{
    mode: "add" | "edit";
    dept: Department | null;
  } | null>(null);
  const [deptForm, setDeptForm] = useState<{ name: string; parent_id: string | null }>({
    name: "",
    parent_id: null,
  });
  const [deptSubmitting, setDeptSubmitting] = useState(false);

  // Shift rules
  const [rules, setRules] = useState<ShiftRule[]>([]);
  const [rulesLoading, setRulesLoading] = useState(true);
  const [ruleDialog, setRuleDialog] = useState<{
    mode: "add" | "edit";
    rule: ShiftRule | null;
  } | null>(null);
  const [ruleForm, setRuleForm] = useState<ShiftRuleCreate>(emptyRuleForm());
  const [ruleSubmitting, setRuleSubmitting] = useState(false);

  const refreshUsers = useCallback(async () => {
    setUsersLoading(true);
    try {
      const { items } = await api.listUsers();
      setUsers(items);
    } catch (err) {
      toast.error("Failed to load users", {
        description: err instanceof Error ? err.message : String(err),
      });
    } finally {
      setUsersLoading(false);
    }
  }, []);

  const refreshRules = useCallback(async () => {
    setRulesLoading(true);
    try {
      const { items } = await api.listShiftRules();
      setRules(items);
    } catch (err) {
      toast.error("Failed to load shift rules", {
        description: err instanceof Error ? err.message : String(err),
      });
    } finally {
      setRulesLoading(false);
    }
  }, []);

  const refreshDepartments = useCallback(async () => {
    setDepartmentsLoading(true);
    try {
      const { items } = await api.listDepartments();
      setDepartments(items);
    } catch (err) {
      toast.error("Failed to load departments", {
        description: err instanceof Error ? err.message : String(err),
      });
    } finally {
      setDepartmentsLoading(false);
    }
  }, []);

  const refreshHolidays = useCallback(async () => {
    setHolidaysLoading(true);
    try {
      const { items } = await api.listHolidays();
      setHolidays(items);
    } catch (err) {
      toast.error("Failed to load holidays", {
        description: err instanceof Error ? err.message : String(err),
      });
    } finally {
      setHolidaysLoading(false);
    }
  }, []);

  useEffect(() => {
    void refreshUsers();
    void refreshRules();
    void refreshDepartments();
    void refreshHolidays();
  }, [refreshUsers, refreshRules, refreshDepartments, refreshHolidays]);

  const changeRole = async (user: UserListItem, role: UserRole) => {
    if (role === user.role) return;
    setPendingRoleId(user.id);
    try {
      await api.updateUserRole(user.id, role);
      toast.success(`${user.email} is now ${role}`);
      await refreshUsers();
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      toast.error("Could not change role", {
        description: /409/.test(message)
          ? "Cannot demote the last admin."
          : message,
      });
    } finally {
      setPendingRoleId(null);
    }
  };

  const openAddRule = () => {
    setRuleForm(emptyRuleForm());
    setRuleDialog({ mode: "add", rule: null });
  };

  const openEditRule = (rule: ShiftRule) => {
    setRuleForm({
      name: rule.name,
      start_time: rule.start_time,
      end_time: rule.end_time,
      late_grace_minutes: rule.late_grace_minutes,
      early_out_grace_minutes: rule.early_out_grace_minutes,
      overtime_threshold_minutes: rule.overtime_threshold_minutes,
      work_days: rule.work_days,
    });
    setRuleDialog({ mode: "edit", rule });
  };

  const closeRuleDialog = () => setRuleDialog(null);

  const submitRule = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!ruleDialog) return;
    setRuleSubmitting(true);
    try {
      if (ruleDialog.mode === "add") {
        await api.createShiftRule(ruleForm);
        toast.success(`Added ${ruleForm.name}`);
      } else if (ruleDialog.rule) {
        await api.updateShiftRule(ruleDialog.rule.id, ruleForm);
        toast.success(`Updated ${ruleForm.name}`);
      }
      closeRuleDialog();
      await refreshRules();
    } catch (err) {
      toast.error("Could not save shift rule", {
        description: err instanceof Error ? err.message : String(err),
      });
    } finally {
      setRuleSubmitting(false);
    }
  };

  const deleteRule = async (rule: ShiftRule) => {
    try {
      await api.deleteShiftRule(rule.id);
      toast.success(`Removed ${rule.name}`);
      await refreshRules();
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      toast.error("Could not delete", {
        description: /409/.test(message)
          ? "One or more employees are still assigned to this rule."
          : message,
      });
    }
  };

  const openAddDept = () => {
    setDeptForm({ name: "", parent_id: null });
    setDeptDialog({ mode: "add", dept: null });
  };

  const openEditDept = (dept: Department) => {
    setDeptForm({ name: dept.name, parent_id: dept.parent_id });
    setDeptDialog({ mode: "edit", dept });
  };

  const closeDeptDialog = () => setDeptDialog(null);

  const submitDept = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!deptDialog) return;
    setDeptSubmitting(true);
    try {
      if (deptDialog.mode === "add") {
        await api.createDepartment({
          name: deptForm.name,
          parent_id: deptForm.parent_id,
        });
        toast.success(`Added ${deptForm.name}`);
      } else if (deptDialog.dept) {
        await api.updateDepartment(deptDialog.dept.id, {
          name: deptForm.name,
          parent_id: deptForm.parent_id,
        });
        toast.success(`Updated ${deptForm.name}`);
      }
      closeDeptDialog();
      await refreshDepartments();
    } catch (err) {
      toast.error("Could not save department", {
        description: err instanceof Error ? err.message : String(err),
      });
    } finally {
      setDeptSubmitting(false);
    }
  };

  const deleteDept = async (dept: Department) => {
    try {
      await api.deleteDepartment(dept.id);
      toast.success(`Removed ${dept.name}`);
      await refreshDepartments();
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      toast.error("Could not delete", {
        description: /409/.test(message)
          ? "Reassign affected employees or child departments first."
          : message,
      });
    }
  };

  const deptName = (id: string | null): string => {
    if (id === null) return "—";
    return departments.find((d) => d.id === id)?.name ?? "—";
  };

  const openAddHoliday = () => {
    setHolidayForm({ date: "", name: "" });
    setHolidayDialog({ mode: "add", holiday: null });
  };

  const openEditHoliday = (holiday: Holiday) => {
    setHolidayForm({ date: holiday.date, name: holiday.name });
    setHolidayDialog({ mode: "edit", holiday });
  };

  const closeHolidayDialog = () => setHolidayDialog(null);

  const submitHoliday = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!holidayDialog) return;
    setHolidaySubmitting(true);
    try {
      if (holidayDialog.mode === "add") {
        await api.createHoliday(holidayForm);
        toast.success(`Added ${holidayForm.name}`);
      } else if (holidayDialog.holiday) {
        await api.updateHoliday(holidayDialog.holiday.id, holidayForm);
        toast.success(`Updated ${holidayForm.name}`);
      }
      closeHolidayDialog();
      await refreshHolidays();
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      toast.error("Could not save holiday", {
        description: /409/.test(message)
          ? "A holiday already exists on that date."
          : message,
      });
    } finally {
      setHolidaySubmitting(false);
    }
  };

  const deleteHoliday = async (holiday: Holiday) => {
    try {
      await api.deleteHoliday(holiday.id);
      toast.success(`Removed ${holiday.name}`);
      await refreshHolidays();
    } catch (err) {
      toast.error("Could not delete", {
        description: err instanceof Error ? err.message : String(err),
      });
    }
  };

  const toggleWorkDay = (index: number) => {
    setRuleForm((prev) => {
      const chars = prev.work_days.split("");
      chars[index] = chars[index] === "1" ? "0" : "1";
      return { ...prev, work_days: chars.join("") };
    });
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Settings</h1>
        <p className="text-sm text-muted-foreground">
          Manage users, roles, and shift rules.
        </p>
      </div>

      {/* USERS SECTION */}
      <Card>
        <CardHeader className="flex flex-row items-center gap-3 space-y-0">
          <span className="grid h-9 w-9 place-items-center rounded-md bg-muted text-muted-foreground">
            <Users2 className="h-5 w-5" />
          </span>
          <div>
            <CardTitle>Users</CardTitle>
            <CardDescription>Change roles for signed-in users.</CardDescription>
          </div>
        </CardHeader>
        <CardContent>
          {usersLoading ? (
            <div className="space-y-2">
              <Skeleton className="h-10 w-full" />
              <Skeleton className="h-10 w-full" />
            </div>
          ) : users.length === 0 ? (
            <p className="text-sm text-muted-foreground">No users yet.</p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Email</TableHead>
                  <TableHead>Role</TableHead>
                  <TableHead className="w-[180px]">Change role</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {users.map((u) => (
                  <TableRow key={u.id}>
                    <TableCell className="font-medium">{u.email}</TableCell>
                    <TableCell>
                      <Badge variant="secondary">{u.role}</Badge>
                    </TableCell>
                    <TableCell>
                      <select
                        aria-label={`role for ${u.email}`}
                        value={u.role}
                        disabled={pendingRoleId === u.id}
                        onChange={(e) =>
                          void changeRole(u, e.target.value as UserRole)
                        }
                        className="h-9 rounded-md border bg-background px-3 text-sm"
                      >
                        {ROLES.map((r) => (
                          <option key={r} value={r}>
                            {r}
                          </option>
                        ))}
                      </select>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* SHIFT RULES SECTION */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between gap-2 space-y-0">
          <div className="flex items-center gap-3">
            <span className="grid h-9 w-9 place-items-center rounded-md bg-muted text-muted-foreground">
              <Clock className="h-5 w-5" />
            </span>
            <div>
              <CardTitle>Shift rules</CardTitle>
              <CardDescription>
                Per-employee schedule; drives late / early / overtime in reports.
              </CardDescription>
            </div>
          </div>
          <Dialog
            open={ruleDialog !== null}
            onOpenChange={(open) => !open && closeRuleDialog()}
          >
            <DialogTrigger asChild>
              <Button onClick={openAddRule}>
                <Plus className="mr-1 h-4 w-4" /> Add rule
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>
                  {ruleDialog?.mode === "edit" ? "Edit shift rule" : "Add shift rule"}
                </DialogTitle>
                <DialogDescription>
                  Late / early-out / overtime are computed against these values.
                </DialogDescription>
              </DialogHeader>
              <form onSubmit={submitRule} className="grid gap-4">
                <div className="grid gap-2">
                  <Label htmlFor="rule_name">Name</Label>
                  <Input
                    id="rule_name"
                    value={ruleForm.name}
                    onChange={(e) =>
                      setRuleForm({ ...ruleForm, name: e.target.value })
                    }
                    required
                  />
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div className="grid gap-2">
                    <Label htmlFor="rule_start">Start time</Label>
                    <Input
                      id="rule_start"
                      type="time"
                      step={1}
                      value={ruleForm.start_time.slice(0, 5)}
                      onChange={(e) =>
                        setRuleForm({ ...ruleForm, start_time: `${e.target.value}:00` })
                      }
                      required
                    />
                  </div>
                  <div className="grid gap-2">
                    <Label htmlFor="rule_end">End time</Label>
                    <Input
                      id="rule_end"
                      type="time"
                      step={1}
                      value={ruleForm.end_time.slice(0, 5)}
                      onChange={(e) =>
                        setRuleForm({ ...ruleForm, end_time: `${e.target.value}:00` })
                      }
                      required
                    />
                  </div>
                </div>
                <div className="grid grid-cols-3 gap-3">
                  <div className="grid gap-2">
                    <Label htmlFor="late_grace">Late grace (min)</Label>
                    <Input
                      id="late_grace"
                      type="number"
                      min={0}
                      max={240}
                      value={ruleForm.late_grace_minutes}
                      onChange={(e) =>
                        setRuleForm({
                          ...ruleForm,
                          late_grace_minutes: Number(e.target.value) || 0,
                        })
                      }
                    />
                  </div>
                  <div className="grid gap-2">
                    <Label htmlFor="early_grace">Early-out grace (min)</Label>
                    <Input
                      id="early_grace"
                      type="number"
                      min={0}
                      max={240}
                      value={ruleForm.early_out_grace_minutes}
                      onChange={(e) =>
                        setRuleForm({
                          ...ruleForm,
                          early_out_grace_minutes: Number(e.target.value) || 0,
                        })
                      }
                    />
                  </div>
                  <div className="grid gap-2">
                    <Label htmlFor="ot_threshold">OT threshold (min)</Label>
                    <Input
                      id="ot_threshold"
                      type="number"
                      min={0}
                      max={600}
                      value={ruleForm.overtime_threshold_minutes}
                      onChange={(e) =>
                        setRuleForm({
                          ...ruleForm,
                          overtime_threshold_minutes: Number(e.target.value) || 0,
                        })
                      }
                    />
                  </div>
                </div>
                <div className="grid gap-2">
                  <Label>Work days</Label>
                  <div className="flex gap-1">
                    {WORK_DAY_LABELS.map((label, i) => {
                      const on = ruleForm.work_days[i] === "1";
                      return (
                        <button
                          key={label}
                          type="button"
                          onClick={() => toggleWorkDay(i)}
                          className={
                            on
                              ? "h-9 w-12 rounded-md border bg-primary text-sm font-medium text-primary-foreground"
                              : "h-9 w-12 rounded-md border bg-background text-sm text-muted-foreground"
                          }
                        >
                          {label}
                        </button>
                      );
                    })}
                  </div>
                </div>
                <DialogFooter>
                  <Button type="button" variant="outline" onClick={closeRuleDialog}>
                    Cancel
                  </Button>
                  <Button type="submit" disabled={ruleSubmitting}>
                    {ruleSubmitting ? "Saving…" : "Save"}
                  </Button>
                </DialogFooter>
              </form>
            </DialogContent>
          </Dialog>
        </CardHeader>
        <CardContent>
          {rulesLoading ? (
            <div className="space-y-2">
              <Skeleton className="h-10 w-full" />
              <Skeleton className="h-10 w-full" />
            </div>
          ) : rules.length === 0 ? (
            <p className="text-sm text-muted-foreground">
              No shift rules yet. Add one to start computing late / early / OT in
              reports.
            </p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Name</TableHead>
                  <TableHead>Hours</TableHead>
                  <TableHead>Grace</TableHead>
                  <TableHead>OT after</TableHead>
                  <TableHead>Work days</TableHead>
                  <TableHead className="w-[120px]"></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {rules.map((r) => (
                  <TableRow key={r.id}>
                    <TableCell className="font-medium">{r.name}</TableCell>
                    <TableCell className="font-mono text-xs">
                      {r.start_time.slice(0, 5)}–{r.end_time.slice(0, 5)}
                    </TableCell>
                    <TableCell className="text-xs">
                      late {r.late_grace_minutes}m · early {r.early_out_grace_minutes}m
                    </TableCell>
                    <TableCell className="text-xs">
                      {r.overtime_threshold_minutes}m
                    </TableCell>
                    <TableCell className="text-xs">
                      {workDaysToLabel(r.work_days)}
                    </TableCell>
                    <TableCell className="text-right">
                      <Button
                        variant="ghost"
                        size="icon"
                        aria-label={`edit ${r.name}`}
                        onClick={() => openEditRule(r)}
                      >
                        <Pencil className="h-4 w-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="icon"
                        aria-label={`delete ${r.name}`}
                        onClick={() => void deleteRule(r)}
                      >
                        <Trash2 className="h-4 w-4 text-destructive" />
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* DEPARTMENTS SECTION */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between gap-2 space-y-0">
          <div className="flex items-center gap-3">
            <span className="grid h-9 w-9 place-items-center rounded-md bg-muted text-muted-foreground">
              <Building2 className="h-5 w-5" />
            </span>
            <div>
              <CardTitle>Departments</CardTitle>
              <CardDescription>
                Org hierarchy. Employees opt in via the row Edit dialog on the
                Employees page.
              </CardDescription>
            </div>
          </div>
          <Dialog
            open={deptDialog !== null}
            onOpenChange={(open) => !open && closeDeptDialog()}
          >
            <DialogTrigger asChild>
              <Button onClick={openAddDept}>
                <Plus className="mr-1 h-4 w-4" /> Add department
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>
                  {deptDialog?.mode === "edit"
                    ? "Edit department"
                    : "Add department"}
                </DialogTitle>
                <DialogDescription>
                  Parent is optional; leave blank for a top-level node.
                </DialogDescription>
              </DialogHeader>
              <form onSubmit={submitDept} className="grid gap-4">
                <div className="grid gap-2">
                  <Label htmlFor="dept_name">Name</Label>
                  <Input
                    id="dept_name"
                    value={deptForm.name}
                    onChange={(e) =>
                      setDeptForm({ ...deptForm, name: e.target.value })
                    }
                    required
                  />
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="dept_parent">Parent department</Label>
                  <select
                    id="dept_parent"
                    aria-label="parent department"
                    value={deptForm.parent_id ?? ""}
                    onChange={(e) =>
                      setDeptForm({
                        ...deptForm,
                        parent_id: e.target.value === "" ? null : e.target.value,
                      })
                    }
                    className="h-9 rounded-md border bg-background px-3 text-sm"
                  >
                    <option value="">— none —</option>
                    {departments
                      .filter((d) => d.id !== deptDialog?.dept?.id)
                      .map((d) => (
                        <option key={d.id} value={d.id}>
                          {d.name}
                        </option>
                      ))}
                  </select>
                </div>
                <DialogFooter>
                  <Button type="button" variant="outline" onClick={closeDeptDialog}>
                    Cancel
                  </Button>
                  <Button type="submit" disabled={deptSubmitting}>
                    {deptSubmitting ? "Saving…" : "Save"}
                  </Button>
                </DialogFooter>
              </form>
            </DialogContent>
          </Dialog>
        </CardHeader>
        <CardContent>
          {departmentsLoading ? (
            <div className="space-y-2">
              <Skeleton className="h-10 w-full" />
              <Skeleton className="h-10 w-full" />
            </div>
          ) : departments.length === 0 ? (
            <p className="text-sm text-muted-foreground">
              No departments yet. Add one to organise employees by team or
              location.
            </p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Name</TableHead>
                  <TableHead>Parent</TableHead>
                  <TableHead className="w-[120px]"></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {departments.map((d) => (
                  <TableRow key={d.id}>
                    <TableCell className="font-medium">{d.name}</TableCell>
                    <TableCell className="text-xs text-muted-foreground">
                      {deptName(d.parent_id)}
                    </TableCell>
                    <TableCell className="text-right">
                      <Button
                        variant="ghost"
                        size="icon"
                        aria-label={`edit ${d.name}`}
                        onClick={() => openEditDept(d)}
                      >
                        <Pencil className="h-4 w-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="icon"
                        aria-label={`delete ${d.name}`}
                        onClick={() => void deleteDept(d)}
                      >
                        <Trash2 className="h-4 w-4 text-destructive" />
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* HOLIDAYS SECTION */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between gap-2 space-y-0">
          <div className="flex items-center gap-3">
            <span className="grid h-9 w-9 place-items-center rounded-md bg-muted text-muted-foreground">
              <CalendarDays className="h-5 w-5" />
            </span>
            <div>
              <CardTitle>Holidays</CardTitle>
              <CardDescription>
                Calendar dates that skip late / early / absent in payroll
                reports. OT still applies on holidays worked.
              </CardDescription>
            </div>
          </div>
          <Dialog
            open={holidayDialog !== null}
            onOpenChange={(open) => !open && closeHolidayDialog()}
          >
            <DialogTrigger asChild>
              <Button onClick={openAddHoliday}>
                <Plus className="mr-1 h-4 w-4" /> Add holiday
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>
                  {holidayDialog?.mode === "edit" ? "Edit holiday" : "Add holiday"}
                </DialogTitle>
                <DialogDescription>
                  Each calendar date is unique. Name is for display in reports.
                </DialogDescription>
              </DialogHeader>
              <form onSubmit={submitHoliday} className="grid gap-4">
                <div className="grid gap-2">
                  <Label htmlFor="holiday_date">Date</Label>
                  <Input
                    id="holiday_date"
                    type="date"
                    value={holidayForm.date}
                    onChange={(e) =>
                      setHolidayForm({ ...holidayForm, date: e.target.value })
                    }
                    required
                  />
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="holiday_name">Name</Label>
                  <Input
                    id="holiday_name"
                    value={holidayForm.name}
                    onChange={(e) =>
                      setHolidayForm({ ...holidayForm, name: e.target.value })
                    }
                    placeholder="e.g. Christmas Day"
                    required
                  />
                </div>
                <DialogFooter>
                  <Button
                    type="button"
                    variant="outline"
                    onClick={closeHolidayDialog}
                  >
                    Cancel
                  </Button>
                  <Button type="submit" disabled={holidaySubmitting}>
                    {holidaySubmitting ? "Saving…" : "Save"}
                  </Button>
                </DialogFooter>
              </form>
            </DialogContent>
          </Dialog>
        </CardHeader>
        <CardContent>
          {holidaysLoading ? (
            <div className="space-y-2">
              <Skeleton className="h-10 w-full" />
              <Skeleton className="h-10 w-full" />
            </div>
          ) : holidays.length === 0 ? (
            <p className="text-sm text-muted-foreground">
              No holidays configured. Add one to mark a calendar day as off
              for payroll.
            </p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-[140px]">Date</TableHead>
                  <TableHead>Name</TableHead>
                  <TableHead className="w-[120px]"></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {holidays.map((h) => (
                  <TableRow key={h.id}>
                    <TableCell className="font-mono text-xs">{h.date}</TableCell>
                    <TableCell className="font-medium">{h.name}</TableCell>
                    <TableCell className="text-right">
                      <Button
                        variant="ghost"
                        size="icon"
                        aria-label={`edit ${h.name}`}
                        onClick={() => openEditHoliday(h)}
                      >
                        <Pencil className="h-4 w-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="icon"
                        aria-label={`delete ${h.name}`}
                        onClick={() => void deleteHoliday(h)}
                      >
                        <Trash2 className="h-4 w-4 text-destructive" />
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      <PermissionsMatrix />
    </div>
  );
}
