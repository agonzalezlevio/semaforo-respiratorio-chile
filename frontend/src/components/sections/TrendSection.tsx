import type { ForecastData, WeekData } from "@/lib/types";
import { WeeklyTrendCard } from "@/components/sections/WeeklyTrendCard";
import { ProjectionCard } from "@/components/sections/ProjectionCard";

interface TrendSectionProps {
  timeseries: WeekData[];
  forecast: ForecastData | null;
}

export function TrendSection({ timeseries, forecast }: TrendSectionProps) {
  if (timeseries.length === 0) return null;

  return (
    <section aria-label="Tendencia y proyección de urgencias" className={`grid gap-3 ${forecast ? "md:grid-cols-2" : ""}`}>
      <WeeklyTrendCard timeseries={timeseries} />
      {forecast && <ProjectionCard forecast={forecast} timeseries={timeseries} />}
    </section>
  );
}
