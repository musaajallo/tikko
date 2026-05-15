# TODO

## Session end (2026-05-14)

**F01–F32 complete on `main` — every roadmap feature shipped.** Plus a profile page, real settings page, employee leave list on mobile, web leave-requests page, web templates page, TOTP recovery codes, XLSX export, Remember-me persistence, edit-employee dialog, delete-confirm dialog.
- **api 218/218** · **web 33/33** · **shared-types 11/11** · **mobile 15/15** = 277 tests
- `all-features.md` F01–F32 all ticked. No roadmap items left.
- **Alembic migrations**: 4 total — `8c51c515c891` (initial), `598bccf9f7db` (leave_requests), `2823730c4ea4` (shift_rules), `b2d4cc7dbe00` (user_totp).
- **Cloud mode is now enforced at boot**: lifespan calls `Settings.validate_for_deployment()`; misconfigured cloud deploys (default jwt secret, sqlite DB, default localhost CORS) fail fast with a combined error listing every issue.
- **Known migration gotcha**: when autogenerate emits a new FK inside `batch_alter_table` (SQLite path), hand-edit the file to name the constraint — autogen emits `create_foreign_key(None, ...)` and SQLite's batch mode rejects it. Hit once during F26, documented in the done.md entry.

The walking skeleton is now usable in a real browser end-to-end, with ADMS push protocol,
WebSocket real-time feed, mobile real-time UI, a per-device background poller, and an
in-process pyzk harness for tests + hardware-free dev.

## Resume here next session

Working through Tier 1 of the BioTime parity gap. F33 (Departments) first.

## BioTime 9.5 parity gap — added 2026-05-14

The goal is to close the visible distance between tikko and BioTime 9.5 as a
turnkey time-and-attendance product. Items grouped by priority. Tier 1 must
ship before tikko can plausibly be pitched as a BioTime replacement; Tier 2 is
"serious product, not a toy"; Tier 3 is parity-for-parity polish.

### Tier 1 — core data + workflow gaps

- **F33 Departments / org hierarchy** — `Department(id, name, parent_id?)`,
  `Employee.department_id` FK, CRUD endpoints, settings UI section, employee
  form dept selector. Foundation for dept-filtered reports.
- **F34 Audit log** — `AuditEvent(actor_user_id, action, resource_type,
  resource_id, before_json, after_json, at)` + helper threaded through every
  mutating endpoint + paginated `/audit-log` view (admin only).
- **F35 Holiday calendar** — `Holiday(date, name)` + CRUD + payroll engine skips
  late/early/OT on holidays + settings UI section.
- **F36 Bulk employee import** — `POST /employees/import` CSV multipart, per-row
  result envelope, UI dropzone on `/employees` with results dialog.
- **F37 Leave types + balances** — `LeaveType(name, days_per_year, color)`,
  `LeaveBalance(employee_id, leave_type_id, year, allocated, used)`, request
  references a type, approval consumes balance.
- **F38 Manual punch correction** — `AttendanceLog.source ∈ {device, manual}` +
  `POST /attendance/manual` + audit-logged + UI button on attendance views.
- **F39 Cross-midnight shifts** — `ShiftRule` supports `end_time < start_time`
  (overnight); payroll engine attributes overnight punches to the shift's
  start date.
- **F39b Multi-segment shifts (deferred)** — `ShiftSegment` rows on a rule for
  split-shift days (retail / hospitality). Bigger refactor; kept out of F39 to
  ship cross-midnight without scope creep.
- **F40 Department / late / early / OT-specific reports** — dept roll-up
  endpoint + dedicated late, early-out, and overtime report variants.

### Tier 2 — enterprise / ops parity

- **F41 LDAP / SSO** — at minimum SAML or OIDC; LDAP bind is a BioTime staple.
- **F42 API keys for service accounts** — long-lived bearer tokens scoped to a
  capability set, listed/revocable from settings.
- **F43 Pay periods + rate tiers** — weekly/biweekly/monthly periods, regular
  vs. OT vs. holiday-OT rates per employee or per dept, payroll export.
- **F44 Multi-tenant / multi-company** — `tenant_id` on every domain row,
  middleware-enforced scoping, per-tenant settings.
- **F45 Scheduled reports** — cron-like definitions that email a generated
  report (XLSX) to a recipient list on a schedule.
- **F46 Face + card biometrics** — extend `EmployeeTemplate` beyond fingerprint
  to face templates and proximity-card UIDs; pull/push parity on ZK terminals
  that support them.

### Tier 3 — polish + completeness

- **F47 Employee photos** — upload + storage + display on employee card +
  optional sync to ZK terminals that show photos.
- **F48 Custom fields per employee** — admin-defined extra fields
  (name + type), rendered on the employee form.
- **F49 Internationalisation** — i18n on web + mobile (English baseline, then
  a second locale, probably Arabic or French given target geography).
- **F50 Kiosk / self-service mode** — a tablet-mounted "tap your code, see your
  status" view that runs on the same hardware as the ADMS terminals.
- **F51 SMS notifications** — alongside email, optional SMS via Twilio for
  leave decisions + clock-in confirmation.
- **F52 Mobile geofenced punch with selfie** — for orgs that want soft-clock
  from phones without a physical terminal; GPS + selfie liveness check.

## Up next — roadmap

_All original F01–F32 features shipped. Now executing the BioTime parity gap above, Tier 1 first._

## Optional features

_All optional UI gaps and follow-ups from the prior list are also shipped (F30-recovery, F28-xlsx, web leave-requests, web templates, employee leave on mobile, F22-edit, F22-delete-confirm)._

## Followups (not features)

- Backfill `tasks/done.md` entries for F15–F18 + UI polish (notes only live in commit messages right now).
- Migrate `next lint` → ESLint CLI + flat config when bumping to Next 16.
- `pnpm.overrides` to align `@types/react` (currently band-aided with `{children as any}` in `app/layout.tsx`).
- Postgres-dialect path for the attendance dedup insert (currently SQLite-flavoured `ON CONFLICT`).
- Set `TIKKO_JWT_SECRET` properly in prod (F31 now refuses to boot in cloud mode with the default — but no real secret is set yet).
- Refresh-token rotation flow — refresh tokens are issued but never exchanged.
- Mobile suite flake — first jest run after a cold start sometimes fails with an `act(...)` warning on `Animated.View` from `TouchableOpacity` in `login.tsx`. Second run is reliably green.
- TOTP `secret_b32` is stored plaintext — encryption-at-rest needs a KMS / wrapper-key story.

## Blocked

_(none)_
