import { TOOLTIP_STYLE } from "@/lib/chart-theme";
import { formatNumber } from "@/lib/format";

interface ChartPayloadEntry {
  dataKey: string;
  value: number | [number, number];
  color: string;
  name: string;
  payload: Record<string, unknown>;
}

interface ChartTooltipProps {
  active?: boolean;
  payload?: ChartPayloadEntry[];
  label?: number | string;
  excludeKeys?: string[];
  formatValue?: (value: number) => string;
}

export function ChartTooltip({ active, payload, label, excludeKeys, formatValue = formatNumber }: ChartTooltipProps) {
  if (!active || !payload?.length) return null;
  const dateRange = payload[0]?.payload?.date_range as string | undefined;
  const filtered = excludeKeys ? payload.filter((e) => !excludeKeys.includes(e.dataKey)) : payload;

  return (
    <div style={TOOLTIP_STYLE}>
      <div className="font-semibold mb-1 text-(--text2) text-2xs">
        SE {label}
        {dateRange ? ` · ${dateRange}` : ""}
      </div>
      {filtered.map((entry) => {
        const val = entry.value;
        if (typeof val !== "number") return null;
        return (
          <div key={entry.dataKey} className="flex justify-between gap-4 text-xs">
            <span className="text-text3">{entry.name}</span>
            <span className="font-semibold text-text1 [font-variant-numeric:tabular-nums]">{formatValue(val)}</span>
          </div>
        );
      })}
    </div>
  );
}
