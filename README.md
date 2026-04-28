# Leaky Pipeline — Women in Tech

**Course:** CPSC 5530 Data Visualization and Exploration  
**Due:** Sunday May 4th 11:59pm

A four-act data story exploring the underrepresentation of women in tech, from education through workforce, and the emerging data gaps that make this harder to study.

## Project Narrative

The "leaky pipeline" metaphor describes how women enter tech education and careers but leave disproportionately — particularly around age 35. This project visualizes that phenomenon across four acts:

| Act | Title | Dataset | Story |
|-----|-------|---------|-------|
| 1 | The Pipeline | IPEDS | Women in CS/tech education over time |
| 2 | The Workforce | BLS CPS | Women in tech occupations by age |
| 3 | The Data Gap | NSF NCSES | Where measurement breaks down |
| 4 | The Cliff | Big Tech DEI | Companies stopping diversity reporting |

## Repository Structure

```
leaky-pipeline-viz/
├── bls/
│   ├── bls_datasets/           # Raw BLS CPS annual files
│   │   └── cpsa20{15-24}.xlsx
│   ├── processed_bls_data/     # Cleaned outputs
│   └── bls_preprocessing.py
├── ipeds/
│   ├── ipeds_datasets/         # Raw IPEDS completions files
│   │   └── c20{10,13,16,19,22,24}_a.csv
│   ├── processed_ipeds_csv_files/
│   └── ipeds_preprocessing.py
├── ncses/
│   ├── ncses_datasets/
│   │   ├── gss/                # Graduate Students Survey
│   │   │   └── gss20{16-24}_Code.xlsx
│   │   ├── nscg/               # National Survey of College Graduates
│   │   │   └── epcg{19,23}.csv
│   │   └── sdr/                # Survey of Doctorate Recipients
│   │       └── epsd23.csv
│   ├── processed_gss_data/
│   ├── processed_nscg_data/
│   ├── processed_sdr_data/
│   ├── gss_preprocessing.py
│   ├── nscg_preprocessing.py
│   └── sdr_preprocessing.py
├── big_tech_diversity.csv      # Compiled DEI report data
└── README.md
```

## Datasets

### 1. IPEDS Completions (Act 1)

