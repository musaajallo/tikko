"use client";

import { ShieldCheck } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { toast } from "sonner";

import { Checkbox } from "@/components/ui/checkbox";
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
import { api, type PermissionsMatrixResponse, type UserRole } from "@/lib/api";

// Human-readable copy for each known capability. Kept here (frontend) because
// the backend deliberately uses machine-friendly slugs as the source of truth.
// Missing keys fall back to the slug itself.
const CAPABILITY_LABELS: Record<string, string> = {
  view_devices: "View devices + attendance",
  manage_devices: "Add / edit / delete devices",
  poll_devices: "Poll device attendance",
  view_employees: "View employees + templates",
  manage_employees: "Add / edit / delete employees",
  sync_employees: "Sync employees to devices",
  manage_employee_templates: "Pull / push fingerprint templates",
  view_team_leave: "View team leave requests",
  decide_leave: "Approve / reject leave requests",
  view_shift_rules: "View shift rules",
  manage_shift_rules: "Create / edit / delete shift rules",
  view_reports: "View attendance reports",
  export_reports: "Download CSV / XLSX reports",
  manage_users: "List users + change roles",
  manage_permissions: "Edit this matrix",
};

function labelFor(cap: string): string {
  return CAPABILITY_LABELS[cap] ?? cap;
}

export function PermissionsMatrix() {
  const [data, setData] = useState<PermissionsMatrixResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [pending, setPending] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      const result = await api.getPermissions();
      setData(result);
    } catch (err) {
      toast.error("Failed to load permissions", {
        description: err instanceof Error ? err.message : String(err),
      });
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const toggle = async (role: UserRole, capability: string, granted: boolean) => {
    const key = `${role}:${capability}`;
    setPending(key);
    // Optimistic update so the cell flips immediately; revert on error.
    setData((prev) => {
      if (!prev) return prev;
      const next = { ...prev, matrix: { ...prev.matrix } };
      const caps = new Set(next.matrix[role] ?? []);
      if (granted) caps.add(capability);
      else caps.delete(capability);
      next.matrix[role] = Array.from(caps);
      return next;
    });
    try {
      await api.patchPermission(role, capability, granted);
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      toast.error("Could not change permission", {
        description: /409/.test(message)
          ? "That would leave no role able to edit the matrix."
          : message,
      });
      await refresh();
    } finally {
      setPending(null);
    }
  };

  return (
    <Card>
      <CardHeader className="flex flex-row items-center gap-3 space-y-0">
        <span className="grid h-9 w-9 place-items-center rounded-md bg-muted text-muted-foreground">
          <ShieldCheck className="h-5 w-5" />
        </span>
        <div>
          <CardTitle>Roles &amp; permissions</CardTitle>
          <CardDescription>
            Toggle a cell to grant or revoke a capability. Enforced server-side;
            the UI also hides disallowed nav items.
          </CardDescription>
        </div>
      </CardHeader>
      <CardContent>
        {loading || !data || !data.all_capabilities ? (
          <div className="space-y-2">
            <Skeleton className="h-10 w-full" />
            <Skeleton className="h-10 w-full" />
            <Skeleton className="h-10 w-full" />
          </div>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Capability</TableHead>
                {data.all_roles.map((r) => (
                  <TableHead key={r} className="w-[100px] text-center capitalize">
                    {r}
                  </TableHead>
                ))}
              </TableRow>
            </TableHeader>
            <TableBody>
              {data.all_capabilities.map((cap) => (
                <TableRow key={cap}>
                  <TableCell>
                    <div className="font-medium">{labelFor(cap)}</div>
                    <div className="font-mono text-xs text-muted-foreground">{cap}</div>
                  </TableCell>
                  {data.all_roles.map((role) => {
                    const granted = (data.matrix[role] ?? []).includes(cap);
                    const key = `${role}:${cap}`;
                    return (
                      <TableCell key={role} className="text-center">
                        <Checkbox
                          aria-label={`${cap} for ${role}`}
                          checked={granted}
                          disabled={pending === key}
                          onCheckedChange={(checked) =>
                            void toggle(role, cap, checked === true)
                          }
                        />
                      </TableCell>
                    );
                  })}
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </CardContent>
    </Card>
  );
}
