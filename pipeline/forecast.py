"""Produces LightGBM quantile forecasts for national Total respiratory visits."""

import warnings

import numpy as np
import pandas as pd

from pipeline.config import (
    FORECAST_HORIZONS,
    FORECAST_QUANTILES,
    FORECAST_FOURIER_K,
    FORECAST_LAGS,
    FORECAST_LGB_PARAMS,
    FORECAST_EXCLUDE_YEARS,
    FORECAST_CAL_SIZE,
    CHILEAN_HOLIDAY_WEEKS,
)
from pipeline.compute import classify_color, epi_week_date_range

try:
    import lightgbm as lgb
    HAS_LGB = True
except ImportError:
    HAS_LGB = False


def build_ratio_series(national: pd.DataFrame, baselines_df: pd.DataFrame) -> pd.DataFrame:
    """Build ratio series: actual/median with log transform.

    Excludes FORECAST_EXCLUDE_YEARS (COVID distortion) from training data.

    Returns DataFrame with columns:
        Anio, SE, NumTotal, baseline_median, ratio, ratio_t
    """
    total = national[national["Causa"] == "Total"][["Anio", "SE", "NumTotal"]].copy()

    # Exclude COVID years from training data
    total = total[~total["Anio"].isin(FORECAST_EXCLUDE_YEARS)]
    total = total.sort_values(["Anio", "SE"]).reset_index(drop=True)

    # Get baseline medians for Total cause
    bl = baselines_df[baselines_df["Causa"] == "Total"][["SE", "NumTotal_median"]].copy()
    bl = bl.rename(columns={"NumTotal_median": "baseline_median"})

    # SE 53 maps to SE 1 for baseline lookup
    total["_bl_se"] = total["SE"].apply(lambda x: 1 if x == 53 else x)
    total = total.merge(bl, left_on="_bl_se", right_on="SE", suffixes=("", "_bl"))
    total = total.drop(columns=["SE_bl", "_bl_se"])

    # Compute ratio and log transform
    total["ratio"] = total["NumTotal"] / total["baseline_median"].replace(0, np.nan)
    total["ratio_t"] = total["ratio"].apply(lambda x: np.log(x) if pd.notna(x) and x > 0 else np.nan)

    return total.dropna(subset=["ratio_t"]).reset_index(drop=True)


def build_features(ratio_series: pd.DataFrame) -> pd.DataFrame:
    """Build feature matrix for LightGBM.

    Features: lag_1..lag_4, sin_1..cos_K, week_of_year, is_holiday
    Target: ratio_t
    """
    df = ratio_series.copy()

    # Lag features
    for lag in FORECAST_LAGS:
        df[f"lag_{lag}"] = df["ratio_t"].shift(lag)

    # Fourier features (period = 52)
    for k in range(1, FORECAST_FOURIER_K + 1):
        df[f"sin_{k}"] = np.sin(2 * np.pi * k * df["SE"] / 52)
        df[f"cos_{k}"] = np.cos(2 * np.pi * k * df["SE"] / 52)

    # Calendar features
    df["week_of_year"] = df["SE"]
    df["is_holiday"] = df["SE"].isin(CHILEAN_HOLIDAY_WEEKS).astype(int)

    # Drop rows with NaN from lags
    max_lag = max(FORECAST_LAGS)
    df = df.iloc[max_lag:].reset_index(drop=True)

    return df


def get_feature_columns() -> list[str]:
    """Return the list of feature column names."""
    cols = [f"lag_{lag}" for lag in FORECAST_LAGS]
    for k in range(1, FORECAST_FOURIER_K + 1):
        cols.extend([f"sin_{k}", f"cos_{k}"])
    cols.extend(["week_of_year", "is_holiday"])
    return cols


