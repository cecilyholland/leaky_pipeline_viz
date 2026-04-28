# Interactive Charts Implementation Plan

## Overview

4 interactive Plotly charts, each saved as standalone HTML:

```
visualizations/
├── chart1_bls_age_cliff.html       # BLS occupation × age × year
├── chart2_nscg_intersectional.html # NSCG race × age × year  
├── chart3_bigtech_timeline.html    # Big Tech companies over time
├── chart4_ipeds_pipeline.html      # IPEDS track × degree × year
└── index.html                      # Dashboard linking all 4
```

---

## Chart 1: BLS Age Cliff (Primary)

### Data Source
`bls/processed_bls_data/bls_combined_clean.csv`

### Chart Type
Animated bar chart or population pyramid

### Layout
```
┌─────────────────────────────────────────────────────────┐
│  Women in Tech by Age: The 35-44 Cliff                  │
│  ┌─────────────────────────────────────────────────┐    │
│  │ Occupation: [Software Developers      ▼]        │    │
│  └─────────────────────────────────────────────────┘    │
│                                                         │
│     16-19  ████                                         │
│     20-24  ████████████                                 │
│     25-34  ████████████████████████████  ← Peak        │
│     35-44  ██████████████████  ← 24% drop              │
│     45-54  ████████████                                 │
│     55-64  ████████                                     │
│       65+  ████                                         │
│                                                         │
│  Year: ●────────────────────────○  [2015 ← → 2024]     │
│                                                         │
│  ▢ Show men for comparison                              │
└─────────────────────────────────────────────────────────┘
```

### Interactive Elements
1. **Dropdown** (`dcc.Dropdown` or `updatemenus`): Select occupation
   - Software Developers
   - Computer Systems Analysts
   - Database Administrators
   - Information Security Analysts
   - Web Developers
   - CS & Math (all)
   
2. **Slider** (`sliders`): Year selection 2015-2024
   - With play/pause animation button
   
3. **Checkbox** (toggle trace): Show/hide men's bars for comparison

4. **Hover**: Show count (thousands), % women, year-over-year change

### Key Annotations
- Arrow pointing to 35-44 bracket: "The Cliff: 24% fewer women than 25-34"
- Text box showing % change from peak bracket

### Colors
- Women: `#E15759` (coral)
- Men (if shown): `#4E79A7` (blue), lower opacity

---

## Chart 2: NSCG Intersectional Heatmap

### Data Source
`ncses/processed_nscg_data/nscg_intersectional_cliff.csv`

### Chart Type
Heatmap with annotations

### Layout
```
┌─────────────────────────────────────────────────────────┐
│  Women in Computing by Race & Age                       │
│  ┌──────────────────────────────────────┐               │
│  │ Year: ○ 2019   ● 2023   ○ Change    │               │
│  └──────────────────────────────────────┘               │
│                                                         │
│           Under25  25-34  35-44  45-54  55-64  65+     │
│  Asian      28%    17%    35%    42%    40%    --      │
│  Black      --     15%    21%    27%    20%    --      │
│  Hispanic   34%    34%    28%    39%    22%    11%     │
│  White      37%    22%    22%    27%    27%    27%     │
│  Multi      --     41%    13%    33%    41%    --      │
│                                                         │
│  [Color scale: 10% ─────────────────── 45%]            │
│                                                         │
│  Gray cells (--) = sample size < 20, suppressed        │
└─────────────────────────────────────────────────────────┘
```

### Interactive Elements
1. **Radio buttons**: Toggle between 2019 / 2023 / Change (Δpp)
   
2. **Hover**: Show:
   - Exact percentage
   - Sample size (n)
   - If "Change" view: 2019 value, 2023 value, delta

3. **Click cell**: Highlight row and column for comparison

### Color Scale
- Main view: Sequential (`Oranges` or `YlOrRd`), higher = more women = darker
- Change view: Diverging (`RdYlGn`), negative = red, positive = green

### Key Annotations
- Title updates based on selection
- Note at bottom: "Cells with n < 20 suppressed per NCSES guidelines"

---

## Chart 3: Big Tech Timeline

### Data Source
`big_tech_diversity.csv`

### Chart Type
Multi-line chart with markers

### Layout
```
┌─────────────────────────────────────────────────────────┐
│  Big Tech Diversity Reporting: The Data Cliff           │
│                                                         │
│  Metric: ○ Technical Roles   ● Overall Workforce        │
│                                                         │
│  35% ─┼─────────────────────────────────────────────    │
│       │                              ╭─ Apple           │
│  30% ─┼──────────────────────────╭───┴──────────────    │
│       │              ╭───────────┴─────╮                │
│       │         ╭────┴─────────────────┼─ Google        │
│  25% ─┼─────────┴──────────────────────┤                │
│       │    ╭───────────────────────────┼─ Microsoft     │
│       │────┴───────────────────────────╯    (dashed)    │
│  20% ─┼─────────────────────────────────────────────    │
│       │                         ╭──────┬─ Meta          │
│  15% ─┼─────────────────────────┴──────╯   (dashed)     │
│       │                                                 │
│       └─────┼─────┼─────┼─────┼─────┼─────┼─────┼────   │
│           2014  2016  2018  2020  2022  2024  2025      │
│                                                         │
│  ☑ Google  ☑ Apple  ☑ Microsoft  ☑ Meta  ☐ Amazon      │
│                                                         │
│  ▓ Reported    ░ Not reported (projected)               │
└─────────────────────────────────────────────────────────┘
```

