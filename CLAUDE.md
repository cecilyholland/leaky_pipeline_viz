# Claude Instructions

Data visualization project analyzing women's representation in tech ("leaky pipeline").

## Quick Reference

```
conda activate plda2
python ipeds/ipeds_preprocessing.py
python bls/bls_preprocessing.py
python ncses/gss_preprocessing.py
python ncses/nscg_preprocessing.py
python ncses/sdr_preprocessing.py
```

## Project Structure

| Directory | Raw Data | Processed Output | Script |
|-----------|----------|------------------|--------|
| `ipeds/` | `ipeds_datasets/c20XX_a.csv` | `processed_ipeds_csv_files/` | `ipeds_preprocessing.py` |
| `bls/` | `bls_datasets/cpsa20XX.xlsx` | `processed_bls_data/` | `bls_preprocessing.py` |
| `ncses/` | `ncses_datasets/{gss,nscg,sdr}/` | `processed_{gss,nscg,sdr}_data/` | `{gss,nscg,sdr}_preprocessing.py` |
| root | `big_tech_diversity.csv` | (already clean) | — |

## Key Data Patterns

### IPEDS
- CIPCODE must be loaded as string: `dtype={"CIPCODE": str}`
- CIP 11.XX = Computing fields, CIP 14.09 = Computer Engineering, CIP 14.10 = Electrical Engineering
- AWLEVEL: 3=Associate's, 5=Bachelor's, 7=Master's, 17=Doctorate

### BLS
- Sheet `cpsaat11` = occupation × sex, `cpsaat11b` = occupation × age
- Women count by age is estimated (pct_women × age_bracket_total)

### NCSES (3 surveys)

**GSS (Graduate Students Survey):**
- xlsx files with sheets: Race, Support, PD_NFR
- Institution-level aggregates by field (gss_code)
- gss_code: 106=CS, 118=Computer Eng, 119=Electrical Eng
- Variables: `{ma,dr}_ft_{wmen,tot}_all_races_v`

**NSCG/SDR (College Grads / Doctorate Recipients):**
- Individual-level microdata with survey weights (WTSURVY)
- N2OCPRMG=1 means "Computer & math scientists"
- 2023 NSCG uses `SEX_2023` instead of `SEX`
- Suppress intersectional cells with n < 20

### Big Tech
- `reporting_status`: reported, not_reported, still_reporting
- Google/Meta/Microsoft stopped DEI reporting in 2024-2025

## Common Fixes

- Use `float("nan")` not `pd.NA` when computing pct_women (avoids `.round()` TypeError)
- Use `pd.to_numeric(series, errors="coerce")` not `.astype(float, errors="ignore")`
- Avoid Unicode chars in print statements on Windows (use ASCII alternatives)

## Visualization Stack

- Plotly for interactive charts
- Output as HTML for embedding in report
- Four-act narrative structure (Education → Workforce → Data Gap → DEI Cliff)
