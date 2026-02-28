import type { ForecastData, WeekData } from "./types";

interface ForecastChartPoint {
  week: number;
  date_range?: string;
  observed?: number;
  median?: number;
  projected?: number;
  low95?: number;
  high95?: number;
  range?: [number, number];
}

export function buildForecastChart(forecast: ForecastData, timeseries: WeekData[]): ForecastChartPoint[] {
  const { current_week, current_year } = forecast;

  // Index baselines for O(1) lookup in projections
  const baselineByKey = new Map(timeseries.map((t) => [`${t.year}-${t.week}`, t.baseline_median]));

  // Slice by index (not year) so early-January forecasts include prior-year observed data
  const cutoff = timeseries.findIndex((t) => t.year === current_year && t.week === current_week);
  const endIdx = cutoff >= 0 ? cutoff + 1 : timeseries.length;
  const recentObserved = timeseries.slice(Math.max(0, endIdx - 4), endIdx).map((t) => ({
    week: t.week,
    date_range: t.date_range,
    observed: t.total,
    median: t.baseline_median,
  }));

  const projectedWeeks = forecast.horizons.map((h) => ({
    week: h.week,
    date_range: h.date_range,
    projected: h.proj,
    low95: h.lo95,
    high95: h.hi95,
    range: [h.lo95, h.hi95] as [number, number],
    median: baselineByKey.get(`${h.year}-${h.week}`),
  }));

  return [...recentObserved, ...projectedWeeks];
}

interface TimeSeriesChartPoint {
  week: number;
  year: number;
  date_range: string;
  observed: number;
  median: number;
}

export function buildTimeSeriesChart(timeseries: WeekData[]): TimeSeriesChartPoint[] {
  return timeseries.map((t) => ({
    week: t.week,
    year: t.year,
    date_range: t.date_range,
    observed: t.total,
    median: t.baseline_median,
  }));
}
