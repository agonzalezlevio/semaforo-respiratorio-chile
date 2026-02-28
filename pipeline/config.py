"""Central configuration for the respiratory surveillance alert pipeline."""

from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_RAW = ROOT_DIR / "data" / "raw"
DATA_OUTPUT = ROOT_DIR / "data" / "output"
REGIONS_OUTPUT = DATA_OUTPUT / "regions"
PARQUET_PATH = DATA_RAW / "at_urg_respiratorio_semanal.parquet"

SADU_URL = (
    "https://datos.gob.cl/dataset/606ef5bb-11d1-475b-b69f-b980da5757f4"
    "/resource/ae6c9887-106d-4e98-8875-40bf2b836041"
    "/download/at_urg_respiratorio_semanal.parquet"
)

# Prefix-based to handle encoding corruption (ñ/í -> 0xED->0xCD in Parquet)
CAUSE_MAP = {
    "TOTAL CAUSA SISTEMA RESPIRATORIO": "Total",
    "IRA ALTA": "IRA Alta",
    "INFLUENZA": "Influenza",
    "TOTAL ATENCIONES POR COVID": "COVID-19",
    "- POR COVID": "COVID-19",
    "NEUMON": "Neumonía",
    "BRONQUITIS": "Bronquitis",
    "CRISIS OBSTRUCTIVA": "Obstructiva",
    "- CAUSAS SISTEMA RESPIRATORIO": "_subtotal",
}

CANONICAL_CAUSES = [
    "Total", "Influenza", "COVID-19", "Neumonía",
    "IRA Alta", "Bronquitis", "Obstructiva", "Otra resp.",
]

AGE_COLUMNS = {
    "NumMenor1Anio": "<1 año",
    "Num1a4Anios": "1-4 años",
    "Num5a14Anios": "5-14 años",
    "Num15a64Anios": "15-64 años",
    "Num65oMas": "65+ años",
}

# % change vs median: <10% green, 10-25% yellow, 25-50% orange, >=50% red
COLOR_THRESHOLDS = {
    "green": 10,
    "yellow": 25,
    "orange": 50,
}

REFERENCE_YEARS = [2017, 2018, 2019, 2022, 2023]

EARS_WINDOW = 7
EARS_GUARD = 2
EARS_THRESHOLD = 2.0

MIX_Z_THRESHOLD = 1.8
MIX_SHARE_THRESHOLD = 0.03

FORECAST_HORIZONS = [1, 2, 3, 4]
FORECAST_QUANTILES = [0.025, 0.1, 0.25, 0.5, 0.75, 0.9, 0.975]
FORECAST_FOURIER_K = 3
FORECAST_LAGS = [1, 2, 3, 4]
FORECAST_LGB_PARAMS = {
    "n_estimators": 200,
    "max_depth": 6,
    "learning_rate": 0.05,
    "min_child_samples": 20,
    "verbose": -1,
}
CHILEAN_HOLIDAY_WEEKS = [1, 38, 39, 51, 52]

REGION_MAP = {
    1: "Tarapacá",
    2: "Antofagasta",
    3: "Atacama",
    4: "Coquimbo",
    5: "Valparaíso",
    6: "O'Higgins",
    7: "Maule",
    8: "Biobío",
    9: "Araucanía",
    10: "Los Lagos",
    11: "Aysén",
    12: "Magallanes",
    13: "Metropolitana",
    14: "Los Ríos",
    15: "Arica y Parinacota",
    16: "Ñuble",
}

FORECAST_EXCLUDE_YEARS = [2020, 2021]
FORECAST_CAL_SIZE = 52

VALIDATION_FOLDS = [
    {"train_end": 2022, "test_year": 2023},
    {"train_end": 2023, "test_year": 2024},
    {"train_end": 2024, "test_year": 2025},
]
VALIDATION_MIN_TRAIN_ROWS = 100
