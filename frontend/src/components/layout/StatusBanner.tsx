import type { CSSProperties } from "react";
import { LEVEL_COLOR, LEVEL_TEXT_COLOR, LEVEL_BG, alertName } from "@/lib/colors";
import type { WeekData, RegionIndex, AlertLevel } from "@/lib/types";
import { Card } from "@/components/ui/Card";

interface StatusBannerProps {
  current: WeekData;
  regionName: string | null;
  regionIndex: RegionIndex | null;
}

const ALERT_MESSAGES: Record<AlertLevel, string> = {
  green: "Sin alerta respiratoria",
  yellow: "Alerta moderada",
  orange: "Alerta significativa",
  red: "Alerta crítica",
};

const ALERT_LEVELS: AlertLevel[] = ["green", "yellow", "orange", "red"];

function AlertBar({ active }: { active: AlertLevel }) {
  return (
    <div className="flex gap-0.75 items-end" aria-hidden="true">
      {ALERT_LEVELS.map((level) => {
        const isActive = level === active;
        const fg = LEVEL_COLOR[level];
        return (
          <div
            key={level}
            data-active={isActive || undefined}
            className="w-1.75 h-6 rounded-sm transition-[background,border-color] duration-200
                       border border-(--bar-fg)/20 bg-(--bar-fg)/13
                       data-active:border-transparent data-active:bg-(--bar-fg)"
            style={{ "--bar-fg": fg } as CSSProperties}
          />
        );
      })}
    </div>
  );
}

function getActivityLabel(changePct: number): string {
  if (changePct < -50) return "significativamente bajo";
  if (changePct < 0) return "bajo";
  return "sobre";
}

export function StatusBanner({ current, regionName, regionIndex }: StatusBannerProps) {
  const level = current.color;
  const fg = LEVEL_COLOR[level];
  const fgText = LEVEL_TEXT_COLOR[level];
  const bg = LEVEL_BG[level];
  const name = alertName[level];
  const message = ALERT_MESSAGES[level];
  const activityLabel = getActivityLabel(current.change_pct);
  const isNational = regionName === null;

  let totalRegions = 0;
  let greenCount = 0;
  const nonGreenRegions: string[] = [];

  if (regionIndex) {
    totalRegions = regionIndex.regions.length;
    for (const r of regionIndex.regions) {
      if (r.color === "green") greenCount++;
      else nonGreenRegions.push(`${r.name} en nivel ${alertName[r.color].toLowerCase()}`);
    }
  }

  return (
    <Card
      className="p-4"
      style={{ "--fg": fg, "--fg-text": fgText, "--fg-glow": `${fg}25`, background: bg, borderColor: `${fg}30` } as CSSProperties}
    >
      <div className="flex items-center gap-3.5">
        <div
          aria-hidden="true"
          className="shrink-0 w-5 h-5 rounded-full bg-(--fg) shadow-[0_0_0_4px_var(--fg-glow)] animate-[pulse-dot_2s_ease-in-out_infinite]"
        />

        <div className="flex-1 min-w-0">
          <div className="text-base font-bold leading-[1.3] mb-0.5 text-(--fg-text)">
            Nivel {name} - {message}
          </div>
          <div className="text-[13px] text-(--text2) leading-normal">
            Actividad respiratoria {activityLabel} lo esperado.
            {isNational && regionIndex && (
              <>
                {" "}
                {greenCount} de {totalRegions} regiones en nivel verde.
                {nonGreenRegions.length > 0 && ` ${nonGreenRegions.join(". ")}.`}
              </>
            )}
          </div>
        </div>

        <div className="shrink-0">
          <AlertBar active={level} />
        </div>
      </div>
    </Card>
  );
}
