import type { CSSProperties, ReactNode } from "react";
import { cn } from "@/lib/utils";

interface CaptionProps {
  children: ReactNode;
  className?: string;
  style?: CSSProperties;
}

export function Caption({ children, className, style }: CaptionProps) {
  return (
    <span className={cn("text-xs font-normal text-text3 tracking-[0.3px] block mb-1", className)} style={style}>
      {children}
    </span>
  );
}
