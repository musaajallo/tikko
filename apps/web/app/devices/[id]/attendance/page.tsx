import AttendanceClient from "./AttendanceClient";

export default async function DeviceAttendancePage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  return <AttendanceClient deviceId={id} />;
}
