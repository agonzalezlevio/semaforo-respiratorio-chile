import { LevelDot } from "@/components/ui/LevelDot";
import type { WeekData } from "@/lib/types";

export function FreshnessStrip({ current }: { current: WeekData }) {
  const weekLabel = `Datos hasta SE ${current.week} (${current.date_range})`;
  const weekLabelShort = `SE ${current.week} · ${current.date_range}`;

  return (
    <div
      role="status"
      aria-label="Estado de actualización de datos"
      className="flex flex-col md:flex-row md:items-center gap-1 md:gap-4 p-2 md:px-3 md:py-2 text-3xs md:text-2xs bg-surface border border-(--border) rounded text-(--text2) leading-normal"
    >
      <div className="flex items-center gap-1.5">
        <LevelDot level="green" size={6} />
        <span className="font-semibold text-text1">
          <span className="hidden md:inline">{weekLabel}</span>
          <span className="md:hidden">{weekLabelShort}</span>
        </span>
      </div>
      <span className="hidden md:inline text-(--border)" aria-hidden="true">
        |
      </span>
      <span>
        <span className="hidden md:inline">Frecuencia: semanal (cada lunes)</span>
        <span className="md:hidden">Actualización semanal (lunes)</span>
      </span>
      <span className="hidden md:inline text-(--border)" aria-hidden="true">
        |
      </span>
      <span className="text-trend-up leading-[1.4]">
        <span className="hidden md:inline">Los datos DEIS tienen un rezago habitual de 1-4 semanas epidemiológicas</span>
        <span className="md:hidden">Rezago habitual: 1-4 SE</span>
      </span>
    </div>
  );
}
