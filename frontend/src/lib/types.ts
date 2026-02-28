export type AlertLevel = "green" | "yellow" | "orange" | "red";

export interface CauseData {
  name: string;
  total: number;
  baseline: number;
  change_pct: number;
  z_score: number;
  oe: number;
  color: AlertLevel;
}

export interface AgeData {
  group: string;
  total: number;
  baseline: number;
  change_pct: number;
  color: AlertLevel;
}

export interface WeekData {
  year: number;
  week: number;
  date_range: string;
  prev_date_range: string | null;
  color: AlertLevel;
  total: number;
  baseline_median: number;
  change_pct: number;
  z_score: number;
  oe_ratio: number;
  oe_pct: number;
  band_lo: number;
  band_hi: number;
  delta_prev_week: number | null;
  delta_oe: number | null;
  delta_change_pct_pp: number | null;
  by_cause: CauseData[];
  by_age: AgeData[];
}

export interface AlertData {
  current: WeekData;
  timeseries: WeekData[];
  // e.g. [2017, 2018, 2019, 2022, 2023]
  referenceYears: number[];
}

export interface ForecastHorizon {
  horizon: number;
  year: number;
  week: number;
  date_range: string;
  proj: number;
  lo95: number;
  hi95: number;
  lo50: number;
  hi50: number;
  color: AlertLevel;
  pOrange: number;
  pRed: number;
}

export interface ForecastData {
  status: string;
  current_year: number;
  current_week: number;
  horizons: ForecastHorizon[];
}

export interface RegionInfo {
  code: number;
  name: string;
  color: AlertLevel;
  total: number;
  change_pct: number | null;
  week: number | null;
  year: number | null;
}

export interface RegionIndex {
  regions: RegionInfo[];
}
