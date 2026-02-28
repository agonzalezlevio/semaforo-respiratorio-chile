"""Classifies weekly data into alert levels and builds the alert timeseries."""

import math
from datetime import date, timedelta

import numpy as np
import pandas as pd

from pipeline.config import (
    AGE_COLUMNS,
    CANONICAL_CAUSES,
    COLOR_THRESHOLDS,
    REFERENCE_YEARS,
)


def classify_color(change_pct) -> str:
    """Classifies a percentage change into a alert alert level."""
    if change_pct is None or (isinstance(change_pct, float) and math.isnan(change_pct)):
        return "no_data"
    if change_pct < COLOR_THRESHOLDS["green"]:
        return "green"
    if change_pct < COLOR_THRESHOLDS["yellow"]:
        return "yellow"
    if change_pct < COLOR_THRESHOLDS["orange"]:
        return "orange"
    return "red"


def compute_change_pct(actual, median):
    """Computes percentage change: (actual/median - 1) * 100. Returns NaN if median is 0 or NaN."""
    if median is None or (isinstance(median, float) and math.isnan(median)) or median == 0:
        return float("nan")
    return (actual / median - 1) * 100


def compute_zscore(actual, ref_values) -> float:
    """Computes z-score of actual against reference values. Returns 0 if std is 0."""
    if len(ref_values) == 0:
        return 0.0
    mu = np.mean(ref_values)
    sigma = np.std(ref_values, ddof=0)
    if sigma == 0:
        return 0.0
    return float((actual - mu) / sigma)


_MONTHS_ES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]


def epi_week_date_range(year: int, week: int) -> str:
    """Convert (year, epi_week) to a Spanish date range like '31 mar - 6 abr'."""
    jan1 = date(year, 1, 1)
    dow = jan1.isoweekday()  # Monday=1 … Sunday=7
    start = jan1 + timedelta(days=(week - 1) * 7 - (dow - 1))
    end = start + timedelta(days=6)
    d1, m1 = start.day, _MONTHS_ES[start.month - 1]
    d2, m2 = end.day, _MONTHS_ES[end.month - 1]
    if m1 == m2:
        return f"{d1}-{d2} {m1}"
    return f"{d1} {m1}-{d2} {m2}"


def compute_baselines(national: pd.DataFrame) -> pd.DataFrame:
    """Computes baseline statistics from reference years for each (SE, Causa)."""
    ref = national[national["Anio"].isin(REFERENCE_YEARS)].copy()

    # Exclude SE 53 (rare carryover week)
    ref = ref[ref["SE"] <= 52]

    agg_dict = {
        "NumTotal": ["median", _p25, _p75, _p90],
    }
    for col in AGE_COLUMNS:
        if col in ref.columns:
            agg_dict[col] = ["median", _p25, _p75, _p90]

    baselines = ref.groupby(["SE", "Causa"]).agg(agg_dict)

    # Flatten multi-level columns
    baselines.columns = ["_".join(col).strip() for col in baselines.columns]
    baselines = baselines.reset_index()

    return baselines


def _p25(x):
    return np.percentile(x, 25)


def _p75(x):
    return np.percentile(x, 75)


def _p90(x):
    return np.percentile(x, 90)


_p25.__name__ = "p25"
_p75.__name__ = "p75"
_p90.__name__ = "p90"


