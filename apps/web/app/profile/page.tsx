"use client";

import { CheckCircle2, KeyRound, ShieldCheck, User2 } from "lucide-react";
import Link from "next/link";
import QRCode from "qrcode";
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
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import { api, type AuthMeResponse } from "@/lib/api";

export default function ProfilePage() {
  const [me, setMe] = useState<AuthMeResponse | null>(null);
  const [loading, setLoading] = useState(true);

  const [hasTOTP, setHasTOTP] = useState<boolean | null>(null);

  // Change password
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [pwSubmitting, setPwSubmitting] = useState(false);

  // TOTP enroll
  const [enrollOpen, setEnrollOpen] = useState(false);
  const [enrollSecret, setEnrollSecret] = useState<string | null>(null);
  const [qrDataUrl, setQrDataUrl] = useState<string | null>(null);
  const [enrollCode, setEnrollCode] = useState("");
  const [enrollSubmitting, setEnrollSubmitting] = useState(false);

  // TOTP disable
  const [disableOpen, setDisableOpen] = useState(false);
  const [disablePassword, setDisablePassword] = useState("");
  const [disableSubmitting, setDisableSubmitting] = useState(false);

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      const result = await api.getMe();
      setMe(result);
    } catch (err) {
      toast.error("Failed to load profile", {
        description: err instanceof Error ? err.message : String(err),
      });
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  // We don't have a dedicated "is TOTP enabled" endpoint; infer by calling
  // enroll, which returns 409 if already enabled. To avoid the side-effect of
  // mutating state on every page load, we only set the flag on user action.
  // For the visual cue we keep it null until the user interacts.

  const onChangePassword = async (e: React.FormEvent) => {
    e.preventDefault();
    setPwSubmitting(true);
    try {
      await api.changePassword({
        current_password: currentPassword,
        new_password: newPassword,
      });
      toast.success("Password updated");
      setCurrentPassword("");
      setNewPassword("");
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      toast.error("Could not change password", {
        description: /401/.test(message) ? "Current password is wrong." : message,
      });
    } finally {
      setPwSubmitting(false);
    }
  };

  const openEnroll = async () => {
    try {
      const result = await api.totpEnroll();
      setEnrollSecret(result.secret);
      setEnrollOpen(true);
      const dataUrl = await QRCode.toDataURL(result.otpauth_uri);
      setQrDataUrl(dataUrl);
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      if (/409/.test(message)) {
        toast.info("Two-factor is already enabled.");
        setHasTOTP(true);
      } else {
        toast.error("Could not start enrollment", { description: message });
      }
    }
  };

  const onVerifyEnroll = async () => {
    setEnrollSubmitting(true);
    try {
      await api.totpVerify(enrollCode);
      toast.success("Two-factor authentication enabled");
      setHasTOTP(true);
      setEnrollOpen(false);
      setEnrollSecret(null);
      setQrDataUrl(null);
      setEnrollCode("");
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      toast.error("Verification failed", {
        description: /422/.test(message) ? "That code didn't match." : message,
      });
    } finally {
      setEnrollSubmitting(false);
    }
  };

  const onDisableTotp = async () => {
    setDisableSubmitting(true);
    try {
      await api.totpDisable(disablePassword);
      toast.success("Two-factor authentication disabled");
      setHasTOTP(false);
      setDisableOpen(false);
      setDisablePassword("");
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      toast.error("Could not disable", {
        description: /401/.test(message) ? "Password is wrong." : message,
      });
    } finally {
      setDisableSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Profile</h1>
        <p className="text-sm text-muted-foreground">
          Your account, password, and two-factor authentication.
        </p>
      </div>

      <Card>
        <CardHeader className="flex flex-row items-center gap-3 space-y-0">
          <span className="grid h-9 w-9 place-items-center rounded-md bg-muted text-muted-foreground">
            <User2 className="h-5 w-5" />
          </span>
          <div>
            <CardTitle>Account</CardTitle>
            <CardDescription>Signed-in identity and linked employee.</CardDescription>
          </div>
        </CardHeader>
        <CardContent>
          {loading || !me ? (
            <div className="space-y-2">
              <Skeleton className="h-5 w-72" />
              <Skeleton className="h-5 w-40" />
            </div>
          ) : (
            <dl className="grid grid-cols-1 gap-3 text-sm md:grid-cols-2">
              <div>
                <dt className="text-xs uppercase tracking-wide text-muted-foreground">Email</dt>
                <dd className="font-medium">{me.user.email}</dd>
              </div>
              <div>
                <dt className="text-xs uppercase tracking-wide text-muted-foreground">Role</dt>
                <dd>
                  <Badge variant="secondary">{me.user.role}</Badge>
                </dd>
              </div>
              <div>
                <dt className="text-xs uppercase tracking-wide text-muted-foreground">
                  Linked employee
                </dt>
                <dd>
                  {me.employee ? (
                    <Link
                      href={`/employees`}
                      className="font-medium text-primary hover:underline"
                    >
                      {me.employee.full_name}{" "}
                      <span className="text-muted-foreground">
                        (#{me.employee.employee_code})
                      </span>
                    </Link>
                  ) : (
                    <span className="text-muted-foreground">Not linked</span>
                  )}
                </dd>
              </div>
              <div>
                <dt className="text-xs uppercase tracking-wide text-muted-foreground">
                  Account created
                </dt>
                <dd className="font-mono text-xs">{me.user.created_at}</dd>
              </div>
            </dl>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center gap-3 space-y-0">
          <span className="grid h-9 w-9 place-items-center rounded-md bg-muted text-muted-foreground">
            <KeyRound className="h-5 w-5" />
          </span>
          <div>
            <CardTitle>Change password</CardTitle>
            <CardDescription>Minimum 10 characters.</CardDescription>
          </div>
        </CardHeader>
        <CardContent>
          <form onSubmit={onChangePassword} className="grid max-w-md gap-4">
            <div className="grid gap-2">
              <Label htmlFor="current_password">Current password</Label>
              <Input
                id="current_password"
                type="password"
                value={currentPassword}
                onChange={(e) => setCurrentPassword(e.target.value)}
                required
                autoComplete="current-password"
              />
            </div>
            <div className="grid gap-2">
              <Label htmlFor="new_password">New password</Label>
              <Input
                id="new_password"
                type="password"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                required
                minLength={10}
                autoComplete="new-password"
              />
            </div>
            <div>
              <Button type="submit" disabled={pwSubmitting}>
                {pwSubmitting ? "Saving…" : "Update password"}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center gap-3 space-y-0">
          <span className="grid h-9 w-9 place-items-center rounded-md bg-muted text-muted-foreground">
            <ShieldCheck className="h-5 w-5" />
          </span>
          <div>
            <CardTitle>Two-factor authentication</CardTitle>
            <CardDescription>
              Required for admin logins. Recommended for everyone.
            </CardDescription>
          </div>
        </CardHeader>
        <CardContent className="flex items-center gap-3">
          {hasTOTP === true ? (
            <>
              <Badge className="gap-1" variant="default">
                <CheckCircle2 className="h-3.5 w-3.5" /> Enabled
              </Badge>
              <Button variant="outline" onClick={() => setDisableOpen(true)}>
                Disable
              </Button>
            </>
          ) : (
            <>
              <Badge variant="secondary">Not enabled</Badge>
              <Button onClick={openEnroll}>Enable two-factor</Button>
            </>
          )}
        </CardContent>
      </Card>

      {/* Enroll dialog */}
      <Dialog
        open={enrollOpen}
        onOpenChange={(open) => {
          if (!open) {
            setEnrollOpen(false);
            setEnrollSecret(null);
            setQrDataUrl(null);
            setEnrollCode("");
          }
        }}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Set up two-factor</DialogTitle>
            <DialogDescription>
              Scan the QR with your authenticator app (Google Authenticator, Authy, 1Password,
              …) and enter the 6-digit code to confirm.
            </DialogDescription>
          </DialogHeader>
          {qrDataUrl && (
            <div className="grid place-items-center gap-2">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src={qrDataUrl}
                alt="TOTP QR code"
                className="h-44 w-44 rounded-md border bg-white p-2"
              />
              <p className="text-xs text-muted-foreground">
                Or enter the setup key manually:
              </p>
              <code className="rounded bg-muted px-2 py-1 font-mono text-xs">
                {enrollSecret}
              </code>
            </div>
          )}
          <div className="grid gap-2">
            <Label htmlFor="enroll_code">Verification code</Label>
            <Input
              id="enroll_code"
              inputMode="numeric"
              pattern="\d{6}"
              maxLength={6}
              placeholder="123456"
              value={enrollCode}
              onChange={(e) => setEnrollCode(e.target.value)}
            />
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => {
                setEnrollOpen(false);
                setEnrollSecret(null);
                setQrDataUrl(null);
                setEnrollCode("");
              }}
            >
              Cancel
            </Button>
            <Button
              onClick={onVerifyEnroll}
              disabled={enrollSubmitting || enrollCode.length !== 6}
            >
              {enrollSubmitting ? "Verifying…" : "Verify and enable"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Disable dialog */}
      <Dialog open={disableOpen} onOpenChange={(open) => !open && setDisableOpen(false)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Disable two-factor authentication</DialogTitle>
            <DialogDescription>
              Confirm your password. This removes the second factor from your account.
            </DialogDescription>
          </DialogHeader>
          <div className="grid gap-2">
            <Label htmlFor="disable_password">Password</Label>
            <Input
              id="disable_password"
              type="password"
              value={disablePassword}
              onChange={(e) => setDisablePassword(e.target.value)}
              autoComplete="current-password"
            />
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDisableOpen(false)}>
              Cancel
            </Button>
            <Button
              variant="destructive"
              onClick={onDisableTotp}
              disabled={disableSubmitting || disablePassword.length === 0}
            >
              {disableSubmitting ? "Disabling…" : "Disable"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
