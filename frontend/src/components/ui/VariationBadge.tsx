import { TrendingUp, TrendingDown } from "lucide-react";
import { LEVEL_TEXT_COLOR } from "@/lib/colors";
import type { CSSProperties } from "react";
import type { AlertLevel } from "@/lib/types";

interface VariationBadgeProps {
  value: number;
  level: AlertLevel;
}

export function VariationBadge({ value, level }: VariationBadgeProps) {
  const color = LEVEL_TEXT_COLOR[level] || LEVEL_TEXT_COLOR.green;
  return (
    <span
      className="inline-flex items-center gap-0.5 text-2xs font-semibold tabular-nums whitespace-nowrap text-(--vc)"
      style={{ "--vc": color } as CSSProperties}
    >
      {value < 0 ? <TrendingDown size={11} strokeWidth={2.5} /> : <TrendingUp size={11} strokeWidth={2.5} />}
      {Math.abs(value).toFixed(1)}%
    </span>
  );
}
