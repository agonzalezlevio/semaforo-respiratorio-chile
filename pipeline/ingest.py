"""Download SADU Parquet, normalize causes, and aggregate to national level."""

import re

import pandas as pd
import requests

from pipeline.config import (
    AGE_COLUMNS,
    CAUSE_MAP,
    DATA_RAW,
    PARQUET_PATH,
    SADU_URL,
)


def download_parquet(force: bool = False) -> None:
    """Download the SADU Parquet file. Skips if already cached unless force=True."""
    if PARQUET_PATH.exists() and not force:
        print(f"  Parquet already cached at {PARQUET_PATH}")
        return
    DATA_RAW.mkdir(parents=True, exist_ok=True)
    print(f"  Downloading from {SADU_URL} ...")
    resp = requests.get(SADU_URL, stream=True, timeout=120)
    resp.raise_for_status()
    with open(PARQUET_PATH, "wb") as f:
        for chunk in resp.iter_content(chunk_size=1024 * 1024):
            f.write(chunk)
    size_mb = PARQUET_PATH.stat().st_size / (1024 * 1024)
    print(f"  Downloaded {size_mb:.1f} MB")


def normalize_cause(text: str) -> str:
    """Strip whitespace and collapse multiple spaces into one."""
    if not isinstance(text, str):
        return str(text)
    return re.sub(r"\s+", " ", text.strip())


def map_cause(cause_raw: str) -> str:
    """Map a raw cause string to a canonical name via prefix matching."""
    upper = cause_raw.upper()
    for prefix, canonical in CAUSE_MAP.items():
        if upper.startswith(prefix):
            return canonical
    return "Otra resp."


def aggregate_national(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate establishment-level data to national totals per (Anio, SE, Causa)."""
    agg_cols = {"NumTotal": "sum"}
    for col in AGE_COLUMNS:
        if col in df.columns:
            agg_cols[col] = "sum"

    national = (
        df.groupby(["Anio", "SE", "Causa"], as_index=False)
        .agg(agg_cols)
    )
    return national


def aggregate_regional(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate establishment-level data to regional totals per (RegionCodigo, Anio, SE, Causa)."""
    # Drop rows without a region code
    regional = df.dropna(subset=["RegionCodigo"]).copy()
    regional["RegionCodigo"] = regional["RegionCodigo"].astype(int)

    agg_cols = {"NumTotal": "sum"}
    for col in AGE_COLUMNS:
        if col in regional.columns:
            agg_cols[col] = "sum"

    regional = (
        regional.groupby(["RegionCodigo", "Anio", "SE", "Causa"], as_index=False)
        .agg(agg_cols)
    )
    return regional


def ingest() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Full ingestion pipeline: download -> normalize -> map -> aggregate.

    Returns (national, regional) DataFrames.
    """
    print("[ingest] Starting ingestion...")
    download_parquet()

    print("  Reading Parquet...")
    df = pd.read_parquet(PARQUET_PATH)
    print(f"  Raw rows: {len(df):,}")

    # Normalize the Causa column and drop subtotal rows
    df["Causa"] = df["Causa"].apply(normalize_cause).apply(map_cause)
    df = df[df["Causa"] != "_subtotal"]

    # Rename SE column for consistency
    if "SemanaEstadistica" in df.columns:
        df = df.rename(columns={"SemanaEstadistica": "SE"})

    # Aggregate to national level
    national = aggregate_national(df)
    print(f"  National rows: {len(national):,}")
    print(f"  Years: {sorted(national['Anio'].unique())}")
    print(f"  Causes: {sorted(national['Causa'].unique())}")

    # Aggregate to regional level
    regional = aggregate_regional(df)
    print(f"  Regional rows: {len(regional):,}")
    region_codes = sorted(regional["RegionCodigo"].unique())
    print(f"  Regions: {len(region_codes)} ({region_codes})")

    print("[ingest] Done.")
    return national, regional


if __name__ == "__main__":
    national, regional = ingest()
    print("\n--- National Summary ---")
    print(national.groupby("Causa")["NumTotal"].sum().sort_values(ascending=False))
    print(f"\n--- Regional Summary ---")
    print(f"Regions: {sorted(regional['RegionCodigo'].unique())}")
    print(regional.groupby("RegionCodigo")["NumTotal"].sum().sort_values(ascending=False))
