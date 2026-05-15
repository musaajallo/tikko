"use client";

import {
  BookOpen,
  Building2,
  Clock,
  FileBarChart,
  Fingerprint,
  Key,
  Plane,
  ShieldCheck,
  Users2,
  Zap,
} from "lucide-react";
import Link from "next/link";

import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

const TOC: { id: string; label: string }[] = [
  { id: "quickstart", label: "Quick start" },
  { id: "devices", label: "Devices" },
  { id: "employees", label: "Employees & enrollment" },
  { id: "templates", label: "Fingerprint templates" },
  { id: "shifts", label: "Shift rules" },
  { id: "leave", label: "Leave requests" },
  { id: "reports", label: "Reports" },
  { id: "rbac", label: "Roles & permissions" },
  { id: "2fa", label: "Two-factor authentication" },
  { id: "api", label: "API reference" },
  { id: "deploy", label: "Deployment" },
];

function Section({
  id,
  title,
  icon: Icon,
  children,
}: {
  id: string;
  title: string;
  icon: React.ComponentType<{ className?: string }>;
  children: React.ReactNode;
}) {
  return (
    <section id={id} className="scroll-mt-20">
      <Card>
        <CardHeader className="flex flex-row items-center gap-3 space-y-0">
          <span className="grid h-9 w-9 place-items-center rounded-md bg-muted text-muted-foreground">
            <Icon className="h-5 w-5" />
          </span>
          <CardTitle>{title}</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3 text-sm leading-relaxed text-muted-foreground">
          {children}
        </CardContent>
      </Card>
    </section>
  );
}

