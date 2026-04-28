# Visualization Plan — Leaky Pipeline

## Narrative Arc

The story follows women through the tech pipeline, showing where and how they "leak out":

1. **Act 1 (Education):** Women enter CS programs but remain a minority
2. **Act 2 (Workforce):** Those who enter tech leave disproportionately around age 35
3. **Act 3 (Data Gap):** The data to study this is sparse and fragmented
4. **Act 4 (Cliff):** Companies are now stopping DEI reporting entirely

---

## Interactive Charts (4 Total)

We're building **4 rich interactive Plotly charts** saved as standalone HTML files:

```
visualizations/
├── chart1_bls_age_cliff.html       # BLS occupation × age × year
├── chart2_nscg_intersectional.html # NSCG race × age × year  
├── chart3_bigtech_timeline.html    # Big Tech companies over time
├── chart4_ipeds_pipeline.html      # IPEDS track × degree × year
└── index.html                      # Dashboard linking all 4
```

---

## Chart 1: BLS Age Cliff (PRIMARY)

**Data:** `bls/processed_bls_data/bls_combined_clean.csv`  
**Dimensions:** 10 years × 11 occupations × 7 age brackets  
**Type:** Animated bar chart / population pyramid

### Interactive Elements
| Control | Type | Options |
|---------|------|---------|
| Occupation | Dropdown | Software Developers, Database Admins, Systems Analysts, etc. |
| Year | Slider | 2015-2024 with play/pause animation |
| Comparison | Checkbox | Show/hide men's bars |

### Key Story Points
- Peak employment at 25-34 age bracket
- Sharp 24% drop at 35-44 ("The Cliff")
- Continued decline through older brackets
- Year-over-year animation shows stagnation

### Hover Details
- Count (thousands)
- % women in bracket
- Year-over-year change

---

## Chart 2: NSCG Intersectional Heatmap

**Data:** `ncses/processed_nscg_data/nscg_intersectional_cliff.csv`  
**Dimensions:** 2 years × 6 race groups × 6 age brackets  
**Type:** Heatmap with cell annotations

### Interactive Elements
| Control | Type | Options |
|---------|------|---------|
| Year View | Radio buttons | 2019 / 2023 / Change (Δpp) |
| Cell hover | Tooltip | Exact %, sample size, suppression flag |

### Key Story Points
- Which demographic groups face the steepest age cliff?
- Pre-COVID (2019) vs post-COVID (2023) comparison
- Gray cells highlight data sparsity (n < 20 suppressed)
- "Change" view reveals who improved vs regressed

### Color Scales
- 2019/2023 views: Sequential (`YlOrRd`) — higher % = darker
- Change view: Diverging (`RdYlGn`) — red = worse, green = better

---

## Chart 3: Big Tech Timeline

**Data:** `big_tech_diversity.csv`  
**Dimensions:** 12 years × 5 companies × 2 metrics  
**Type:** Multi-line chart with markers

### Interactive Elements
| Control | Type | Options |
|---------|------|---------|
| Metric | Radio buttons | Technical Roles / Overall Workforce |
| Companies | Checkboxes | Google, Apple, Microsoft, Meta, Amazon |
| Legend | Click | Toggle individual companies |

### Key Story Points
- Progress was slow but steady (2014-2023)
- Google, Meta, Microsoft confirmed no 2025 DEI reports
- Apple and Amazon still reporting
- Visual "cliff" where lines go dashed

### Visual Encoding
| Status | Line Style | Marker |
|--------|------------|--------|
| `reported` | Solid | Circle |
| `not_reported` | Dashed | X |
| `still_reporting` | Solid | Star |

### Company Colors
- Google: `#4285F4`
- Apple: `#A2AAAD`
- Microsoft: `#00A4EF`
- Meta: `#0668E1`
- Amazon: `#FF9900`

---

## Chart 4: IPEDS Education Pipeline

**Data:** `ipeds/processed_ipeds_csv_files/ipeds_national_by_track.csv`  
**Dimensions:** 6 years × 8 tracks × 4 degree levels  
**Type:** Grouped bar chart or multi-line

### Interactive Elements
| Control | Type | Options |
|---------|------|---------|
| Track | Dropdown | CS, Cybersecurity, Computer Eng, Electrical Eng, etc. |
| Degree Level | Toggle/Tabs | All levels / Bachelor's only / Doctoral only |
| Comparison | Checkboxes | Add Psychology, Biology, Engineering overlay |

### Key Story Points
- CS Bachelor's: 18.3% (2010) → 23.8% (2024), only +5.5pp in 14 years
- Compare to Psychology (~70% women) to show the gap
- Does women's % change across degree levels?

### Colors (by degree level)
- Associate's: `#76B7B2`
- Bachelor's: `#59A14F`
- Master's: `#EDC948`
- Doctorate: `#B07AA1`

---

## Technical Stack

### Dependencies
```python
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
```

### Color Palette
```python
COLORS = {
    'women': '#E15759',      # Coral red
    'men': '#4E79A7',        # Steel blue
    'neutral': '#59A14F',    # Green
    'missing': '#BAB0AC',    # Gray
}
```

### Layout Defaults
```python
LAYOUT_DEFAULTS = {
    'font_family': 'Arial, sans-serif',
    'title_font_size': 20,
    'legend_orientation': 'h',
    'legend_y': -0.15,
    'margin': {'t': 80, 'b': 100, 'l': 60, 'r': 40},
    'plot_bgcolor': 'white',
}
```

### HTML Output
```python
fig.write_html(
    "visualizations/chartX_name.html",
    include_plotlyjs=True,
    full_html=True,
    config={
        'displayModeBar': True,
        'toImageButtonOptions': {'format': 'png', 'scale': 2}
    }
)
```

---

## Build Order

| Priority | Chart | Complexity | Rationale |
|----------|-------|------------|-----------|
| 1 | BLS Age Cliff | High | Core narrative, most dimensions |
| 2 | Big Tech Timeline | Medium | Quick win, newsworthy |
| 3 | NSCG Heatmap | Medium-High | Equity angle, data gap story |
| 4 | IPEDS Pipeline | Medium | Establishes baseline |

---

## Key Questions Answered

| Question | Chart | Answer |
|----------|-------|--------|
| Where is the pipeline leaking? | BLS Age Cliff | Age 35-44, 24% drop |
| Is it getting better? | All charts | Barely — ~2pp/decade |
| Who is most affected? | NSCG Heatmap | Varies by race × age |
| Can we measure this going forward? | Big Tech | No — data disappearing |
| How bad is the starting point? | IPEDS | Only 24% of CS grads are women |

---

## Dashboard (index.html)

Final deliverable: A single-page dashboard with:
- 4 embedded charts (iframes or tabs)
- Brief narrative text between charts
- Key statistics callout boxes
- Navigation between acts
