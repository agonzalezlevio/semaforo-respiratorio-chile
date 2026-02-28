"""EARS C2 anomaly detection and mix shift analysis."""

import numpy as np
import pandas as pd

from pipeline.config import (
    CANONICAL_CAUSES,
    EARS_GUARD,
    EARS_THRESHOLD,
    EARS_WINDOW,
    MIX_SHARE_THRESHOLD,
    MIX_Z_THRESHOLD,
)


def ears_c2(
    series,
    window: int = EARS_WINDOW,
    guard: int = EARS_GUARD,
    threshold: float = EARS_THRESHOLD,
) -> list[dict]:
    """EARS C2: rolling z-score with guard band.

    Args:
        series: array-like of numeric values (chronologically ordered).
        window: number of baseline observations.
        guard: guard band (skip recent observations to avoid contamination).
        threshold: z-score threshold for alert.

    Returns:
        List of dicts with keys: index, z, alert.
    """
    values = np.array(series, dtype=float)
    results = []
    start = window + guard
    for i in range(start, len(values)):
        baseline = values[i - window - guard : i - guard]
        mu = np.mean(baseline)
        sigma = np.std(baseline, ddof=0)
        if sigma > 0:
            z = float((values[i] - mu) / sigma)
        else:
            z = 0.0
        results.append({
            "index": i,
            "z": round(z, 2),
            "alert": z > threshold,
        })
    return results


def detect_volume_spikes(national: pd.DataFrame) -> list[dict]:
    """Run EARS C2 on the Total cause national series to detect volume spikes."""
    total = national[national["Causa"] == "Total"].sort_values(["Anio", "SE"])
    if total.empty:
        return []

    series = total["NumTotal"].values
    years = total["Anio"].values
    weeks = total["SE"].values

    alerts_raw = ears_c2(series)
    spikes = []
    for a in alerts_raw:
        if a["alert"]:
            idx = a["index"]
            spikes.append({
                "type": "volume_spike",
                "year": int(years[idx]),
                "week": int(weeks[idx]),
                "total": int(series[idx]),
                "z_score": a["z"],
            })
    return spikes


def detect_mix_shift(
    national: pd.DataFrame,
    alert_timeseries: list[dict],
) -> list[dict]:
    """Detects mix shift: individual cause z-score spikes when total is normal.

    A mix shift fires when:
    1. The total is green or yellow (change < 25%).
    2. An individual cause has z > MIX_Z_THRESHOLD.
    3. That cause represents > MIX_SHARE_THRESHOLD of the total.
    """
    mix_shifts = []

    # Build per-cause EARS C2 series
    cause_series = {}
    for cause in CANONICAL_CAUSES:
        if cause == "Total":
            continue
        cause_data = national[national["Causa"] == cause].sort_values(["Anio", "SE"])
        if cause_data.empty:
            continue
        cause_series[cause] = {
            "values": cause_data["NumTotal"].values,
            "years": cause_data["Anio"].values,
            "weeks": cause_data["SE"].values,
            "alerts": ears_c2(cause_data["NumTotal"].values, threshold=MIX_Z_THRESHOLD),
        }

    # Index alert entries for quick lookup
    alert_index = {(e["year"], e["week"]): e for e in alert_timeseries}

    # Check each cause's alerts against alert context
    for cause, data in cause_series.items():
        for alert in data["alerts"]:
            if not alert["alert"]:
                continue
            idx = alert["index"]
            year = int(data["years"][idx])
            week = int(data["weeks"][idx])
            actual = int(data["values"][idx])

            sem_entry = alert_index.get((year, week))
            if sem_entry is None:
                continue

            # Only trigger when total is green or yellow
            if sem_entry["color"] not in ("green", "yellow"):
                continue

            # Check share threshold
            total = sem_entry["total"]
            if total == 0:
                continue
            share = actual / total
            if share < MIX_SHARE_THRESHOLD:
                continue

            mix_shifts.append({
                "type": "mix_shift",
                "year": year,
                "week": week,
                "total_color": sem_entry["color"],
                "total_change_pct": sem_entry["change_pct"],
                "cause": cause,
                "cause_total": actual,
                "cause_z": alert["z"],
                "cause_share": round(share * 100, 1),
            })

    # Sort chronologically
    mix_shifts.sort(key=lambda x: (x["year"], x["week"], x["cause"]))
    return mix_shifts


def annotate_alert_with_mix_shift(
    alert_json: dict,
    mix_shifts: list[dict],
) -> dict:
    """Add mix_shift_active and mix_shift_causes to alert timeseries entries."""
    # Group mix shifts by (year, week)
    ms_index: dict[tuple, list[str]] = {}
    for ms in mix_shifts:
        key = (ms["year"], ms["week"])
        if key not in ms_index:
            ms_index[key] = []
        ms_index[key].append(ms["cause"])

    for entry in alert_json["timeseries"]:
        key = (entry["year"], entry["week"])
        if key in ms_index:
            entry["mix_shift_active"] = True
            entry["mix_shift_causes"] = ms_index[key]
        else:
            entry["mix_shift_active"] = False
            entry["mix_shift_causes"] = []

    # Update current entry
    if alert_json["current"]:
        key = (alert_json["current"]["year"], alert_json["current"]["week"])
        if key in ms_index:
            alert_json["current"]["mix_shift_active"] = True
            alert_json["current"]["mix_shift_causes"] = ms_index[key]
        else:
            alert_json["current"]["mix_shift_active"] = False
            alert_json["current"]["mix_shift_causes"] = []

    return alert_json


def build_anomalies_json(volume_spikes: list[dict], mix_shifts: list[dict]) -> dict:
    """Structure anomalies into output dict."""
    # Merge and sort all anomalies chronologically
    all_anomalies = volume_spikes + mix_shifts
    all_anomalies.sort(key=lambda x: (x["year"], x["week"]))

    return {
        "total_anomalies": len(all_anomalies),
        "volume_spikes": len(volume_spikes),
        "mix_shifts": len(mix_shifts),
        "mix_z_threshold": MIX_Z_THRESHOLD,
        "events": all_anomalies,
    }


def detect_anomalies(
    national: pd.DataFrame,
    alert_json: dict,
) -> tuple[dict, dict]:
    """Main anomaly detection step. Returns (anomalies_json, updated_alert_json)."""
    print("[anomalies] Detecting volume spikes (EARS C2)...")
    volume_spikes = detect_volume_spikes(national)
    print(f"  Volume spikes: {len(volume_spikes)}")

    print("[anomalies] Detecting mix shifts...")
    mix_shifts = detect_mix_shift(national, alert_json["timeseries"])
    print(f"  Mix shifts: {len(mix_shifts)}")

    # Annotate alert with mix shift info
    alert_json = annotate_alert_with_mix_shift(alert_json, mix_shifts)

    anomalies_json = build_anomalies_json(volume_spikes, mix_shifts)
    print("[anomalies] Done.")
    return anomalies_json, alert_json
