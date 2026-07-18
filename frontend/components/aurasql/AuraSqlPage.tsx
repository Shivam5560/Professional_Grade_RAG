import type { ReactNode } from "react";

import { CanvasHeader } from "@/components/shell/CanvasHeader";
import { FocusCanvas } from "@/components/shell/FocusCanvas";

export function AuraSqlPage({
  title,
  description,
  eyebrow = "AuraSQL",
  actions,
  children,
}: {
  title: string;
  description: string;
  eyebrow?: string;
  actions?: ReactNode;
  children: ReactNode;
}) {
  return (
    <FocusCanvas ariaLabel={`${title} workspace`}>
      <CanvasHeader
        eyebrow={eyebrow}
        title={title}
        description={description}
        actions={actions}
      />
      <div className="flex flex-1 flex-col py-5 sm:py-6">{children}</div>
    </FocusCanvas>
  );
}
