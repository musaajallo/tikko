"use client";

import { ArrowLeft, Clock, RefreshCw } from "lucide-react";
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
import { Skeleton } from "@/components/ui/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { api, type AttendanceList } from "@/lib/api";

export default function AttendanceClient({ deviceId }: { deviceId: string }) {
  const [list, setList] = useState<AttendanceList>({ items: [], total: 0 });
  const [loading, setLoading] = useState(true);
  const [polling, setPolling] = useState(false);

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      const result = await api.listAttendance(deviceId);
      setList(result);
    } catch (err) {
      toast.error("Failed to load attendance", {
        description: err instanceof Error ? err.message : String(err),
      });
    } finally {
      setLoading(false);
    }
  }, [deviceId]);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const onPoll = async () => {
    setPolling(true);
    try {
      const result = await api.pollDevice(deviceId);
      toast.success("Device polled", {
        description: `${result.polled} record${result.polled === 1 ? "" : "s"}, ${result.new} new`,
      });
      await refresh();
    } catch (err) {
      toast.error("Poll failed", {
        description: err instanceof Error ? err.message : String(err),
      });
    } finally {
      setPolling(false);
    }
  };

  return (
    <div className="space-y-4">
      <Link
        href="/devices"
        className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground"
      >
        <ArrowLeft className="h-4 w-4" /> All devices
      </Link>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0">
          <div>
            <CardTitle>Attendance</CardTitle>
            <CardDescription>Punches pulled from this terminal.</CardDescription>
          </div>
          <Button onClick={onPoll} disabled={polling}>
            <RefreshCw className={`mr-1 h-4 w-4 ${polling ? "animate-spin" : ""}`} />
            {polling ? "Polling…" : "Poll now"}
          </Button>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="space-y-2">
              <Skeleton className="h-10 w-full" />
              <Skeleton className="h-10 w-full" />
              <Skeleton className="h-10 w-full" />
            </div>
          ) : list.items.length === 0 ? (
            <div className="grid place-items-center gap-2 py-12 text-center">
              <Clock className="h-10 w-10 text-muted-foreground" />
              <h3 className="text-base font-semibold">No attendance records yet</h3>
              <p className="max-w-sm text-sm text-muted-foreground">
                Click <strong>Poll now</strong> to pull punches buffered on the device.
              </p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Device user</TableHead>
                  <TableHead>Punched at (UTC)</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead>Verify mode</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {list.items.map((item) => (
                  <TableRow key={item.id}>
                    <TableCell className="font-medium">
                      {item.device_user_id}
                    </TableCell>
                    <TableCell className="font-mono text-xs">
                      {item.punched_at}
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline">{item.punch_type}</Badge>
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline">{item.verify_mode}</Badge>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
