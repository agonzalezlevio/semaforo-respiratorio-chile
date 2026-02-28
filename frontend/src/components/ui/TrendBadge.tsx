import { TrendingUp, TrendingDown } from "lucide-react";
import { cn } from "@/lib/utils";

interface TrendBadgeProps {
  direction: "up" | "down";
  delta: string;
  context: string;
  compact?: boolean;
}

export function TrendBadge({ direction, delta, context, compact = false }: TrendBadgeProps) {
  const ArrowIcon = direction === "up" ? TrendingUp : TrendingDown;
  const ariaLabel = `${direction === "up" ? "Aumento" : "Disminución"} de ${delta} ${context}`;

  return (
    <span
      aria-label={ariaLabel}
      className={cn(
        "inline-flex items-center gap-0.75 font-medium tabular-nums text-text3 bg-background px-1.25 py-0.5 rounded-[3px] whitespace-nowrap",
        compact ? "text-[9px]" : "text-3xs",
      )}
    >
      <ArrowIcon aria-hidden="true" size={compact ? 10 : 11} strokeWidth={2.5} className={direction === "up" ? "text-trend-up" : "text-trend-down"} />
      {delta}
      <span className="text-text2" aria-hidden="true">
        {context}
      </span>
    </span>
  );
}
