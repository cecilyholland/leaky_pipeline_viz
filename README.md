# The Leaky Pipeline: Women in Tech

A data visualization project exploring women's representation in tech - from education through workforce, and the growing data gap that makes measurement increasingly difficult.

**Course:** CPSC 5530 Data Visualization and Exploration  
Youtube link to presentation: https://www.youtube.com/watch?v=VOf9SW9kf8Y

## Quick Start

```bash
# 1. Set up environment
conda activate plda2

# 2. Download raw data (see Data Sources below)

# 3. Run preprocessing scripts
python ipeds/ipeds_preprocessing.py
python bls/bls_preprocessing.py
python ncses/nscg_preprocessing.py

# 4. Export chart data for embedded dashboard
python visualizations/export_chart_data.py

# 5. View the dashboard (requires local server for JSON loading)
cd visualizations
python -m http.server 8000
# Open http://localhost:8000/index_embedded.html
```

## Project Narrative

Four-act data story exploring the "leaky pipeline":

| Act | Title | Data Source | Key Question |
|-----|-------|-------------|--------------|
| 1 | The Pipeline | IPEDS | How many women enter tech education? |
| 2 | The Cliff | BLS CPS | Where do women leave the workforce? |
| 3 | Intersections | NSF NSCG | Does the cliff affect all women equally? |
| 4 | The Data Gap | Big Tech Reports | Can we even measure progress anymore? |

**Central finding:** Women enter tech education and jobs but leave by ~age 35 ("the cliff"), and the data infrastructure to study this is itself fragmenting as companies stop DEI reporting.

## Interactive Dashboard Features

The embedded dashboard (`visualizations/index_embedded.html`) includes:

### Act 1: Education Pipeline (IPEDS)
- Track comparison mode (e.g., CS vs Cybersecurity)
- Degree level filtering
- Trend lines by degree type

### Act 2: The Age Cliff (BLS)
- Occupation comparison overlay
- Year animation with Play button
- Keyboard shortcuts (arrow keys to change year)
- Value labels toggle

### Act 3: Intersectional View (NSCG)
- Row/column highlighting on hover
- Click cells for detailed breakdown (sample size, margin of error)
- 2019 vs 2023 comparison with change view

### Act 4: The Data Gap (Big Tech)
- Company isolation (click legend to highlight)
- Timeline event annotations (2014 first reports, 2020 BLM, 2024 DEI backlash)
- Trend projections toggle

### Cross-Cutting Features
- CSV download button for each chart
- Guided tour with 9 insight-driven steps
- Responsive design

## Data Sources

### Raw Data (not included - download separately)

| Dataset | Source | Files Location |
|---------|--------|----------------|
| IPEDS | [nces.ed.gov/ipeds](https://nces.ed.gov/ipeds) | `ipeds/ipeds_datasets/c20XX_a.csv` |
| BLS CPS | [bls.gov/cps/tables.htm](https://www.bls.gov/cps/tables.htm) | `bls/bls_datasets/cpsa20XX.xlsx` |
| NSF NSCG | [ncses.nsf.gov](https://ncses.nsf.gov) | `ncses/ncses_datasets/nscg/` |

### Processed Data (included in repo)

| Output | Description |
|--------|-------------|
| `ipeds/processed_ipeds_csv_files/` | National trends by track and degree |
| `bls/processed_bls_data/` | Tech occupations by sex and age |
| `ncses/processed_nscg_data/` | Intersectional analysis by race and age |
| `big_tech_diversity.csv` | FAANG diversity metrics 2014-2024 |
| `visualizations/chart_data/` | JSON exports for embedded dashboard |

## Key Findings

- **Education:** CS Bachelor's: 18.3% women (2010) to 23.8% (2024) - only +5.5pp over 14 years
- **The Cliff:** Software Devs peak at 25-34 age bracket, drop 24% by 35-44
- **Stagnation:** Software Developers went from 17.9% to 20.3% women (2015-2024) - near flat
- **Data Gap:** Google, Meta, Microsoft stopped publishing diversity reports in 2024-2025
- **Intersectionality:** Gray/suppressed cells in NSCG data reveal how few women of certain races exist in computing at certain ages

## Project Structure

```
leaky-pipeline-viz/
|-- bls/
|   |-- bls_preprocessing.py
|   |-- processed_bls_data/
|-- ipeds/
|   |-- ipeds_preprocessing.py
|   |-- processed_ipeds_csv_files/
|-- ncses/
|   |-- nscg_preprocessing.py
|   |-- processed_nscg_data/
|-- visualizations/
|   |-- index_embedded.html      # Main dashboard
|   |-- export_chart_data.py     # JSON exporter
|   |-- chart_data/              # JSON for dashboard
|   |-- chart1_bls_age_cliff.py  # Standalone charts
|   |-- chart2_nscg_intersectional.py
|   |-- chart3_bigtech_timeline.py
|   |-- chart4_ipeds_pipeline.py
|-- big_tech_diversity.csv
|-- README.md
|-- CLAUDE.md                    # AI assistant instructions
```

## Technical Notes

- **Environment:** Conda env `plda2` with pandas, plotly, openpyxl
- **CIPCODE:** Always load with `dtype={"CIPCODE": str}`
- **pct_women:** Use `float("nan")` not `pd.NA` for `.round()` compatibility
- **BLS age data:** `women_count_k_approx` is estimated (bracket total x occupation % women)
- **NSCG suppression:** Cells with n < 20 are suppressed per NCSES guidelines

## Visualizations

### Standalone Charts (Plotly HTML)
```bash
python visualizations/chart1_bls_age_cliff.py
python visualizations/chart2_nscg_intersectional.py
python visualizations/chart3_bigtech_timeline.py
python visualizations/chart4_ipeds_pipeline.py
```

### Embedded Dashboard
```bash
python visualizations/export_chart_data.py
cd visualizations && python -m http.server 8000
# Open http://localhost:8000/index_embedded.html
```

## License

Educational project for CPSC 5530. Data sources are publicly available government datasets and company reports.