**Source:** [NCES IPEDS Complete Data Files](https://nces.ed.gov/ipeds/) → C[year]_A.csv  
**Years:** 2010, 2013, 2016, 2019, 2022, 2024  
**Scope:** CIP 11 (Computing) + CIP 14.09/14.10 (Computer/Electrical Engineering)

**Raw files:** `ipeds/ipeds_datasets/c20XX_a.csv`

| Column | Description |
|--------|-------------|
| UNITID | Institution ID |
| CIPCODE | 6-digit CIP code (e.g., "11.0701" = Computer Science) |
| AWLEVEL | Award level (3=Associate's, 5=Bachelor's, 7=Master's, 17=Doctorate) |
| CTOTALT | Total completions |
| CTOTALW | Women completions |
| CTOTALM | Men completions |

**Processed outputs:**
- `ipeds_national_by_track.csv` — Completions by track/year/award level with pct_women
- `ipeds_bachelors_by_track.csv` — Bachelor's degrees only
- `ipeds_cs_cyber_ladder.csv` — CS and Cybersecurity across degree levels
- `ipeds_filtered_raw.csv` — All filtered records

**Key finding:** CS bachelor's women % went 18.3% (2010) → 23.8% (2024), only +5.5pp over 14 years

### 2. BLS Current Population Survey (Act 2)

**Source:** [BLS CPS Tables](https://bls.gov/cps/tables.htm) → Household Data Annual Averages  
**Files:** cpsa20XX.xlsx (sheets: cpsaat11, cpsaat11b)  
**Years:** 2015–2024

**Raw files:** `bls/bls_datasets/cpsa20XX.xlsx`

| Sheet | Content |
|-------|---------|
| cpsaat11 | Occupation × sex (total employed, % women) |
| cpsaat11b | Occupation × age bracket (count by age group) |

**Processed outputs:**
- `bls_tech_by_sex.csv` — Women % by occupation and year
- `bls_tech_by_age.csv` — Age distribution by occupation
- `bls_combined_clean.csv` — Combined with estimated women counts

**Important note:** `women_count_k_approx` = total_in_bracket × pct_women. This is an approximation since BLS doesn't publish age × sex × occupation cross-tabs.

**Key findings:**
- Software Developers: 17.9% → 20.3% women (2015–2024), near-stagnant
- Age cliff visible: Software Devs peak at 25–34 (742k), drop 24% at 35–44 (567k), drop 35% more at 45–54 (366k)

### 3. NSF NCSES Surveys (Act 3)

Three microdata surveys from the National Center for Science and Engineering Statistics.

#### NSCG — National Survey of College Graduates
**Source:** [NCSES Data Download](https://ncsesdata.nsf.gov/datadownload/)  
**Files:** `ncses/ncses_datasets/nscg/epcg{19,23}.csv`  
**Years:** 2019, 2023

Individual-level survey of college graduates. Key variables:
- `SEX` / `SEX_2023` — M/F
- `N2OCPRMG` — Occupation major group (1 = Computer & math scientists)
- `AGEGR` — Age group (5-year bins: 20, 25, 30...)
- `RACETHM` — Race/ethnicity (1=Hispanic, 3=Asian, 4=Black, 5=White, 7=Multi)
- `WTSURVY` — Survey weight

**Processed outputs:**
- `nscg_age_cliff_computing.csv` — Women % by age bracket in computing
- `nscg_2019_2023_diff.csv` — Pre/post-COVID comparison
- `nscg_intersectional_cliff.csv` — Women % by age × race
- `nscg_field_trends.csv` — Women % by BA field
- `nscg_salary_gap_computing.csv` — Median salary by sex

#### SDR — Survey of Doctorate Recipients
**Source:** [NCSES Data Download](https://ncsesdata.nsf.gov/datadownload/)  
**Files:** `ncses/ncses_datasets/sdr/epsd23.csv`  
**Years:** 2023 only

Individual-level survey of U.S. doctorate holders. Same variable structure as NSCG.

**Processed outputs:**
- `sdr_age_cliff_computing.csv` — Women % by age bracket
- `sdr_occupation_summary.csv` — Women % by occupation field
- `sdr_intersectional_computing.csv` — Women % by race in computing
- `sdr_salary_gap_computing.csv` — Salary gap (women earn 86.7% of men)

#### GSS — Graduate Students and Postdocs Survey
**Source:** [NCSES Data Download](https://ncsesdata.nsf.gov/datadownload/)  
**Files:** `ncses/ncses_datasets/gss/gss20{16-24}_Code.xlsx`  
**Years:** 2016, 2019, 2020, 2021, 2022, 2023, 2024

Institution-level survey of graduate enrollment by field. The xlsx files contain multiple sheets (Race, Support, PD_NFR) with enrollment counts.

Key variables (from Appendix B codebook):
- `gss_code` — Field code (106=Computer Science, 118=Computer Engineering, 119=Electrical Engineering)
- `ft_wmen_all_races_v` — Full-time women grad students
- `ft_tot_all_races_v` — Full-time total grad students
- `dr_ft_wmen_all_races_v` — Doctoral women full-time
- `ma_ft_wmen_all_races_v` — Master's women full-time

**Processed outputs:**
- `gss_all_fields_by_year.csv` — All fields aggregated by year
- `gss_computing_by_year.csv` — Computing fields only (CS, CE, EE)
- `gss_computing_intersectional.csv` — Women by race in computing

**Key finding:** CS doctoral women % went 19.9% (2019) -> 21.9% (2024), only +2.0pp in 5 years

### 4. Big Tech Diversity Reports (Act 4)

**File:** `big_tech_diversity.csv` (manually compiled)  
**Companies:** Google, Apple, Microsoft, Meta, Amazon  
**Years:** 2014–2025

| Column | Description |
|--------|-------------|
| company | Company name |
| year | Report year |
| women_overall_pct | Women % of total workforce |
| women_technical_pct | Women % of technical roles |
| reporting_status | `reported`, `not_reported`, `still_reporting` |
| source | Source document |

**Key story:** Google, Meta, Microsoft confirmed no 2025 DEI reports. Apple and Amazon still reporting. This creates a "data cliff" at 2025 where we lose visibility into workforce composition.

## Running Preprocessing

```bash
conda activate plda2

# IPEDS
python ipeds/ipeds_preprocessing.py

# BLS
python bls/bls_preprocessing.py

# NCSES
python ncses/nscg_preprocessing.py
python ncses/sdr_preprocessing.py
python ncses/gss_preprocessing.py
```

## Technical Notes

- **Conda environment:** plda2
- **Dependencies:** pandas, numpy, openpyxl (for xlsx files)
- **CIPCODE handling:** Always load with `dtype={"CIPCODE": str}` and recompute CIP2 after load
- **pct_women calculation:** Use `float("nan")` not `pd.NA` for `.round(1)` compatibility
- **All scripts run from repo root**

## Visualization Plan (Plotly)

| Act | Chart Type | Key Interactions |
|-----|------------|------------------|
| 1 | Choropleth + multi-line | Year slider, dropdown by track |
| 2 | Scatter/bubble + bar | Age bracket filter, occupation highlight |
| 3 | Faceted heatmap | Missing-data overlay, animated transitions |
| 4 | Multi-line with cliff | Dashed lines where reporting stopped |

## Data Caveats

1. **BLS age × sex approximation:** Women counts by age bracket are estimated, not directly measured
2. **NCSES small cells:** Intersectional breakdowns suppress cells with n < 15-30
3. **Big Tech self-reported:** Company DEI data is not independently audited
4. **IPEDS timing:** 2024 data is preliminary

## Report Requirements

- 15+ pages
- Interactive visualizations saved as HTML
- YouTube video demo
- Python code (.ipynb or .py)
- Dataset links
