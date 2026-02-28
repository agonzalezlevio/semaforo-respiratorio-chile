import { lazy, Suspense } from "react";
import type { WeekData, ForecastData, RegionIndex } from "@/lib/types";
import { FreshnessStrip } from "@/components/sections/FreshnessStrip";
import { StatusBanner } from "@/components/layout/StatusBanner";
import { KPIRow } from "@/components/sections/KPIRow";
import { CausesSection } from "@/components/sections/CausesSection";

const TrendSection = lazy(() => import("@/components/sections/TrendSection").then((m) => ({ default: m.TrendSection })));
const ForecastCards = lazy(() => import("@/components/sections/ForecastCards").then((m) => ({ default: m.ForecastCards })));
const HeatmapPanel = lazy(() => import("@/components/sections/HeatmapPanel").then((m) => ({ default: m.HeatmapPanel })));
const CompositionPanel = lazy(() => import("@/components/sections/CompositionPanel").then((m) => ({ default: m.CompositionPanel })));
const MethodologyPanel = lazy(() => import("@/components/sections/MethodologyPanel").then((m) => ({ default: m.MethodologyPanel })));

interface DashboardProps {
  current: WeekData;
  timeseries: WeekData[];
  forecast: ForecastData | null;
  regionName: string | null;
  referenceYears: number[];
  regionIndex: RegionIndex | null;
}

function ChartFallback() {
  return <div className="h-50 flex items-center justify-center text-text3 text-xs">Cargando gráficos…</div>;
}

export function Dashboard({ current, timeseries, forecast, regionName, referenceYears, regionIndex }: DashboardProps) {
  return (
    <div className="flex flex-col gap-4 max-w-330 mx-auto">
      <FreshnessStrip current={current} />
      <StatusBanner current={current} regionName={regionName} regionIndex={regionIndex} />
      <KPIRow current={current} referenceYears={referenceYears} />
      <CausesSection current={current} regionIndex={regionIndex} />

      <Suspense fallback={<ChartFallback />}>
        <TrendSection timeseries={timeseries} forecast={forecast} />
      </Suspense>

      {forecast && (
        <Suspense fallback={<ChartFallback />}>
          <ForecastCards forecast={forecast} />
        </Suspense>
      )}

      <Suspense fallback={<ChartFallback />}>
        <div className="flex flex-col gap-2.5">
          <HeatmapPanel timeseries={timeseries} />
          <CompositionPanel timeseries={timeseries} />
          <MethodologyPanel />
        </div>
      </Suspense>

      <footer className="mt-2 pt-3 border-t border-(--border) flex flex-col gap-1.5">
        <div className="flex justify-between flex-wrap gap-1">
          <span className="text-3xs text-text3">Proyecto independiente · No representa una fuente oficial del Ministerio de Salud</span>
          <span className="text-3xs text-text3">Datos públicos: DEIS/MINSAL vía datos.gob.cl</span>
        </div>
        <span className="text-3xs text-text3 leading-normal">
          Este dashboard no constituye consejo médico. Los datos se obtienen de fuentes públicas y pueden presentar diferencias respecto a cifras
          oficiales debido a rezagos en la notificación.
        </span>
      </footer>
    </div>
  );
}