### Interactive Elements
1. **Radio buttons**: Toggle Technical vs Overall workforce %

2. **Checkboxes**: Show/hide each company
   - All checked by default except Amazon (missing technical data)

3. **Hover**: Show:
   - Company, year, percentage
   - `reporting_status`
   - Source document

4. **Legend click**: Toggle individual companies

### Visual Encoding
- **Solid line + circle markers**: `reported`
- **Dashed line + X markers**: `not_reported`
- **Solid line + star markers**: `still_reporting` (2025)

### Key Annotations
- Vertical dashed line at 2024/2025: "DEI Reporting Stops"
- Text box: "Google, Meta, Microsoft confirmed no 2025 reports"

### Colors (company-specific)
- Google: `#4285F4`
- Apple: `#A2AAAD`
- Microsoft: `#00A4EF`
- Meta: `#0668E1`
- Amazon: `#FF9900`

---

## Chart 4: IPEDS Education Pipeline

### Data Source
`ipeds/processed_ipeds_csv_files/ipeds_national_by_track.csv`

### Chart Type
Grouped bar chart or line chart

### Layout
```
┌─────────────────────────────────────────────────────────┐
│  Women in CS Education: Degree Pipeline                 │
│                                                         │
│  Track: [Computer Science           ▼]                  │
│                                                         │
│  50% ─┼─────────────────────────────────────────────    │
│       │                                                 │
│  40% ─┼─────────────────────────────────────────────    │
│       │                                                 │
│  30% ─┼─────────────────────────────────────────────    │
│       │     ╭────────────────────╮                      │
│  20% ─┼─────┴────────────────────┴──────────────────    │
│       │  ■ Associate's  ■ Bachelor's  ■ Master's        │
│  10% ─┼─────────────────────────────────■───────────    │
│       │                               Doctorate         │
│       └─────┼─────┼─────┼─────┼─────┼─────┼─────────   │
│           2010  2013  2016  2019  2022  2024            │
│                                                         │
│  Compare to: ☐ Psychology  ☐ Biology  ☐ Engineering    │
└─────────────────────────────────────────────────────────┘
```

### Interactive Elements
1. **Dropdown**: Select primary track
   - Computer Science
   - Cybersecurity
   - Information Science
   - Computer Engineering
   - Electrical Engineering
   - IT & General Computing

2. **Checkboxes**: Add comparison fields (optional overlay)
   - Psychology (typically ~70% women)
   - Biology (typically ~60% women)
   - All Engineering (typically ~20% women)

3. **Toggle** (or tabs): View by degree level
   - All levels (grouped bars)
   - Bachelor's only (single line)
   - Doctoral only (single line)

4. **Hover**: Show total degrees awarded + women count + %

### Colors (by degree level)
- Associate's: `#76B7B2`
- Bachelor's: `#59A14F`
- Master's: `#EDC948`
- Doctorate: `#B07AA1`

### Key Annotations
- Text showing change: "+5.5pp since 2010" for CS Bachelor's

---

## Technical Implementation

### Dependencies
```python
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
```

### Standalone HTML Output
```python
fig.write_html(
    "visualizations/chart1_bls_age_cliff.html",
    include_plotlyjs=True,  # Embed JS for offline viewing
    full_html=True,
    config={
        'displayModeBar': True,
        'toImageButtonOptions': {'format': 'png', 'scale': 2}
    }
)
```

### Common Config
```python
COLORS = {
    'women': '#E15759',
    'men': '#4E79A7',
    'neutral': '#59A14F',
    'missing': '#BAB0AC',
}

LAYOUT_DEFAULTS = {
    'font_family': 'Arial, sans-serif',
    'title_font_size': 20,
    'legend_orientation': 'h',
    'legend_y': -0.15,
    'margin': {'t': 80, 'b': 100, 'l': 60, 'r': 40},
    'plot_bgcolor': 'white',
}
```

---

## Build Order

1. **Chart 1 (BLS)** — Most complex, most impactful
2. **Chart 3 (Big Tech)** — Simpler, good quick win
3. **Chart 2 (NSCG)** — Medium complexity, important for equity angle
4. **Chart 4 (IPEDS)** — Establishes the "pipeline entry" baseline

---

## Estimated Time

| Chart | Complexity | Est. Hours |
|-------|------------|------------|
| BLS Age Cliff | High | 2-3 |
| Big Tech Timeline | Medium | 1-2 |
| NSCG Heatmap | Medium-High | 2 |
| IPEDS Pipeline | Medium | 1-2 |
| Index/Dashboard | Low | 0.5 |
| **Total** | | **7-10** |
