import type React from "react";
import type { RegionIndex, AlertLevel } from "@/lib/types";
import { LEVEL_COLOR, LEVEL_TEXT_COLOR, LEVEL_BG } from "@/lib/colors";
import { Card } from "@/components/ui/Card";
import { Caption } from "@/components/ui/Caption";

const LEVEL_ORDER: Array<{ key: AlertLevel; label: string }> = [
  { key: "green", label: "Verde" },
  { key: "yellow", label: "Amarillo" },
  { key: "orange", label: "Naranjo" },
  { key: "red", label: "Rojo" },
];

export function RegionLevelSummary({ regionIndex }: { regionIndex: RegionIndex }) {
  const counts: Record<AlertLevel, number> = {
    green: 0,
    yellow: 0,
    orange: 0,
    red: 0,
  };

  for (const region of regionIndex.regions) {
    counts[region.color] = (counts[region.color] ?? 0) + 1;
  }

  return (
    <Card className="p-4">
      <Caption>Regiones en cada nivel</Caption>
      <div role="list" aria-label="Recuento de regiones por nivel de alerta" className="grid grid-cols-4 gap-1.5 mt-1.5">
        {LEVEL_ORDER.map(({ key, label }) => {
          const count = counts[key] ?? 0;
          const hasAlert = count > 0;
          const fg = LEVEL_COLOR[key];
          const fgText = LEVEL_TEXT_COLOR[key];

          return (
            <div
              key={key}
              role="listitem"
              data-active={hasAlert || undefined}
              className="group flex flex-col items-center rounded py-2.5 px-1.5 pb-2 transition-[background] duration-200
                         bg-surface-alt border border-border-light
                         data-active:bg-(--tile-bg) data-active:border-(--tile-fg)/20"
              style={hasAlert ? ({ "--tile-bg": LEVEL_BG[key], "--tile-fg": fg, "--tile-fg-text": fgText } as React.CSSProperties) : undefined}
            >
              <span
                className="text-lg font-bold leading-[1.1] font-features-['tnum'] mb-1
                           text-text3 group-data-active:text-(--tile-fg-text)"
                aria-label={`${count} región${count !== 1 ? "es" : ""} en nivel ${label}`}
              >
                {count}
              </span>
              <span className="text-[9px] mt-px text-text3 group-data-active:text-(--text2)">{label}</span>
            </div>
          );
        })}
      </div>
    </Card>
  );
}
