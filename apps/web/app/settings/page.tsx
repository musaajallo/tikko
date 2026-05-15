"use client";

import { Clock, Pencil, Plus, Trash2, Users2 } from "lucide-react";
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

  useEffect(() => {
    void refreshUsers();
    void refreshRules();
  }, [refreshUsers, refreshRules]);

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

      <PermissionsMatrix />
    </div>
  );
}
