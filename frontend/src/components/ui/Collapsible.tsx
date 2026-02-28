import { useState, useId, type ReactNode } from "react";
import { Card } from "./Card";

interface CollapsibleProps {
  title: string;
  defaultOpen?: boolean;
  children: ReactNode;
}

export function Collapsible({ title, defaultOpen = false, children }: CollapsibleProps) {
  const [open, setOpen] = useState(defaultOpen);
  const contentId = useId();
  return (
    <Card className="p-0 overflow-hidden">
      <button
        onClick={() => setOpen((prev) => !prev)}
        aria-expanded={open}
        aria-controls={contentId}
        className="group w-full flex items-center justify-between px-4 py-3 border-none cursor-pointer font-[inherit]
                   bg-surface border-b border-b-transparent
                   aria-expanded:bg-blue-light aria-expanded:border-b-border-light"
      >
        <span className="text-sm font-semibold text-text1">{title}</span>
        <span
          className="text-2xs font-medium text-blue px-2 py-0.5 rounded-[3px]
                     bg-blue-light group-aria-expanded:bg-surface"
        >
          {open ? "Ocultar" : "Ver detalle"}
        </span>
      </button>
      <div id={contentId} hidden={!open} className="p-4">
        {children}
      </div>
    </Card>
  );
}
