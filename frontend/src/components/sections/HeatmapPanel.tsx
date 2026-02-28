import { useMemo } from "react";
import type React from "react";
import { LEVEL_COLOR, alertName } from "@/lib/colors";
import { Collapsible } from "@/components/ui/Collapsible";
import type { AlertLevel, WeekData } from "@/lib/types";

function cellColor(color: WeekData["color"], isCurrent: boolean): string {
  const base = LEVEL_COLOR[color];
  return isCurrent ? base : `${base}50`;
}

export function HeatmapPanel({ timeseries }: { timeseries: WeekData[] }) {
  const byYear = useMemo(() => {
    const map = new Map<number, WeekData[]>();
    for (const w of timeseries) {
      if (!map.has(w.year)) map.set(w.year, []);
      map.get(w.year)!.push(w);
    }
    return Array.from(map.entries()).sort((a, b) => a[0] - b[0]);
  }, [timeseries]);

  const firstYear = byYear.length > 0 ? byYear[0][0] : 0;
  const currentYear = byYear.length > 0 ? byYear[byYear.length - 1][0] : 0;
  const yearRange = firstYear && currentYear ? `${firstYear}-${currentYear}` : "";

  return (
    <Collapsible title={`Historial semanal - Heatmap ${yearRange}`}>
      {/* Mobile: rows, padded to 52 weeks */}
      <div className="flex flex-col gap-1.5 md:hidden overflow-hidden">
        {byYear.map(([year, weeks]) => {
          const isCurrent = year === currentYear;
          const empty = Math.max(0, 52 - weeks.length);
          return (
            <div key={year} className="flex items-center gap-2">
              <span className={`shrink-0 w-6 text-right text-[9px] mb-0.5 ${isCurrent ? "text-(--nhs-blue) font-bold" : "text-text3 font-normal"}`}>
                {String(year).slice(2)}
              </span>
              <div className="flex gap-px flex-1 min-w-0">
                {weeks.map((d) => (
                  <div key={`${d.year}-${d.week}`} className="flex-1 min-w-0 h-3 rounded-sm" style={{ background: cellColor(d.color, isCurrent) }} />
                ))}
                {Array.from({ length: empty }, (_, i) => (
                  <div key={`empty-${i}`} className="flex-1 min-w-0 h-3 rounded-sm bg-(--border)/40" />
                ))}
              </div>
            </div>
          );
        })}
      </div>

      {/* Desktop: columns, padded to 52 weeks */}
      <div className="hidden md:flex gap-1.5 pb-1">
        {byYear.map(([year, weeks]) => {
          const isCurrent = year === currentYear;
          const empty = Math.max(0, 52 - weeks.length);
          return (
            <div key={year} className="flex flex-col items-center gap-px min-w-0 flex-52">
              <span className={`text-[9px] mb-0.5 ${isCurrent ? "text-(--nhs-blue) font-bold" : "text-text3 font-normal"}`}>
                {String(year).slice(2)}
              </span>
              <div className="flex gap-px w-full">
                {weeks.map((d) => (
                  <div
                    key={`${d.year}-${d.week}`}
                    className="flex-1 min-w-0 h-3.5 rounded-sm"
                    style={{ background: cellColor(d.color, isCurrent) }}
                  />
                ))}
                {Array.from({ length: empty }, (_, i) => (
                  <div key={`empty-${i}`} className="flex-1 min-w-0 h-3.5 rounded-sm bg-(--border)/40" />
                ))}
              </div>
            </div>
          );
        })}
      </div>
      <div className="flex gap-2.5 mt-2">
        {(["green", "yellow", "orange", "red"] as const satisfies AlertLevel[]).map((level) => (
          <div key={level} className="flex items-center gap-1">
            <span
              className="w-2 h-2 rounded-[2px] inline-block bg-(--legend-color)"
              style={{ "--legend-color": LEVEL_COLOR[level] } as React.CSSProperties}
            />
            <span className="text-3xs text-text3">{alertName[level]}</span>
          </div>
        ))}
      </div>
    </Collapsible>
  );
}