def estimate_exceedance_prob(
    quantile_values: list[float],
    quantile_levels: list[float],
    threshold: float,
) -> float:
    """Estimate P(X > threshold) via linear interpolation between quantiles.

    Args:
        quantile_values: predicted values at each quantile level (ascending)
        quantile_levels: the quantile levels (e.g. [0.025, 0.1, ..., 0.975])
        threshold: the value to compute exceedance probability for

    Returns:
        Estimated probability that X exceeds threshold (0 to 1).
    """
    if threshold <= quantile_values[0]:
        return 1.0 - quantile_levels[0]
    if threshold >= quantile_values[-1]:
        return 1.0 - quantile_levels[-1]

    # Find the interval containing threshold
    for i in range(len(quantile_values) - 1):
        if quantile_values[i] <= threshold <= quantile_values[i + 1]:
            # Linear interpolation
            frac = (threshold - quantile_values[i]) / (quantile_values[i + 1] - quantile_values[i])
            cdf_at_threshold = quantile_levels[i] + frac * (quantile_levels[i + 1] - quantile_levels[i])
            return 1.0 - cdf_at_threshold

    return 0.0


def _next_week(year: int, week: int) -> tuple[int, int]:
    """Advance by one epidemiological week."""
    if week >= 53:
        return year + 1, 1
    return year, week + 1


