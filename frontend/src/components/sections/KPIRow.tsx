import type { CSSProperties } from "react";
import type { WeekData } from "@/lib/types";
import { LEVEL_COLOR } from "@/lib/colors";
import { formatNumber, formatPct } from "@/lib/format";
import { Card } from "@/components/ui/Card";
import { Caption } from "@/components/ui/Caption";
import { TrendBadge } from "@/components/ui/TrendBadge";

interface KPIRowProps {
  current: WeekData;
  referenceYears: number[];
}

interface KPICardProps {
  label: string;
  value: string;
  sub: string;
  accentColor?: string;
  valueColor?: string;
  trend?: { direction: "up" | "down"; delta: string; context: string } | null;
}

function KPICard({ label, value, sub, accentColor, valueColor, trend }: KPICardProps) {
  return (
    <Card
      className="p-4 relative pl-3.25 border-l-[3px] border-l-(--accent)"
      style={{ "--accent": accentColor ?? "var(--border-light)" } as CSSProperties}
    >
      <Caption>{label}</Caption>
      <div
        className="flex items-center gap-1.5 text-[28px] font-bold leading-[1.2] font-features-['tnum'] text-(--val-color)"
        style={{ "--val-color": valueColor ?? "var(--text1)" } as CSSProperties}
        aria-label={`${label}: ${value}`}
      >
        {value}
      </div>
      {trend && (
        <div className="mt-0.75">
          <TrendBadge direction={trend.direction} delta={trend.delta} context={trend.context} compact />
        </div>
      )}
      <span className="text-2xs text-text3 leading-[1.3] mt-0.75 block">{sub}</span>
    </Card>
  );
}

function trendDirection(delta: number): "up" | "down" {
  return delta >= 0 ? "up" : "down";
}

export function KPIRow({ current, referenceYears }: KPIRowProps) {
  const { week, total, baseline_median, change_pct, delta_prev_week, color, oe_ratio, oe_pct, delta_oe, delta_change_pct_pp } = current;

  const refLabel = referenceYears.length > 0 ? referenceYears.join(", ") : "histórica";

  const prevWeekNum = week > 1 ? week - 1 : 52;
  const vsContext = current.prev_date_range ? `vs SE ${prevWeekNum} (${current.prev_date_range})` : `vs SE ${prevWeekNum}`;

  let trendEmergencies: KPICardProps["trend"] = null;
  if (delta_prev_week != null) {
    trendEmergencies = {
      direction: trendDirection(delta_prev_week),
      delta: formatNumber(Math.abs(delta_prev_week)),
      context: vsContext,
    };
  }

  let trendOe: KPICardProps["trend"] = null;
  if (delta_oe != null) {
    const sign = delta_oe >= 0 ? "+" : "";
    trendOe = {
      direction: trendDirection(delta_oe),
      delta: `${sign}${Math.abs(delta_oe).toFixed(2)}`,
      context: vsContext,
    };
  }

  let trendVar: KPICardProps["trend"] = null;
  if (delta_change_pct_pp != null) {
    const sign = delta_change_pct_pp >= 0 ? "+" : "";
    trendVar = {
      direction: trendDirection(delta_change_pct_pp),
      delta: `${sign}${Math.abs(delta_change_pct_pp).toFixed(1)}pp`,
      context: vsContext,
    };
  }

  const accentVariation = LEVEL_COLOR[color];

  return (
    <section aria-label="Indicadores clave de la semana" className="grid grid-cols-2 gap-3">
      <KPICard
        label="Urgencias observadas"
        value={formatNumber(total)}
        sub={`SE ${week} · ${current.date_range}`}
        accentColor="var(--nhs-blue)"
        trend={trendEmergencies}
      />

      <KPICard label="Mediana esperada" value={formatNumber(baseline_median)} sub={`Referencia ${refLabel}`} />

      <KPICard label="Razón O/E" value={oe_ratio.toFixed(2)} sub={`${oe_pct}% del esperado`} trend={trendOe} />

      <KPICard
        label="Variación"
        value={formatPct(change_pct)}
        sub={change_pct < 0 ? "Bajo la mediana" : "Sobre la mediana"}
        accentColor={accentVariation}
        valueColor={accentVariation}
        trend={trendVar}
      />
    </section>
  );
}
