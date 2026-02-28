import type { CSSProperties } from "react";

interface LegendItem {
  color: string;
  label: string;
  dashed?: boolean;
}

export function ChartLegend({ items }: { items: LegendItem[] }) {
  return (
    <div className="flex gap-3 mt-2 flex-wrap">
      {items.map(({ color, label, dashed }) => (
        <div key={label} className="flex items-center gap-1">
          <span
            data-dashed={dashed || undefined}
            className="w-3 block rounded-sm h-0.75 bg-(--swatch-color) data-dashed:h-0 data-dashed:bg-transparent data-dashed:border-t-2 data-dashed:border-dashed data-dashed:border-(--swatch-color)"
            style={{ "--swatch-color": color } as CSSProperties}
          />
          <span className="text-2xs text-text3">{label}</span>
        </div>
      ))}
    </div>
  );
}