def _cqr_calibrate(
    X_shifted: np.ndarray,
    y_shifted: np.ndarray,
    X_pred: np.ndarray,
    cal_size: int,
) -> dict[float, float]:
    """Train with CQR (Conformalized Quantile Regression).

    1. Train calibration models on data[:-cal_size]
    2. Compute nonconformity scores on data[-cal_size:]
    3. Train production models on all data
    4. Predict with corrections applied

    Returns dict mapping quantile level -> corrected prediction (in ratio_t space).
    """
    n = len(X_shifted)
    cal_size = min(cal_size, n // 5)  # at most 20% for calibration
    if cal_size < 10:
        # Not enough data for calibration -fall back to raw predictions
        raw_preds = {}
        for q in FORECAST_QUANTILES:
            params = dict(FORECAST_LGB_PARAMS)
            params["objective"] = "quantile"
            params["alpha"] = q
            model = lgb.LGBMRegressor(**params)
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                model.fit(X_shifted, y_shifted)
                raw_preds[q] = model.predict(X_pred)[0]
        return raw_preds

    X_train, X_cal = X_shifted[:-cal_size], X_shifted[-cal_size:]
    y_train, y_cal = y_shifted[:-cal_size], y_shifted[-cal_size:]

    # Step 1: Train calibration models and predict on calibration set
    cal_preds = {}
    for q in FORECAST_QUANTILES:
        params = dict(FORECAST_LGB_PARAMS)
        params["objective"] = "quantile"
        params["alpha"] = q
        model = lgb.LGBMRegressor(**params)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            model.fit(X_train, y_train)
            cal_preds[q] = model.predict(X_cal)

    # Step 2: Compute CQR corrections per interval
    # Interval pairs: (lower_q, upper_q, alpha)
    interval_pairs = [
        (0.025, 0.975, 0.05),
        (0.1, 0.9, 0.20),
        (0.25, 0.75, 0.50),
    ]
    corrections = {}
    for q_lo, q_hi, alpha in interval_pairs:
        scores = np.maximum(cal_preds[q_lo] - y_cal, y_cal - cal_preds[q_hi])
        q_level = min((1 - alpha) * (1 + 1 / len(scores)), 1.0)
        corrections[(q_lo, q_hi)] = float(np.quantile(scores, q_level))

    # Step 3: Train production models on all data
    prod_preds = {}
    for q in FORECAST_QUANTILES:
        params = dict(FORECAST_LGB_PARAMS)
        params["objective"] = "quantile"
        params["alpha"] = q
        model = lgb.LGBMRegressor(**params)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            model.fit(X_shifted, y_shifted)
            prod_preds[q] = model.predict(X_pred)[0]

    # Step 4: Apply corrections (widen intervals)
    for q_lo, q_hi, _alpha in interval_pairs:
        c = corrections[(q_lo, q_hi)]
        prod_preds[q_lo] -= c
        prod_preds[q_hi] += c

    return prod_preds


def train_and_predict(
    features_df: pd.DataFrame,
    baselines_df: pd.DataFrame,
    current_year: int,
    current_week: int,
) -> list[dict]:
    """Train quantile LGBMs per horizon and predict next 4 weeks.

    Uses CQR (Conformalized Quantile Regression) for calibrated intervals.
    Returns list of 4 horizon dicts.
    """
    feature_cols = get_feature_columns()
    X = features_df[feature_cols].values
    y = features_df["ratio_t"].values

    # Get baseline medians for future weeks
    bl_total = baselines_df[baselines_df["Causa"] == "Total"].set_index("SE")["NumTotal_median"]

    horizons = []
    yr, wk = current_year, current_week

    for h in FORECAST_HORIZONS:
        yr, wk = _next_week(yr, wk) if h == 1 else _next_week(*horizons[-1]["_yw"])
        bl_se = 1 if wk == 53 else wk
        baseline_med = float(bl_total.get(bl_se, bl_total.median()))

        # Shift target for direct forecasting
        y_shifted = y[:-h] if h > 0 else y
        X_shifted = X[:len(y_shifted)]

        if len(X_shifted) < 30:
            continue

        # Train with CQR calibration
        quantile_preds_t = _cqr_calibrate(
            X_shifted, y_shifted, X[[-1]], FORECAST_CAL_SIZE,
        )

        # Inverse transform: ratio = exp(ratio_t), clamped for safety
        quantile_preds = {}
        for q in FORECAST_QUANTILES:
            ratio_t = quantile_preds_t[q]
            ratio = np.exp(min(ratio_t, 10))
            value = ratio * baseline_med
            quantile_preds[q] = {"ratio_t": ratio_t, "ratio": ratio, "value": value}

        q_values = [quantile_preds[q]["ratio"] for q in FORECAST_QUANTILES]
        q_levels = list(FORECAST_QUANTILES)

        proj = round(quantile_preds[0.5]["value"])
        lo95 = round(quantile_preds[0.025]["value"])
        hi95 = round(quantile_preds[0.975]["value"])
        lo50 = round(quantile_preds[0.25]["value"])
        hi50 = round(quantile_preds[0.75]["value"])

        # Color from median projection
        change_pct = (quantile_preds[0.5]["ratio"] - 1) * 100
        color = classify_color(change_pct)

        # Exceedance probabilities (ratio > 1.25 = orange, ratio > 1.50 = red)
        p_orange = estimate_exceedance_prob(q_values, q_levels, 1.25)
        p_red = estimate_exceedance_prob(q_values, q_levels, 1.50)

        horizon_data = {
            "horizon": h,
            "year": yr,
            "week": wk,
            "date_range": epi_week_date_range(yr, wk),
            "proj": proj,
            "lo95": lo95,
            "hi95": hi95,
            "lo50": lo50,
            "hi50": hi50,
            "color": color,
            "p_orange": round(p_orange, 3),
            "p_red": round(p_red, 3),
            "_yw": (yr, wk),
        }
        horizons.append(horizon_data)

    # Remove internal _yw field
    for h in horizons:
        h.pop("_yw", None)

    return horizons


def forecast(
    national: pd.DataFrame,
    baselines_df: pd.DataFrame,
    alert_json: dict,
) -> dict:
    """Main forecast entry point.

    Returns forecast dict with current_year, current_week, horizons[].
    Graceful fallback if lightgbm is not available.
    """
    if not HAS_LGB:
        print("[forecast] LightGBM not available -skipping forecast.")
        return {"status": "unavailable", "horizons": []}

    current = alert_json.get("current")
    if current is None:
        return {"status": "no_current_data", "horizons": []}

    current_year = current["year"]
    current_week = current["week"]

    print(f"[forecast] Building forecast for SE {current_week}/{current_year}...")

    try:
        ratio_series = build_ratio_series(national, baselines_df)
        print(f"  Ratio series: {len(ratio_series)} rows")

        features_df = build_features(ratio_series)
        print(f"  Feature matrix: {len(features_df)} rows × {len(get_feature_columns())} features")

        horizons = train_and_predict(features_df, baselines_df, current_year, current_week)
        print(f"  Horizons generated: {len(horizons)}")

        for h in horizons:
            print(f"    SE+{h['horizon']}: {h['proj']:,} proj · {h['color']} · "
                  f"P(orange)={h['p_orange']:.1%} · P(red)={h['p_red']:.1%}")

        return {
            "status": "ok",
            "current_year": current_year,
            "current_week": current_week,
            "horizons": horizons,
        }
    except Exception as e:
        import traceback; traceback.print_exc()
        print(f"[forecast] Error: {e}")
        return {"status": "error", "error": str(e), "horizons": []}
