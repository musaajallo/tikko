import { ComingSoon } from "@/components/coming-soon";

export default function DocumentationPage() {
  return (
    <ComingSoon
      title="Documentation"
      description="Operator and admin guides for tikko."
      bullets={[
        "Quick start: register a device and run your first poll",
        "Employee enrollment and fingerprint template workflow",
        "Deployment modes (LAN vs cloud) and TLS",
        "API reference (OpenAPI) and webhook contracts",
      ]}
    />
  );
}
