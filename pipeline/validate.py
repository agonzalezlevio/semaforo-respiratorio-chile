"""Runs retrospective time-series cross-validation for the LightGBM forecast model.

Standalone script: ``python -m pipeline.validate``
Not run weekly (too expensive, ~2 min). Run manually when needed.
"""

import json

import numpy as np
import pandas as pd

from pipeline.config import (
    DATA_OUTPUT,
    FORECAST_CAL_SIZE,
    FORECAST_HORIZONS,
    FORECAST_QUANTILES,
    VALIDATION_FOLDS,
    VALIDATION_MIN_TRAIN_ROWS,
)
from pipeline.compute import compute_baselines
from pipeline.forecast import (
    build_features,
    build_ratio_series,
    get_feature_columns,
    _cqr_calibrate,
    HAS_LGB,
)
from pipeline.compute import classify_color


WIS_ALPHAS = [0.05, 0.20, 0.50]
WIS_QUANTILE_PAIRS = [
    (0.025, 0.975),  # 95% interval
    (0.1, 0.9),      # 80% interval
    (0.25, 0.75),    # 50% interval
]


def compute_wis(
    actual: float,
    quantile_preds: dict[float, float],
) -> float:
    """Compute Weighted Interval Score (FluSight standard).

    WIS = (1/(K+0.5)) * [0.5*|y - median| + sum(alpha_k/2 * IS(alpha_k))]

    where IS(alpha) = (U - L) + (2/alpha)*max(L - y, 0) + (2/alpha)*max(y - U, 0)

    Args:
        actual: observed value
        quantile_preds: dict mapping quantile level -> predicted value

    Returns:
        WIS score (lower is better)
    """
    median_pred = quantile_preds.get(0.5, 0)
    abs_error = 0.5 * abs(actual - median_pred)

    interval_scores = 0.0
    for alpha, (q_lo, q_hi) in zip(WIS_ALPHAS, WIS_QUANTILE_PAIRS):
        L = quantile_preds.get(q_lo, 0)
        U = quantile_preds.get(q_hi, 0)
        width = U - L
        undershoot = (2 / alpha) * max(L - actual, 0)
        overshoot = (2 / alpha) * max(actual - U, 0)
        IS_alpha = width + undershoot + overshoot
        interval_scores += (alpha / 2) * IS_alpha

    K = len(WIS_ALPHAS)
    wis = (1 / (K + 0.5)) * (abs_error + interval_scores)
    return wis


def _build_naive_quantiles(baselines_df: pd.DataFrame, se: int) -> dict[float, float]:
    """Build naive forecast quantiles from baselines for a given SE.

    Uses baseline median as point forecast; p25/p75 as IC 50%.
    Extrapolates IC 80% and IC 95% using the IQR.
    """
    bl = baselines_df[(baselines_df["Causa"] == "Total") &
                      (baselines_df["SE"] == (1 if se == 53 else se))]
    if bl.empty:
        return {q: 0 for q in FORECAST_QUANTILES}

    row = bl.iloc[0]
    median = float(row["NumTotal_median"])
    p25 = float(row["NumTotal_p25"])
    p75 = float(row["NumTotal_p75"])
    iqr = p75 - p25

    # Extrapolate wider intervals from IQR
    p10 = median - 1.5 * iqr
    p90 = median + 1.5 * iqr
    p025 = median - 2.5 * iqr
    p975 = median + 2.5 * iqr

    return {
        0.025: max(p025, 0),
        0.1: max(p10, 0),
        0.25: p25,
        0.5: median,
        0.75: p75,
        0.9: p90,
        0.975: p975,
    }


def _classify_color_from_actual(actual: float, baseline_median: float) -> str:
    """Classifies an alert level from actual value and baseline median."""
    if baseline_median == 0:
        return "no_data"
    change_pct = (actual / baseline_median - 1) * 100
    return classify_color(change_pct)


