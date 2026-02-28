<div align="center">

# Semáforo Respiratorio Chile

**Dashboard de vigilancia epidemiológica de urgencias respiratorias en las 16 regiones de Chile con clasificación de alertas, detección de anomalías y pronósticos semanales.**

[![Python](https://img.shields.io/badge/Python-3.11-3776ab?logo=python&logoColor=white)](https://www.python.org)
[![React](https://img.shields.io/badge/React-19-61dafb?logo=react&logoColor=white)](https://react.dev)
[![TypeScript](https://img.shields.io/badge/TypeScript-5-blue?logo=typescript&logoColor=white)](https://www.typescriptlang.org)
[![Vite](https://img.shields.io/badge/Vite-6-646CFF?logo=vite&logoColor=white)](https://vite.dev)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind-4-06B6D4?logo=tailwindcss&logoColor=white)](https://tailwindcss.com)
[![Recharts](https://img.shields.io/badge/Recharts-2-8884d8)](https://recharts.org)
[![Pytest](https://img.shields.io/badge/Pytest-99_tests-0A9EDC?logo=pytest&logoColor=white)](https://docs.pytest.org)

[English](README.md)

</div>

---

## Overview

Dashboard de vigilancia que monitorea urgencias respiratorias en Chile usando datos públicos DEIS/MINSAL. Un pipeline en Python descarga ~61 MB de datos parquet semanalmente, calcula líneas base históricas, clasifica niveles de alerta por región, detecta anomalías estadísticas (EARS C2 + mix shift) y genera pronósticos a 4 semanas con LightGBM y calibración conformal.

## Features

- **Sistema de alerta en 4 niveles** - verde, amarillo, naranjo, rojo según % de desviación sobre la mediana histórica
- **16 regiones + vista nacional** - selector de región con datos de alerta individuales
- **Tendencia semanal** - comparación multi-año con banda de referencia (IQR)
- **Pronóstico a 4 semanas** - regresión cuantílica LightGBM con intervalos de confianza al 50% y 95%
- **Detección de anomalías** - EARS C2 (excesos de volumen) + mix shift (cambio en composición de causas)
- **Desglose por causa** - 8 causas diagnósticas con razón observado/esperado y z-scores
- **Grupos etarios** - 5 grupos con indicadores de variación
- **Heatmap** - z-scores semanales por causa
- **Composición por causa** - z-scores por causa en el tiempo con umbral estadístico

## Installation

**Requisitos:** Python 3.11+, Node.js >= 22

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
# Ejecutar pipeline de datos
python -m pipeline.run

# Servidor de desarrollo
cd frontend
npm run dev          # http://localhost:5173

# Build de producción
npm run build        # tsc + vite build -> dist/
npm run preview      # preview del build
```

## Project Structure

```
pipeline/
├── config.py .................. Umbrales, causas, regiones, parámetros de forecast
├── ingest.py .................. Descarga parquet, normaliza causas, separa nacional/regional
├── compute.py ................. Líneas base (mediana histórica), clasificación de alertas
├── anomalies.py ............... EARS C2 + mix shift
├── forecast.py ................ LightGBM regresión cuantílica + calibración CQR
├── validate.py ................ Validación retrospectiva (3 folds, WIS, cobertura)
└── run.py ..................... Orquestador - nacional + 16 regiones -> JSON

frontend/src/
├── components/
│   ├── layout/
│   │   ├── AppHeader.tsx ...... Encabezado
│   │   ├── Dashboard.tsx ...... Layout principal
│   │   ├── StatusBanner.tsx ... Banner de nivel de alerta
│   │   └── RegionPicker.tsx ... Selector de región
│   ├── sections/
│   │   ├── KPIRow.tsx ......... Métricas clave: total, variación, O/E, z-score
│   │   ├── CausesSection.tsx .. Layout: tabla de causas + grupos etarios + regiones
│   │   ├── CausesTable.tsx .... Tabla de causas diagnósticas
│   │   ├── AgeGroupPanel.tsx .. Desglose por grupo etario
│   │   ├── RegionLevelSummary.tsx  Conteo de regiones por nivel
│   │   ├── TrendSection.tsx ... Layout: tendencia + proyección
│   │   ├── WeeklyTrendCard.tsx  Gráfico de tendencia multi-año
│   │   ├── ProjectionCard.tsx . Gráfico de pronóstico con intervalos
│   │   ├── ForecastCards.tsx .. Tarjetas de horizonte con probabilidades
│   │   ├── CompositionPanel.tsx  Z-scores por causa en el tiempo
│   │   ├── HeatmapPanel.tsx ... Heatmap de z-scores por causa
│   │   ├── FreshnessStrip.tsx . Última semana epidemiológica disponible
│   │   └── MethodologyPanel.tsx  Notas metodológicas
│   └── ui/
│       ├── Card.tsx ........... Contenedor base
│       ├── ChartTooltip.tsx ... Tooltip de gráficos
│       ├── ChartLegend.tsx .... Leyenda de gráficos
│       ├── ScrollArea.tsx ..... Scroll area
│       ├── Collapsible.tsx .... Sección expandible
│       ├── LevelDot.tsx ....... Indicador de nivel de alerta
│       ├── TrendBadge.tsx ..... Indicador de tendencia
│       ├── VariationBadge.tsx . Variación porcentual
│       ├── Caption.tsx ........ Texto secundario
│       └── SectionTitle.tsx ... Título de sección
├── hooks/
│   ├── useAlertData.ts ........ Fetch de datos de alerta y forecast
│   └── useRegionParam.ts ...... Sync de región en URL
├── lib/
│   ├── api.ts ................. Fetch y parsing de datos
│   ├── types.ts ............... Interfaces TypeScript
│   ├── colors.ts .............. Colores de alerta y palette
│   ├── chart-theme.ts ......... Configuración compartida de ejes y grilla
│   ├── data-transforms.ts ..... Transformaciones de datos para gráficos
│   ├── format.ts .............. Formateo de números (es-CL)
│   └── utils.ts ............... cn() - clsx + tailwind-merge
└── styles/
    └── global.css ............. Tailwind, tokens, color-scheme

tests/ ......................... 99 tests (pytest)
data/output/ ................... JSONs generados (output del pipeline)
.github/workflows/ ............. CI/CD (update.yml)
```

## Testing

```bash
python -m pytest tests/ -v    # 99 tests
```

## Pipeline

| Paso | Módulo | Descripción | Output |
|------|--------|-------------|--------|
| 1 | `ingest.py` | Descarga parquet, normaliza causas, separa nacional/regional | DataFrame |
| 2 | `compute.py` | Líneas base (52 SE x 8 causas), clasificación de alertas | `baselines.json`, `alert.json` |
| 3 | `anomalies.py` | EARS C2 (exceso estadístico) + mix shift (cambio de composición) | `anomalies.json` |
| 4 | `forecast.py` | LightGBM regresión cuantílica (4 horizontes x 7 cuantiles, CQR) | `forecast.json` |
| 5 | `run.py` | Orquesta pasos 1-4, procesa 16 regiones, genera snapshot | `latest.json`, `regions/` |

## Alert System

| Nivel | Umbral (% vs mediana) | Color |
|-------|------------------------|-------|
| Verde | < +10% | `#007F3B` |
| Amarillo | +10% a +25% | `#FFB81C` |
| Naranjo | +25% a +50% | `#ED8B00` |
| Rojo | >= +50% | `#D5281B` |

Años de referencia y umbrales configurados en `pipeline/config.py`.

## Output Files

| Archivo | Descripción |
|---------|-------------|
| `alert.json` | Semana actual + serie temporal con niveles de alerta |
| `baselines.json` | Mediana, IQR y P90 por semana epidemiológica y causa |
| `anomalies.json` | Eventos EARS C2 y mix shift |
| `forecast.json` | 4 horizontes con cuantiles + P(naranjo) / P(rojo) |
| `latest.json` | Snapshot semana actual + pronóstico próxima semana |
| `validation.json` | Validación cruzada (3 folds, WIS, cobertura) |
| `regions/index.json` | Índice de 16 regiones con estado actual |
| `regions/{code}/` | baselines + alert + anomalies por región |

## CI/CD

Workflow: `.github/workflows/update.yml`

- **Cron:** Lunes 12:00 UTC (08:00 Chile)
- **Pipeline job:** checkout -> pytest -> `pipeline.run` -> commit `data/output/`
- **Deploy job:** checkout -> pull datos frescos -> `npm ci` -> build -> GitHub Pages
- **Dispatch manual** disponible

## Data

**8 causas canónicas:**
Total, Influenza, COVID-19, Neumonía, IRA Alta, Bronquitis, Obstructiva, Otra resp.

**5 grupos etarios:**
<1 año, 1-4, 5-14, 15-64, 65+

**16 regiones:**
Arica y Parinacota, Tarapacá, Antofagasta, Atacama, Coquimbo, Valparaíso, Metropolitana, O'Higgins, Maule, Ñuble, Biobío, Araucanía, Los Ríos, Los Lagos, Aysén, Magallanes

---

**Disclaimer:** Este dashboard es una herramienta informativa y no constituye consejo médico. Fuente: SADU / DEIS / MINSAL · [datos.gob.cl](https://datos.gob.cl).

## License

[MIT](LICENSE)

## Author

**agonzalezlevio** - [github.com/agonzalezlevio](https://github.com/agonzalezlevio)
