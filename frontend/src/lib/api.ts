import type { AlertData, AlertLevel, ForecastData, ForecastHorizon, WeekData, RegionIndex } from "./types";

const BASE = import.meta.env.BASE_URL ?? "/";
const DOUBLE_SLASH = /\/\//g;

async function fetchJSON<T>(path: string): Promise<T> {
  const url = `${BASE}data/${path}`.replace(DOUBLE_SLASH, "/");
  const res = await fetch(url);
  if (!res.ok) throw new Error(`Error cargando datos (${res.status})`);
  return res.json();
}

function scopePath(regionCode?: number): string {
  return regionCode != null ? `regions/${regionCode}/` : "";
}

function parseAlertData(raw: Record<string, unknown>): AlertData {
  const current = {
    ...(raw.current as Record<string, unknown>),
    color: (raw.current as Record<string, unknown>).color as AlertLevel,
  } as WeekData;
  const timeseries = (raw.timeseries as Record<string, unknown>[]).map((week) => ({ ...week, color: week.color as AlertLevel }) as WeekData);
  const referenceYears = (raw.reference_years as number[]) ?? [];
  return { current, timeseries, referenceYears };
}

export async function fetchAlertData(regionCode?: number): Promise<AlertData> {
  return parseAlertData(await fetchJSON(scopePath(regionCode) + "alert.json"));
}

export async function fetchForecast(): Promise<ForecastData> {
  const raw = await fetchJSON<Record<string, unknown>>("forecast.json");
  if (raw.status !== "ok") return raw as unknown as ForecastData;
  const horizons = (raw.horizons as Record<string, unknown>[]).map((entry) => ({
    ...entry,
    color: entry.color as AlertLevel,
    pOrange: entry.p_orange as number,
    pRed: entry.p_red as number,
  })) as ForecastHorizon[];
  return { ...raw, horizons } as unknown as ForecastData;
}

export async function fetchRegionIndex(): Promise<RegionIndex> {
  const raw = await fetchJSON<Record<string, unknown>>("regions/index.json");
  const regions = (raw.regions as Record<string, unknown>[]).map((entry) => ({
    ...entry,
    color: entry.color as AlertLevel,
  }));
  return { regions } as RegionIndex;
}