def run_fold(
    national: pd.DataFrame,
    fold_config: dict,
    baselines_func=compute_baselines,
) -> list[dict]:
    """Run one fold of time-series CV.

    For each test week, trains models on all data up to that week
    and predicts h=1..4.

    Args:
        national: full national DataFrame
        fold_config: dict with train_end, test_year
        baselines_func: function to compute baselines (for testing)

    Returns:
        List of dicts with keys: test_year, test_week, horizon, actual,
        predicted (dict of quantile->value), pred_color, actual_color
    """
    if not HAS_LGB:
        print("[validate] LightGBM not available -skipping.")
        return []

    train_end = fold_config["train_end"]
    test_year = fold_config["test_year"]

    # Split data
    train_base = national[national["Anio"] <= train_end]
    test_data = national[(national["Anio"] == test_year) & (national["Causa"] == "Total")]
    test_data = test_data.sort_values("SE")

    if len(train_base) < VALIDATION_MIN_TRAIN_ROWS:
        print(f"  Fold test={test_year}: insufficient training data ({len(train_base)} rows)")
        return []

    # Compute baselines from training data
    baselines_df = baselines_func(train_base)

    # Get baseline median lookup
    bl_total = baselines_df[baselines_df["Causa"] == "Total"].set_index("SE")["NumTotal_median"]

    feature_cols = get_feature_columns()
    results = []

    test_weeks = sorted(test_data["SE"].unique())
    for test_se in test_weeks:
        # Data available: all training + test up to (but not including) test_se + max_horizon
        available = national[
            (national["Anio"] < test_year) |
            ((national["Anio"] == test_year) & (national["SE"] < test_se))
        ]

        # Build features from available data
        try:
            ratio_series = build_ratio_series(available, baselines_df)
            features_df = build_features(ratio_series)
        except Exception as e:
            print(f"  [validate] Skipping SE {test_se}: {e}")
            continue

        if len(features_df) < 30:
            continue

        X = features_df[feature_cols].values
        y = features_df["ratio_t"].values

        # Get actual value for this test week
        actual_row = test_data[test_data["SE"] == test_se]
        if actual_row.empty:
            continue
        actual_value = float(actual_row["NumTotal"].iloc[0])

        # Get baseline median for actual color
        bl_se = 1 if test_se == 53 else test_se
        baseline_med = float(bl_total.get(bl_se, bl_total.median()))

        actual_color = _classify_color_from_actual(actual_value, baseline_med)

        # Train and predict for each horizon
        for h in FORECAST_HORIZONS:
            # For horizon h, we need the actual value h weeks ahead
            # h=1 means predicting test_se itself from data before test_se
            # So actual for h=1 is test_se, for h=2 is test_se+1, etc.
            # But we need the actual at the target week
            if h > 1:
                target_se_actual = test_se + h - 1
                if target_se_actual > 52:
                    continue  # Skip if target is beyond the year
                actual_h_row = test_data[test_data["SE"] == target_se_actual]
                if actual_h_row.empty:
                    continue
                actual_h = float(actual_h_row["NumTotal"].iloc[0])
                bl_se_h = target_se_actual
            else:
                actual_h = actual_value
                bl_se_h = bl_se

            baseline_med_h = float(bl_total.get(bl_se_h, bl_total.median()))

            # Shift target for direct forecasting
            y_shifted = y[:-h] if h > 0 else y
            X_shifted = X[:len(y_shifted)]

            if len(X_shifted) < 30:
                continue

            # Train with CQR calibration (same as production)
            quantile_preds_t = _cqr_calibrate(
                X_shifted, y_shifted, X[[-1]], FORECAST_CAL_SIZE,
            )

            # Inverse transform: ratio = exp(ratio_t)
            quantile_preds = {}
            for q in FORECAST_QUANTILES:
                ratio_t = quantile_preds_t[q]
                pred_ratio = np.exp(min(ratio_t, 10))
                pred_value = pred_ratio * baseline_med_h
                quantile_preds[q] = pred_value

            # Predicted color from median
            pred_median = quantile_preds.get(0.5, 0)
            if baseline_med_h > 0:
                pred_change = (pred_median / baseline_med_h - 1) * 100
            else:
                pred_change = 0
            pred_color = classify_color(pred_change)

            # Actual color at target
            actual_h_color = _classify_color_from_actual(actual_h, baseline_med_h)

            results.append({
                "test_year": test_year,
                "test_week": test_se,
                "horizon": h,
                "actual": actual_h,
                "predicted": quantile_preds,
                "pred_color": pred_color,
                "actual_color": actual_h_color,
            })

    return results


def compute_naive_metrics(
    national: pd.DataFrame,
    baselines_df: pd.DataFrame,
    fold_results: list[dict],
) -> dict:
    """Compute naive seasonal baseline metrics for comparison.

    Uses baseline median as point forecast, extrapolated quantiles from IQR.
    """
    by_horizon: dict[int, list[dict]] = {}

    for r in fold_results:
        h = r["horizon"]
        if h not in by_horizon:
            by_horizon[h] = []

        # Find the SE for the target
        target_se = r["test_week"] + h - 1
        if target_se > 52:
            continue

        naive_q = _build_naive_quantiles(baselines_df, target_se)
        actual = r["actual"]

        wis = compute_wis(actual, naive_q)
        mae = abs(actual - naive_q[0.5])
        in_95 = 1 if naive_q[0.025] <= actual <= naive_q[0.975] else 0

        # Naive color: from baseline median
        bl_row = baselines_df[
            (baselines_df["Causa"] == "Total") &
            (baselines_df["SE"] == (1 if target_se == 53 else target_se))
        ]
        if not bl_row.empty:
            baseline_med = float(bl_row.iloc[0]["NumTotal_median"])
            naive_color = _classify_color_from_actual(naive_q[0.5], baseline_med)
        else:
            naive_color = "green"

        by_horizon[h].append({
            "wis": wis,
            "mae": mae,
            "in_95": in_95,
            "actual": actual,
            "color_correct": 1 if naive_color == r["actual_color"] else 0,
        })

    result = {}
    for h in sorted(by_horizon.keys()):
        entries = by_horizon[h]
        if not entries:
            continue
        total_actual = sum(e["actual"] for e in entries)
        result[str(h)] = {
            "wis": round(np.mean([e["wis"] for e in entries]), 1),
            "mae_pct": round(
                np.mean([e["mae"] for e in entries]) / (total_actual / len(entries)) * 100, 1
            ),
            "coverage_95": round(np.mean([e["in_95"] for e in entries]) * 100, 1),
            "color_accuracy": round(np.mean([e["color_correct"] for e in entries]) * 100, 1),
        }
    return result


