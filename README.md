<div align="center">

# Semáforo Respiratorio Chile

**Epidemiological dashboard for respiratory emergency visits across Chile's 16 regions with alert classification, anomaly detection, and weekly forecasts.**

[![Python](https://img.shields.io/badge/Python-3.11-3776ab?logo=python&logoColor=white)](https://www.python.org)
[![React](https://img.shields.io/badge/React-19-61dafb?logo=react&logoColor=white)](https://react.dev)
[![TypeScript](https://img.shields.io/badge/TypeScript-5-blue?logo=typescript&logoColor=white)](https://www.typescriptlang.org)
[![Vite](https://img.shields.io/badge/Vite-6-646CFF?logo=vite&logoColor=white)](https://vite.dev)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind-4-06B6D4?logo=tailwindcss&logoColor=white)](https://tailwindcss.com)
[![Recharts](https://img.shields.io/badge/Recharts-2-8884d8)](https://recharts.org)
[![Pytest](https://img.shields.io/badge/Pytest-99_tests-0A9EDC?logo=pytest&logoColor=white)](https://docs.pytest.org)

[Español](README.es.md)

</div>

---

## Overview

Surveillance dashboard that monitors respiratory emergency visits across Chile using public DEIS/MINSAL data. A Python pipeline downloads ~61 MB of parquet data weekly, computes historical baselines, classifies alert levels per region, detects statistical anomalies (EARS C2 + mix shift), and generates 4-week forecasts with LightGBM quantile regression and conformal calibration.

## Features

- **4-level alert system** - green, yellow, orange, red based on % deviation from historical median
- **16 regions + national view** - region picker with per-region alert data
- **Weekly trend charts** - multi-year comparison with reference band (IQR)
- **4-week forecasts** - LightGBM quantile regression with 50% and 95% confidence intervals
- **Anomaly detection** - EARS C2 (volume spikes) + mix shift (cause composition changes)
- **Cause breakdown** - 8 diagnostic causes with observed/expected ratios and z-scores
- **Age group analysis** - 5 groups with variation indicators
- **Heatmap** - weekly z-scores by cause
- **Composition chart** - cause-level z-scores over time with statistical threshold

## Installation

**Prerequisites:** Python 3.11+, Node.js >= 22

```bash
git clone https://github.com/agonzalezlevio/semaforo
cd semaforo
```

### Pipeline

```bash
pip install -r requirements.txt
python -m pipeline.run
```

### Frontend

```bash
cd frontend
npm install
```

## Usage

```bash
# Run the data pipeline
python -m pipeline.run

# Start the dev server
cd frontend
npm run dev          # http://localhost:5173

# Production build
npm run build        # tsc + vite build -> dist/
npm run preview      # preview the production build
```

## Project Structure

```
pipeline/
├── config.py .................. Thresholds, causes, regions, forecast params
├── ingest.py .................. Download parquet, normalize causes, split national/regional
├── compute.py ................. Baselines (historical median), alert classification
├── anomalies.py ............... EARS C2 + mix shift
├── forecast.py ................ LightGBM quantile regression + CQR calibration
├── validate.py ................ Retrospective validation (3 folds, WIS, coverage)
└── run.py ..................... Orchestrator - national + 16 regions -> JSON

frontend/src/
├── components/
│   ├── layout/
│   │   ├── AppHeader.tsx ...... Header
│   │   ├── Dashboard.tsx ...... Main layout
│   │   ├── StatusBanner.tsx ... Alert level banner
│   │   └── RegionPicker.tsx ... Region selector
│   ├── sections/
│   │   ├── KPIRow.tsx ......... Key metrics: total, variation, O/E, z-score
│   │   ├── CausesSection.tsx .. Layout: causes table + age groups + regions
│   │   ├── CausesTable.tsx .... Diagnostic causes table
│   │   ├── AgeGroupPanel.tsx .. Age group breakdown
│   │   ├── RegionLevelSummary.tsx  Region count per alert level
│   │   ├── TrendSection.tsx ... Layout: weekly trend + projection
│   │   ├── WeeklyTrendCard.tsx  Multi-year trend chart
│   │   ├── ProjectionCard.tsx . Forecast chart with confidence intervals
│   │   ├── ForecastCards.tsx .. Forecast horizon cards with alert probabilities
│   │   ├── CompositionPanel.tsx  Cause z-scores over time
│   │   ├── HeatmapPanel.tsx ... Z-score heatmap by cause
│   │   ├── FreshnessStrip.tsx . Last available epi week
│   │   └── MethodologyPanel.tsx  Methodology notes
│   └── ui/
│       ├── Card.tsx ........... Base container
│       ├── ChartTooltip.tsx ... Chart tooltip
│       ├── ChartLegend.tsx .... Chart legend
│       ├── ScrollArea.tsx ..... Scroll area
│       ├── Collapsible.tsx .... Expandable section
│       ├── LevelDot.tsx ....... Alert level indicator
│       ├── TrendBadge.tsx ..... Trend indicator
│       ├── VariationBadge.tsx . Percentage variation
│       ├── Caption.tsx ........ Secondary text
│       └── SectionTitle.tsx ... Section heading
├── hooks/
│   ├── useAlertData.ts ........ Fetch alert + forecast data
│   └── useRegionParam.ts ...... URL region param sync
├── lib/
│   ├── api.ts ................. Data fetching and parsing
│   ├── types.ts ............... TypeScript interfaces
│   ├── colors.ts .............. Alert colors and palette
│   ├── chart-theme.ts ......... Shared axis/grid config
│   ├── data-transforms.ts ..... Chart data transforms
│   ├── format.ts .............. Number formatting (es-CL)
│   └── utils.ts ............... cn() - clsx + tailwind-merge
└── styles/
    └── global.css ............. Tailwind, tokens, color-scheme

tests/ ......................... 99 tests (pytest)
data/output/ ................... Generated JSONs (pipeline output)
.github/workflows/ ............. CI/CD (update.yml)
```

## Testing

```bash
python -m pytest tests/ -v    # 99 tests
```

## Pipeline

| Step | Module | Description | Output |
|------|--------|-------------|--------|
| 1 | `ingest.py` | Download parquet, normalize causes, split national/regional | DataFrame |
| 2 | `compute.py` | Baselines (52 epi-weeks x 8 causes), alert classification | `baselines.json`, `alert.json` |
| 3 | `anomalies.py` | EARS C2 (statistical excess) + mix shift (composition change) | `anomalies.json` |
| 4 | `forecast.py` | LightGBM quantile regression (4 horizons x 7 quantiles, CQR) | `forecast.json` |
| 5 | `run.py` | Orchestrates steps 1-4, processes 16 regions, generates snapshot | `latest.json`, `regions/` |

## Alert System

| Level | Threshold (% vs median) | Color |
|-------|-------------------------|-------|
| Green | < +10% | `#007F3B` |
| Yellow | +10% to +25% | `#FFB81C` |
| Orange | +25% to +50% | `#ED8B00` |
| Red | >= +50% | `#D5281B` |

Reference years and thresholds configured in `pipeline/config.py`.

## Output Files

| File | Description |
|------|-------------|
| `alert.json` | Current week + time series with alert levels |
| `baselines.json` | Median, IQR and P90 per epi-week and cause |
| `anomalies.json` | EARS C2 and mix shift events |
| `forecast.json` | 4 horizons with quantiles + P(orange) / P(red) |
| `latest.json` | Current week snapshot + next-week forecast |
| `validation.json` | Cross-validation results (3 folds, WIS, coverage) |
| `regions/index.json` | Index of 16 regions with current status |
| `regions/{code}/` | baselines + alert + anomalies per region |

## CI/CD

Workflow: `.github/workflows/update.yml`

- **Cron:** Monday 12:00 UTC (08:00 Chile)
- **Pipeline job:** checkout -> pytest -> `pipeline.run` -> commit `data/output/`
- **Deploy job:** checkout -> pull fresh data -> `npm ci` -> build -> GitHub Pages
- **Manual dispatch** available

## Data

**8 canonical causes:**
Total, Influenza, COVID-19, Pneumonia, Upper ARI, Bronchitis, Obstructive, Other resp.

**5 age groups:**
<1 year, 1-4, 5-14, 15-64, 65+

**16 regions:**
Arica y Parinacota, Tarapacá, Antofagasta, Atacama, Coquimbo, Valparaíso, Metropolitana, O'Higgins, Maule, Ñuble, Biobío, Araucanía, Los Ríos, Los Lagos, Aysén, Magallanes

---

**Disclaimer:** This dashboard is an informational tool and does not constitute medical advice. Data source: SADU / DEIS / MINSAL · [datos.gob.cl](https://datos.gob.cl).

## License

[MIT](LICENSE)

## Author

**agonzalezlevio** - [github.com/agonzalezlevio](https://github.com/agonzalezlevio)
