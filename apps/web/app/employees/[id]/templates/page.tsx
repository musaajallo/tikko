import EmployeeTemplatesClient from "./templates-client";

export default async function EmployeeTemplatesPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  return <EmployeeTemplatesClient employeeId={id} />;
}