def build_alert_timeseries(national: pd.DataFrame, baselines: pd.DataFrame) -> list[dict]:
    """Builds the alert timeseries for years >= 2024."""
    recent = national[national["Anio"] >= 2024].copy()
    ref_data = national[national["Anio"].isin(REFERENCE_YEARS)]
    entries = []

    # Sort SE 53 before SE 1 (carryover from previous year's last epi week)
    year_weeks = recent[["Anio", "SE"]].drop_duplicates().copy()
    year_weeks["_sort_se"] = year_weeks["SE"].apply(lambda x: 0 if x == 53 else x)
    year_weeks = year_weeks.sort_values(["Anio", "_sort_se"]).drop(columns=["_sort_se"])

    for _, row_yw in year_weeks.iterrows():
        year, week = int(row_yw["Anio"]), int(row_yw["SE"])
        week_data = recent[(recent["Anio"] == year) & (recent["SE"] == week)]

        # Get Total row for this week
        total_row = week_data[week_data["Causa"] == "Total"]
        if total_row.empty:
            continue
        total_actual = int(total_row["NumTotal"].iloc[0])

        # Get baseline for Total
        total_bl = baselines[
            (baselines["SE"] == (week if week <= 52 else 1)) & (baselines["Causa"] == "Total")
        ]
        total_median = float(total_bl["NumTotal_median"].iloc[0]) if not total_bl.empty else 0

        change_pct = compute_change_pct(total_actual, total_median)
        color = classify_color(change_pct)

        # Z-score against reference years
        ref_totals = ref_data[
            (ref_data["SE"] == (week if week <= 52 else 1)) & (ref_data["Causa"] == "Total")
        ]["NumTotal"].values
        z_score = compute_zscore(total_actual, ref_totals)

        # O/E ratio and percentage
        oe_ratio = round(total_actual / total_median, 2) if total_median > 0 else 0
        oe_pct = round(oe_ratio * 100, 1)

        # Expected range band (±12%)
        band_lo = round(total_median * 0.88)
        band_hi = round(total_median * 1.12)

        # Previous week delta
        prev_entry = entries[-1] if entries else None
        delta_prev = None
        delta_oe = None
        delta_change_pct_pp = None
        if prev_entry is not None:
            prev_total = prev_entry["total"]
            if prev_total > 0:
                delta_prev = round((total_actual / prev_total - 1) * 100, 1)
            # O/E delta vs previous week
            prev_oe = prev_entry.get("oe_ratio", 0)
            if prev_oe > 0:
                delta_oe = round(oe_ratio - prev_oe, 2)
            # Change_pct delta in pp
            prev_change = prev_entry.get("change_pct")
            if prev_change is not None and change_pct is not None and not math.isnan(change_pct):
                delta_change_pct_pp = round(change_pct - prev_change, 1)

        # By cause breakdown
        by_cause = []
        for cause in CANONICAL_CAUSES:
            if cause == "Total":
                continue
            cause_row = week_data[week_data["Causa"] == cause]
            if cause_row.empty:
                continue
            cause_actual = int(cause_row["NumTotal"].iloc[0])
            cause_bl = baselines[
                (baselines["SE"] == (week if week <= 52 else 1)) & (baselines["Causa"] == cause)
            ]
            cause_median = float(cause_bl["NumTotal_median"].iloc[0]) if not cause_bl.empty else 0
            cause_change = compute_change_pct(cause_actual, cause_median)

            ref_cause = ref_data[
                (ref_data["SE"] == (week if week <= 52 else 1)) & (ref_data["Causa"] == cause)
            ]["NumTotal"].values
            cause_z = compute_zscore(cause_actual, ref_cause)

            cause_oe = round(cause_actual / cause_median, 2) if cause_median > 0 else 0
            cause_color = classify_color(cause_change) if not math.isnan(cause_change) else "green"

            by_cause.append({
                "name": cause,
                "total": cause_actual,
                "baseline": round(cause_median, 1),
                "change_pct": round(cause_change, 1) if not math.isnan(cause_change) else None,
                "z_score": round(cause_z, 2),
                "oe": cause_oe,
                "color": cause_color,
            })

        # By age breakdown
        by_age = []
        for col, label in AGE_COLUMNS.items():
            if col not in total_row.columns:
                continue
            age_actual = int(total_row[col].iloc[0])
            age_bl_col = f"{col}_median"
            age_median = 0
            if not total_bl.empty and age_bl_col in total_bl.columns:
                age_median = float(total_bl[age_bl_col].iloc[0])
            age_change = compute_change_pct(age_actual, age_median)
            age_color = classify_color(age_change) if not math.isnan(age_change) else "green"
            by_age.append({
                "group": label,
                "total": age_actual,
                "baseline": round(age_median, 1),
                "change_pct": round(age_change, 1) if not math.isnan(age_change) else None,
                "color": age_color,
            })

        prev_dr = entries[-1]["date_range"] if entries else None

        entry = {
            "year": year,
            "week": week,
            "date_range": epi_week_date_range(year, week),
            "prev_date_range": prev_dr,
            "color": color,
            "total": total_actual,
            "baseline_median": round(total_median, 1),
            "change_pct": round(change_pct, 1) if not math.isnan(change_pct) else None,
            "z_score": round(z_score, 2),
            "oe_ratio": oe_ratio,
            "oe_pct": oe_pct,
            "band_lo": band_lo,
            "band_hi": band_hi,
            "delta_prev_week": delta_prev,
            "delta_oe": delta_oe,
            "delta_change_pct_pp": delta_change_pct_pp,
            "by_cause": by_cause,
            "by_age": by_age,
        }
        entries.append(entry)

    return entries


def build_baselines_json(baselines: pd.DataFrame) -> dict:
    """Structures baselines DataFrame into output dict."""
    weeks = []
    for se in sorted(baselines["SE"].unique()):
        se_data = baselines[baselines["SE"] == se]
        by_cause = []
        for cause in CANONICAL_CAUSES:
            cause_data = se_data[se_data["Causa"] == cause]
            if cause_data.empty:
                continue
            row = cause_data.iloc[0]
            entry = {
                "cause": cause,
                "median": round(float(row["NumTotal_median"]), 1),
                "p25": round(float(row["NumTotal_p25"]), 1),
                "p75": round(float(row["NumTotal_p75"]), 1),
                "p90": round(float(row["NumTotal_p90"]), 1),
            }
            # Add age breakdowns
            by_age = {}
            for col, label in AGE_COLUMNS.items():
                med_col = f"{col}_median"
                if med_col in row.index:
                    by_age[label] = {
                        "median": round(float(row[med_col]), 1),
                        "p25": round(float(row[f"{col}_p25"]), 1),
                        "p75": round(float(row[f"{col}_p75"]), 1),
                        "p90": round(float(row[f"{col}_p90"]), 1),
                    }
            if by_age:
                entry["by_age"] = by_age
            by_cause.append(entry)

        weeks.append({
            "week": int(se),
            "causes": by_cause,
        })

    return {
        "reference_years": REFERENCE_YEARS,
        "weeks": weeks,
    }


def build_alert_json(timeseries: list[dict]) -> dict:
    """Structures alert timeseries into output dict."""
    current = timeseries[-1] if timeseries else None
    return {
        "current": current,
        "timeseries": timeseries,
        "reference_years": REFERENCE_YEARS,
    }


def compute(national: pd.DataFrame) -> tuple[dict, dict, pd.DataFrame]:
    """Runs the main compute step. Returns (baselines_json, alert_json, baselines_df)."""
    print("[compute] Computing baselines...")
    baselines = compute_baselines(national)
    print(f"  Baseline entries: {len(baselines)}")

    print("[compute] Building alert timeseries...")
    timeseries = build_alert_timeseries(national, baselines)
    print(f"  Timeseries entries: {len(timeseries)}")

    baselines_json = build_baselines_json(baselines)
    alert_json = build_alert_json(timeseries)

    print("[compute] Done.")
    return baselines_json, alert_json, baselines
