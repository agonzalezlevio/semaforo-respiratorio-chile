import type { CSSProperties, ReactNode } from "react";
import { cn } from "@/lib/utils";

interface CardProps {
  children: ReactNode;
  className?: string;
  style?: CSSProperties;
}

export function Card({ children, className, style }: CardProps) {
  return (
    <div className={cn("bg-surface border border-border rounded p-5", className)} style={style}>
      {children}
    </div>
  );
}
