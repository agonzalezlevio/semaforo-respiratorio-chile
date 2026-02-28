"""Orchestrates the full pipeline: ingest, compute, anomalies, forecast, write JSONs."""

import json
import math
import os
import sys

from pathlib import Path

from pipeline.anomalies import detect_anomalies
from pipeline.compute import compute
from pipeline.config import DATA_OUTPUT, REGION_MAP, REGIONS_OUTPUT
from pipeline.ingest import ingest


class NanEncoder(json.JSONEncoder):
    """Encodes NaN/Infinity as null in JSON output."""

    def default(self, obj):
        return super().default(obj)

    def encode(self, o):
        return super().encode(_sanitize(o))


def _sanitize(obj):
    """Replaces NaN/Infinity with None recursively for JSON serialization."""
    if isinstance(obj, float) and (math.isnan(obj) or math.isinf(obj)):
        return None
    if isinstance(obj, dict):
        return {k: _sanitize(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_sanitize(v) for v in obj]
    return obj


def write_json(data: dict, filename: str) -> None:
    """Writes a dict to a JSON file in data/output/."""
    write_json_to(data, DATA_OUTPUT / filename)


def write_json_to(data: dict, path: Path) -> None:
    """Write JSON atomically via tmp file + os.replace (fallback to direct write on Windows)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    import tempfile
    tmp_fd, tmp_path = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    try:
        with os.fdopen(tmp_fd, "w", encoding="utf-8") as tmp:
            json.dump(data, tmp, cls=NanEncoder, ensure_ascii=False, indent=2)
        try:
            os.replace(tmp_path, str(path))
        except OSError:
            # Windows: os.replace can fail if antivirus/indexer holds the file
            import shutil
            shutil.move(tmp_path, str(path))
    except BaseException:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise
    size_kb = path.stat().st_size / 1024
    print(f"  Wrote {path} ({size_kb:.1f} KB)")


def build_latest_json(alert_json: dict, forecast_json: dict | None = None) -> dict:
    """Extracts current week entry from alert JSON as standalone latest.json."""
    current = alert_json.get("current")
    if current is None:
        return {"error": "no current data"}
    latest = dict(current)
    if forecast_json and forecast_json.get("horizons"):
        h1 = forecast_json["horizons"][0]
        latest["forecast_next"] = {
            "horizon": h1["horizon"],
            "year": h1["year"],
            "week": h1["week"],
            "color": h1["color"],
            "proj": h1["proj"],
            "p_orange": h1["p_orange"],
            "p_red": h1["p_red"],
        }

    return latest


def run_regional_pipeline(regional) -> None:
    """Computes baselines, alert, and anomalies per region. Writes to regions/{code}/."""
    print("\n[regional] Processing regions...")
    index_entries = []

    for code, name in sorted(REGION_MAP.items()):
        region_df = regional[regional["RegionCodigo"] == code].drop(columns=["RegionCodigo"])
        if region_df.empty:
            print(f"  Region {code} ({name}): no data -skipped")
            continue

        baselines_json, alert_json, _ = compute(region_df)
        anomalies_json, alert_json = detect_anomalies(region_df, alert_json)

        region_dir = REGIONS_OUTPUT / str(code)
        write_json_to(baselines_json, region_dir / "baselines.json")
        write_json_to(alert_json, region_dir / "alert.json")
        write_json_to(anomalies_json, region_dir / "anomalies.json")

        # Build index entry from current week
        current = alert_json.get("current")
        index_entries.append({
            "code": code,
            "name": name,
            "color": current["color"] if current else "no_data",
            "total": current["total"] if current else 0,
            "change_pct": current.get("change_pct") if current else None,
            "week": current["week"] if current else None,
            "year": current["year"] if current else None,
        })
        print(f"  Region {code} ({name}): {current['color'].upper() if current else 'N/A'}")

    # Write index
    index_json = {"regions": index_entries}
    write_json_to(index_json, REGIONS_OUTPUT / "index.json")
    print(f"[regional] Done -{len(index_entries)} regions.")


def run_pipeline() -> None:
    """Runs the full pipeline."""
    print("=" * 60)
    print("Semáforo Respiratorio -Pipeline")
    print("=" * 60)

    national, regional = ingest()
    baselines_json, alert_json, baselines_df = compute(national)
    anomalies_json, alert_json = detect_anomalies(national, alert_json)

    from pipeline.forecast import forecast
    forecast_json = forecast(national, baselines_df, alert_json)

    latest_json = build_latest_json(alert_json, forecast_json)

    print("\n[output] Writing JSON files...")
    write_json(baselines_json, "baselines.json")
    write_json(alert_json, "alert.json")
    write_json(anomalies_json, "anomalies.json")
    write_json(forecast_json, "forecast.json")
    write_json(latest_json, "latest.json")

    run_regional_pipeline(regional)

    print("\n" + "=" * 60)
    print("Pipeline complete.")
    if alert_json.get("current"):
        c = alert_json["current"]
        print(f"  Current: SE {c['week']}/{c['year']} -{c['color'].upper()}"
              f" ({c['change_pct']:+.1f}%)" if c.get("change_pct") is not None
              else f"  Current: SE {c['week']}/{c['year']} -{c['color'].upper()}")
    if forecast_json.get("horizons"):
        h1 = forecast_json["horizons"][0]
        print(f"  Forecast SE+1: {h1['color'].upper()} · P(orange)={h1['p_orange']:.1%}")
    print("=" * 60)


if __name__ == "__main__":
    try:
        run_pipeline()
    except Exception as e:
        print(f"\nFATAL: {e}", file=sys.stderr)
        sys.exit(1)
