import { Wrench } from "lucide-react";

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

export interface ComingSoonProps {
  title: string;
  description?: string;
  bullets?: string[];
}

export function ComingSoon({ title, description, bullets }: ComingSoonProps) {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">{title}</h1>
        {description && (
          <p className="text-sm text-muted-foreground">{description}</p>
        )}
      </div>

      <Card>
        <CardHeader className="flex flex-row items-center gap-3 space-y-0">
          <span className="grid h-9 w-9 place-items-center rounded-md bg-muted text-muted-foreground">
            <Wrench className="h-5 w-5" />
          </span>
          <div>
            <CardTitle>Coming soon</CardTitle>
            <CardDescription>
              This page is a placeholder while the feature is being built.
            </CardDescription>
          </div>
        </CardHeader>
        {bullets && bullets.length > 0 && (
          <CardContent>
            <p className="mb-2 text-sm font-medium">What you&apos;ll find here:</p>
            <ul className="ml-5 list-disc space-y-1 text-sm text-muted-foreground">
              {bullets.map((b) => (
                <li key={b}>{b}</li>
              ))}
            </ul>
          </CardContent>
        )}
      </Card>
    </div>
  );
}