export default function DocumentationPage() {
  return (
    <div className="grid gap-6 lg:grid-cols-[200px_1fr]">
      <aside className="hidden lg:block">
        <nav className="sticky top-20 space-y-1 text-sm">
          {TOC.map((item) => (
            <a
              key={item.id}
              href={`#${item.id}`}
              className="block rounded-md px-2 py-1 text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
            >
              {item.label}
            </a>
          ))}
        </nav>
      </aside>

      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Documentation</h1>
          <p className="text-sm text-muted-foreground">
            Operator and admin guides for tikko. Every feature on this page is
            already shipped — links below jump to the relevant screen.
          </p>
        </div>

        <Section id="quickstart" title="Quick start" icon={Zap}>
          <ol className="ml-5 list-decimal space-y-1">
            <li>Sign in as an admin (default seed user: <code>admin@example.com</code>).</li>
            <li>Open <Link href="/devices" className="text-primary underline">Devices</Link> and add a terminal. Click <em>Test connection</em> to verify it answers on TCP/4370.</li>
            <li>Click <em>Poll now</em>; punches are stored, deduped, and broadcast over <code>/ws/attendance</code> in real time.</li>
            <li>Add a shift rule under <Link href="/settings" className="text-primary underline">Settings → Shift rules</Link>, then create an Employee and assign the rule on the row.</li>
            <li>Pull templates from the source terminal under <em>Manage templates</em>, then push to other terminals.</li>
          </ol>
        </Section>

        <Section id="devices" title="Devices" icon={Building2}>
          <p>
            Devices are ZKTeco terminals. Each row stores <code>host</code> + <code>port</code>{" "}
            (default 4370). Polling pulls attendance over pyzk; push-firmware devices
            can also POST to the ADMS receiver at <code>/iclock/cdata</code>.
          </p>
          <p>
            The per-device <em>Poll interval</em> field (in seconds) drives the
            background scheduler. Leave null to skip the device from the polling
            loop.
          </p>
        </Section>

        <Section id="employees" title="Employees & enrollment" icon={Users2}>
          <p>
            <code>employee_code</code> is a digits-only string that doubles as the
            ZK terminal user id. Add an employee, then click <em>Sync to devices</em>{" "}
            to write the name onto one or more terminals.
          </p>
          <p>
            Linking a User to an Employee at registration: include{" "}
            <code>employee_code</code> in the <code>/auth/register</code> body. The
            user&apos;s <code>/me/attendance</code> and <code>/me/leave-requests</code>{" "}
            then scope to that employee.
          </p>
        </Section>

        <Section id="templates" title="Fingerprint templates" icon={Fingerprint}>
          <p>
            Open an employee&apos;s <em>Manage templates</em> dialog. Choose a source
            device and click <em>Pull</em>; tikko stores each enrolled finger&apos;s
            template, keyed by source device so cross-firmware compatibility stays
            traceable. <em>Push</em> writes the latest-per-finger templates to a
            selected set of target devices.
          </p>
        </Section>

        <Section id="shifts" title="Shift rules" icon={Clock}>
          <p>
            A shift rule defines a daily schedule:{" "}
            <code>start_time</code>, <code>end_time</code>, late/early-out grace
            minutes, overtime threshold, and a 7-character <code>work_days</code>{" "}
            mask (Mon to Sun, &quot;1111100&quot; = Mon-Fri).
          </p>
          <p>
            Assign a rule to an employee via the row Edit dialog. The payroll
            engine then computes <em>late</em>, <em>early-out</em>, and{" "}
            <em>overtime</em> minutes per day from their attendance.
          </p>
        </Section>

        <Section id="leave" title="Leave requests" icon={Plane}>
          <p>
            Employees with a linked User submit via mobile (under the dashboard)
            or <code>POST /me/leave-requests</code>. Managers/admins see the queue
            at <Link href="/leave-requests" className="text-primary underline">Leave</Link>{" "}
            (web) or the Approvals screen (mobile).
          </p>
          <p>
            A decision is final — re-PATCHing returns 409. Submitter and approver
            both receive email notifications via Resend when the api key is
            configured.
          </p>
        </Section>

        <Section id="reports" title="Reports" icon={FileBarChart}>
          <p>
            Open <Link href="/reports" className="text-primary underline">Reports</Link>,
            pick an employee + month, and run. The result shows daily breakdown +
            monthly totals. Use the <em>CSV</em> or <em>XLSX</em> buttons to
            download.
          </p>
          <p>
            The employee must have a shift rule assigned, otherwise the run
            returns 422 with a hint.
          </p>
        </Section>

        <Section id="rbac" title="Roles & permissions" icon={ShieldCheck}>
          <p>
            Three roles: <code>admin</code>, <code>manager</code>,{" "}
            <code>employee</code>. Each role has a set of capabilities stored in{" "}
            <code>role_permissions</code>. Edit the matrix at{" "}
            <Link href="/settings" className="text-primary underline">Settings → Roles &amp; permissions</Link>.
          </p>
          <p>
            Changes take effect on the next request — toggle a capability for a
            role and that role&apos;s next <code>/auth/me</code> reflects the new
            grants. The UI hides nav items the user can&apos;t access; the api
            enforces the same gate server-side.
          </p>
        </Section>

        <Section id="2fa" title="Two-factor authentication" icon={Key}>
          <p>
            Open <Link href="/profile" className="text-primary underline">Profile → Two-factor</Link>{" "}
            and click <em>Enable</em>. Scan the QR with any TOTP authenticator
            (Google Authenticator, Authy, 1Password, …) and confirm the 6-digit
            code. tikko returns 10 single-use recovery codes — save them.
          </p>
          <p>
            Admin accounts with TOTP enabled must supply a code on every login;
            recovery codes work as the second factor too (single-use). Disable
            requires re-entering the password.
          </p>
        </Section>

        <Section id="api" title="API reference" icon={BookOpen}>
          <p>
            FastAPI ships a full OpenAPI schema. With the api running on{" "}
            <code>:8001</code>:
          </p>
          <ul className="ml-5 list-disc space-y-1">
            <li>
              Swagger UI:{" "}
              <a
                className="text-primary underline"
                href="http://localhost:8001/docs"
                target="_blank"
                rel="noreferrer"
              >
                http://localhost:8001/docs
              </a>
            </li>
            <li>
              ReDoc:{" "}
              <a
                className="text-primary underline"
                href="http://localhost:8001/redoc"
                target="_blank"
                rel="noreferrer"
              >
                http://localhost:8001/redoc
              </a>
            </li>
            <li>
              Raw schema:{" "}
              <a
                className="text-primary underline"
                href="http://localhost:8001/openapi.json"
                target="_blank"
                rel="noreferrer"
              >
                /openapi.json
              </a>
            </li>
          </ul>
        </Section>

        <Section id="deploy" title="Deployment" icon={Building2}>
          <p>
            Two supported modes via <code>TIKKO_DEPLOY_MODE</code>:
          </p>
          <ul className="ml-5 list-disc space-y-1">
            <li>
              <strong>lan</strong> — single host on an office network. Use{" "}
              <code>docker-compose.lan.yml</code>; api binds to all interfaces so
              devices can reach the ADMS receiver.
            </li>
            <li>
              <strong>cloud</strong> — VPS with TLS and public DNS. Use the systemd
              units under <code>deploy/systemd/</code> behind a reverse proxy.
              Startup validates that <code>TIKKO_JWT_SECRET</code> isn&apos;t the
              default, the database isn&apos;t SQLite, and CORS origins are
              explicit — boots fail-fast otherwise.
            </li>
          </ul>
        </Section>
      </div>
    </div>
  );
}