def aggregate_metrics(fold_results: list[dict]) -> dict:
    """Aggregate per-week results into metrics by horizon."""
    by_horizon: dict[int, list[dict]] = {}

    for r in fold_results:
        h = r["horizon"]
        if h not in by_horizon:
            by_horizon[h] = []

        actual = r["actual"]
        preds = r["predicted"]

        wis = compute_wis(actual, preds)
        mae = abs(actual - preds.get(0.5, 0))
        lo95 = preds.get(0.025, 0)
        hi95 = preds.get(0.975, 0)
        in_95 = 1 if lo95 <= actual <= hi95 else 0
        color_correct = 1 if r["pred_color"] == r["actual_color"] else 0

        by_horizon[h].append({
            "wis": wis,
            "mae": mae,
            "in_95": in_95,
            "actual": actual,
            "color_correct": color_correct,
        })

    result = {}
    for h in sorted(by_horizon.keys()):
        entries = by_horizon[h]
        if not entries:
            continue
        total_actual = sum(e["actual"] for e in entries)
        mean_actual = total_actual / len(entries) if entries else 1
        result[str(h)] = {
            "wis": round(np.mean([e["wis"] for e in entries]), 1),
            "mae_pct": round(np.mean([e["mae"] for e in entries]) / mean_actual * 100, 1),
            "coverage_95": round(np.mean([e["in_95"] for e in entries]) * 100, 1),
            "color_accuracy": round(np.mean([e["color_correct"] for e in entries]) * 100, 1),
        }
    return result


def validate() -> dict:
    """Run full retrospective validation. Writes validation.json."""
    if not HAS_LGB:
        print("[validate] LightGBM not available -cannot run validation.")
        return {"status": "unavailable"}

    from pipeline.ingest import ingest

    print("[validate] Loading data...")
    national, _regional = ingest()
    print(f"  National rows: {len(national)}")

    all_results = []
    for fold in VALIDATION_FOLDS:
        print(f"\n[validate] Fold: train<={fold['train_end']}, test={fold['test_year']}")
        fold_results = run_fold(national, fold)
        print(f"  Results: {len(fold_results)} predictions")
        all_results.extend(fold_results)

    print(f"\n[validate] Total predictions: {len(all_results)}")

    # Aggregate model metrics
    by_horizon = aggregate_metrics(all_results)

    # Compute naive metrics for comparison
    print("[validate] Computing naive baseline metrics...")
    # Use full baselines for naive comparison
    baselines_df = compute_baselines(national)
    naive_by_horizon = compute_naive_metrics(national, baselines_df, all_results)

    # Compute improvement percentages
    improvement_pct = {}
    for h in by_horizon:
        if h in naive_by_horizon and naive_by_horizon[h]["wis"] > 0:
            imp = (1 - by_horizon[h]["wis"] / naive_by_horizon[h]["wis"]) * 100
            improvement_pct[h] = round(imp, 1)

    output = {
        "folds": len(VALIDATION_FOLDS),
        "test_weeks_total": len(all_results),
        "by_horizon": by_horizon,
        "naive_by_horizon": naive_by_horizon,
        "improvement_pct": improvement_pct,
    }

    # Print summary
    print("\n" + "=" * 60)
    print("VALIDATION RESULTS")
    print("=" * 60)
    for h in sorted(by_horizon.keys()):
        m = by_horizon[h]
        n = naive_by_horizon.get(h, {})
        imp = improvement_pct.get(h, 0)
        print(f"\n  SE+{h}:")
        print(f"    WIS:          {m['wis']:>8.1f}  (naive: {n.get('wis', '?'):>8})")
        print(f"    MAE%:         {m['mae_pct']:>7.1f}%  (naive: {n.get('mae_pct', '?'):>7}%)")
        print(f"    Coverage 95%: {m['coverage_95']:>7.1f}%")
        print(f"    Color acc:    {m['color_accuracy']:>7.1f}%")
        print(f"    WIS improvement: {imp:>+.1f}%")

    # Write output
    DATA_OUTPUT.mkdir(parents=True, exist_ok=True)
    out_path = DATA_OUTPUT / "validation.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    print(f"\n[validate] Written to {out_path}")

    return output


if __name__ == "__main__":
    validate()
