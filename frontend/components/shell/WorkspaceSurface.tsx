import type { HTMLAttributes, ReactNode } from "react";

import { cn } from "@/lib/utils";

type WorkspaceSurfaceProps = HTMLAttributes<HTMLDivElement> & {
  children: ReactNode;
  tone?: "default" | "raised" | "inset";
};

export function WorkspaceSurface({
  children,
  className,
  tone = "default",
  ...props
}: WorkspaceSurfaceProps): JSX.Element {
  return (
    <div
      className={cn(
        "bg-workspace text-foreground",
        tone === "raised" && "bg-workspace-raised",
        tone === "inset" && "bg-workspace-inset",
        className,
      )}
      {...props}
    >
      {children}
    </div>
  );
}
