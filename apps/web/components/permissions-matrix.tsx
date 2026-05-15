import { Check, ShieldCheck, X } from "lucide-react";

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

// One row per capability; columns are the three roles.
// Source of truth: the route-level guards in the api (`require_role(...)`).
// Keep this list in sync when adding endpoints with new role gates.
const ROWS: ReadonlyArray<{
  capability: string;
  admin: boolean;
  manager: boolean;
  employee: boolean;
}> = [
  { capability: "Sign in to the web app", admin: true, manager: true, employee: true },
  { capability: "Change own password / TOTP", admin: true, manager: true, employee: true },
  { capability: "See own attendance / leave (mobile dashboard)", admin: false, manager: false, employee: true },
  { capability: "View devices + attendance logs", admin: true, manager: true, employee: false },
  { capability: "Add / edit / delete devices", admin: true, manager: false, employee: false },
  { capability: "Test device connection / poll attendance", admin: true, manager: false, employee: false },
  { capability: "View employees", admin: true, manager: true, employee: false },
  { capability: "Add / edit / delete employees", admin: true, manager: false, employee: false },
  { capability: "Sync employee + push fingerprint templates", admin: true, manager: false, employee: false },
  { capability: "View team leave requests", admin: true, manager: true, employee: false },
  { capability: "Approve / reject leave requests", admin: true, manager: true, employee: false },
  { capability: "View shift rules + reports", admin: true, manager: true, employee: false },
  { capability: "Create / edit / delete shift rules", admin: true, manager: false, employee: false },
  { capability: "Manage users (list, change role)", admin: true, manager: false, employee: false },
];

function Yes() {
  return (
    <span className="inline-flex items-center gap-1 text-emerald-600 dark:text-emerald-400">
      <Check className="h-4 w-4" />
    </span>
  );
}

function No() {
  return (
    <span className="inline-flex items-center text-muted-foreground/60">
      <X className="h-4 w-4" />
    </span>
  );
}

export function PermissionsMatrix() {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center gap-3 space-y-0">
        <span className="grid h-9 w-9 place-items-center rounded-md bg-muted text-muted-foreground">
          <ShieldCheck className="h-5 w-5" />
        </span>
        <div>
          <CardTitle>Roles &amp; permissions</CardTitle>
          <CardDescription>
            What each role can do. Enforced server-side; the UI also hides
            disallowed nav items.
          </CardDescription>
        </div>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Capability</TableHead>
              <TableHead className="w-[100px] text-center">Admin</TableHead>
              <TableHead className="w-[100px] text-center">Manager</TableHead>
              <TableHead className="w-[100px] text-center">Employee</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {ROWS.map((r) => (
              <TableRow key={r.capability}>
                <TableCell>{r.capability}</TableCell>
                <TableCell className="text-center">
                  {r.admin ? <Yes /> : <No />}
                </TableCell>
                <TableCell className="text-center">
                  {r.manager ? <Yes /> : <No />}
                </TableCell>
                <TableCell className="text-center">
                  {r.employee ? <Yes /> : <No />}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  );
}
