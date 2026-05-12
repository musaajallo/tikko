"use client";

import { Cpu, MoreHorizontal, Plus } from "lucide-react";
import Link from "next/link";
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
import type { Device } from "@tikko/shared-types";

export default function DevicesPage() {
  const [devices, setDevices] = useState<Device[]>([]);
  const [loading, setLoading] = useState(true);
  const [open, setOpen] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const [name, setName] = useState("");
  const [host, setHost] = useState("");
  const [port, setPort] = useState("4370");
  const [location, setLocation] = useState("");

  const [testingId, setTestingId] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      const { items } = await api.listDevices();
      setDevices(items);
    } catch (err) {
      toast.error("Failed to load devices", {
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
      await api.createDevice({
        name,
        host,
        port: Number(port) || 4370,
        location: location || null,
      });
      toast.success(`Added ${name}`);
      setName("");
      setHost("");
      setPort("4370");
      setLocation("");
      setOpen(false);
      await refresh();
    } catch (err) {
      toast.error("Could not add device", {
        description: err instanceof Error ? err.message : String(err),
      });
    } finally {
      setSubmitting(false);
    }
  };

  const onTestConnection = async (deviceId: string, deviceName: string) => {
    setTestingId(deviceId);
    try {
      const info = await api.testConnection(deviceId);
      toast.success(`${deviceName} is reachable`, {
        description: `${info.device_name} · serial ${info.serial_number} · firmware ${info.firmware_version}`,
      });
    } catch (err) {
      toast.error(`${deviceName} unreachable`, {
        description: err instanceof Error ? err.message : String(err),
      });
    } finally {
      setTestingId(null);
    }
  };

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between gap-2 space-y-0">
        <div>
          <CardTitle>Devices</CardTitle>
          <CardDescription>
            Terminals registered to this tenant.
          </CardDescription>
        </div>
        <Dialog open={open} onOpenChange={setOpen}>
          <DialogTrigger asChild>
            <Button>
              <Plus className="mr-1 h-4 w-4" /> Add device
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Add device</DialogTitle>
              <DialogDescription>
                Register a terminal that this server can reach on port 4370 (or that
                pushes to this server&apos;s ADMS endpoint).
              </DialogDescription>
            </DialogHeader>
            <form onSubmit={onAdd} className="grid gap-4">
              <div className="grid gap-2">
                <Label htmlFor="name">Name</Label>
                <Input
                  id="name"
                  placeholder="Front gate"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  required
                />
              </div>
              <div className="grid gap-2">
                <Label htmlFor="host">Host (IP)</Label>
                <Input
                  id="host"
                  placeholder="192.168.1.50"
                  value={host}
                  onChange={(e) => setHost(e.target.value)}
                  required
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="grid gap-2">
                  <Label htmlFor="port">Port</Label>
                  <Input
                    id="port"
                    inputMode="numeric"
                    value={port}
                    onChange={(e) => setPort(e.target.value)}
                  />
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="location">Location</Label>
                  <Input
                    id="location"
                    placeholder="HQ entrance"
                    value={location}
                    onChange={(e) => setLocation(e.target.value)}
                  />
                </div>
              </div>
              <DialogFooter>
                <Button type="submit" disabled={submitting}>
                  {submitting ? "Adding…" : "Add device"}
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
        ) : devices.length === 0 ? (
          <div className="grid place-items-center gap-2 py-12 text-center">
            <Cpu className="h-10 w-10 text-muted-foreground" />
            <h3 className="text-base font-semibold">No devices yet</h3>
            <p className="max-w-sm text-sm text-muted-foreground">
              Add your first terminal to start pulling attendance.
            </p>
            <Button className="mt-2" onClick={() => setOpen(true)}>
              <Plus className="mr-1 h-4 w-4" /> Add device
            </Button>
          </div>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Name</TableHead>
                <TableHead>Host</TableHead>
                <TableHead>Location</TableHead>
                <TableHead>Status</TableHead>
                <TableHead className="w-[80px]"></TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {devices.map((d) => (
                <TableRow key={d.id}>
                  <TableCell className="font-medium">{d.name}</TableCell>
                  <TableCell className="font-mono text-xs">
                    {d.host}:{d.port}
                  </TableCell>
                  <TableCell className="text-muted-foreground">
                    {d.location ?? "—"}
                  </TableCell>
                  <TableCell>
                    <Badge variant="secondary">Registered</Badge>
                  </TableCell>
                  <TableCell>
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button variant="ghost" size="icon" className="h-8 w-8">
                          <MoreHorizontal className="h-4 w-4" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        <DropdownMenuItem asChild>
                          <Link href={`/devices/${d.id}/attendance`}>
                            View attendance
                          </Link>
                        </DropdownMenuItem>
                        <DropdownMenuItem
                          onClick={() => onTestConnection(d.id, d.name)}
                          disabled={testingId === d.id}
                        >
                          {testingId === d.id ? "Testing…" : "Test connection"}
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
  );
}
