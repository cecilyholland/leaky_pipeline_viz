"""
gss_preprocessing.py
Survey of Graduate Students & Postdoctorates in Science and Engineering (GSS)
NSF NCSES — Act 3: The Data Gap

DATA STRUCTURE:
  The gss20XX_Code.xlsx files contain the actual data (not just codebooks).
  Each xlsx has 3 sheets: Race, Support, PD_NFR
  Unit of observation: institution x gss_code (field/department) x year

KEY VARIABLES (from Appendix B codebook):
  Variable naming: {degree_level}_{time_status}_{sex}_{race}_v
    - degree_level: (blank)=all grad, ma=master's, dr=doctoral, pd=postdoc
    - time_status: ft=full-time, pt=part-time
    - sex: wmen=women, men=men, tot=total
    - race: all_races, black, indian, asian, pacific, white, hisp, multi, forgn, unk

  Key enrollment variables:
    ft_wmen_all_races_v  - Full-time women grad students, all races
    ft_tot_all_races_v   - Full-time total grad students
    dr_ft_wmen_all_races_v - Doctoral women full-time
    dr_ft_tot_all_races_v  - Doctoral total full-time
    ma_ft_wmen_all_races_v - Master's women full-time
    ma_ft_tot_all_races_v  - Master's total full-time

GSS FIELD CODES (gss_code) for computing/engineering:
  106 = Computer science
  118 = Computer engineering
  119 = Electrical engineering
  712 = Mathematics
  723 = Statistics

Run from repo root:
  conda activate plda2
  python ncses/gss_preprocessing.py
"""

import pandas as pd
import numpy as np
from pathlib import Path

RAW_DIR = Path("ncses/ncses_datasets/gss")
OUT_DIR = Path("ncses/processed_gss_data")
OUT_DIR.mkdir(exist_ok=True)

# GSS field codes for computing and comparison fields
COMPUTING_GSS_CODES = {
    106: "Computer science",
    118: "Computer engineering",
    119: "Electrical engineering",
}

COMPARISON_FIELDS = {
    712: "Mathematics",
    723: "Statistics",
    803: "Chemistry",
    804: "Physics",
    102: "Biochemistry",
    410: "Psychology",
    414: "Sociology",
}

ALL_FIELDS = {**COMPUTING_GSS_CODES, **COMPARISON_FIELDS}

# Key variables to extract for women % analysis
ENROLLMENT_VARS = [
    # All grad (master's + doctoral)
    "ft_wmen_all_races_v", "ft_tot_all_races_v",
    "ft_wmen_black_v", "ft_wmen_hisp_v", "ft_wmen_asian_v",
    "ft_wmen_indian_v", "ft_wmen_white_v", "ft_wmen_multi_v", "ft_wmen_forgn_v",
    # Master's
    "ma_ft_wmen_all_races_v", "ma_ft_tot_all_races_v",
    # Doctoral
    "dr_ft_wmen_all_races_v", "dr_ft_tot_all_races_v",
    "dr_ft_wmen_black_v", "dr_ft_wmen_hisp_v", "dr_ft_wmen_asian_v",
    # First-time (new enrollees)
    "ft_frst_wmen_all_races_v", "ft_frst_tot_all_races_v",
]

POSTDOC_VARS = [
    "pd_wmen_all_races_v", "pd_tot_all_races_v",
    "pd_wmen_black_v", "pd_wmen_hisp_v", "pd_wmen_asian_v",
]


def load_gss_year(filepath: Path) -> pd.DataFrame:
    """Load GSS xlsx file, combining Race sheet data."""
    print(f"  Loading {filepath.name}...")

    try:
        xlsx = pd.ExcelFile(filepath)

        # Race sheet has enrollment by sex/race
        df = pd.read_excel(xlsx, sheet_name="Race")

        # Extract year from filename (gss2024_Code.xlsx -> 2024)
        year = int(filepath.stem.replace("gss", "").replace("_Code", ""))
        if "year" not in df.columns:
            df["year"] = year

        print(f"    -> {len(df):,} rows, year={year}")
        return df

    except Exception as e:
        print(f"    ERROR: {e}")
        return pd.DataFrame()


def aggregate_by_field(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate institution-level data to field (gss_code) level."""
    if df.empty or "gss_code" not in df.columns:
        return pd.DataFrame()

    # Identify numeric count columns (end with _v)
    count_cols = [c for c in df.columns if c.endswith("_v") and c in df.columns]

    # Convert to numeric
    for col in count_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Aggregate by gss_code and year
    agg_dict = {c: "sum" for c in count_cols if c in df.columns}
    agg_dict["institution_id"] = "count"  # count institutions per field

    grouped = df.groupby(["gss_code", "year"]).agg(agg_dict).reset_index()
    grouped = grouped.rename(columns={"institution_id": "n_institutions"})

    return grouped


def compute_pct_women(df: pd.DataFrame) -> pd.DataFrame:
    """Compute women % for each degree level."""
    df = df.copy()

    # All grad students (FT)
    if "ft_wmen_all_races_v" in df.columns and "ft_tot_all_races_v" in df.columns:
        df["pct_women_all_grad"] = (
            df["ft_wmen_all_races_v"] / df["ft_tot_all_races_v"] * 100
        ).round(1)

    # Master's
    if "ma_ft_wmen_all_races_v" in df.columns and "ma_ft_tot_all_races_v" in df.columns:
        df["pct_women_masters"] = (
            df["ma_ft_wmen_all_races_v"] / df["ma_ft_tot_all_races_v"] * 100
        ).round(1)

    # Doctoral
    if "dr_ft_wmen_all_races_v" in df.columns and "dr_ft_tot_all_races_v" in df.columns:
        df["pct_women_doctoral"] = (
            df["dr_ft_wmen_all_races_v"] / df["dr_ft_tot_all_races_v"] * 100
        ).round(1)

    # First-time enrollees
    if "ft_frst_wmen_all_races_v" in df.columns and "ft_frst_tot_all_races_v" in df.columns:
        df["pct_women_first_time"] = (
            df["ft_frst_wmen_all_races_v"] / df["ft_frst_tot_all_races_v"] * 100
        ).round(1)

    # Postdoc
    if "pd_wmen_all_races_v" in df.columns and "pd_tot_all_races_v" in df.columns:
        df["pct_women_postdoc"] = (
            df["pd_wmen_all_races_v"] / df["pd_tot_all_races_v"] * 100
        ).round(1)

    return df


def main():
    print("=" * 65)
    print("GSS Public Use Files - Preprocessing")
    print("Graduate Students & Postdocs in S&E")
    print("=" * 65)

    # Find all GSS xlsx files
    xlsx_files = sorted(RAW_DIR.glob("gss*_Code.xlsx"))
    if not xlsx_files:
        print(f"\nWARNING: No GSS xlsx files found in {RAW_DIR}/")
        print("  Expected: gss2016_Code.xlsx, gss2019_Code.xlsx, etc.")
        return

    print(f"\n[1/4] Found {len(xlsx_files)} GSS files:")
    for f in xlsx_files:
        print(f"  {f.name}")

    # Load and combine all years
    print(f"\n[2/4] Loading data...")
    year_frames = []
    for filepath in xlsx_files:
        df = load_gss_year(filepath)
        if not df.empty:
            year_frames.append(df)

    if not year_frames:
        print("\nFAILED: No data loaded")
        return

    combined = pd.concat(year_frames, ignore_index=True)
    print(f"\n  Total: {len(combined):,} institution-field-year records")

    # Aggregate to field level
    print(f"\n[3/4] Aggregating to field level...")
    field_agg = aggregate_by_field(combined)
    field_agg = compute_pct_women(field_agg)

    # Add field labels
    field_agg["field_label"] = field_agg["gss_code"].map(ALL_FIELDS).fillna("Other")

    # Save all fields
    field_agg.to_csv(OUT_DIR / "gss_all_fields_by_year.csv", index=False)
    print(f"  -> gss_all_fields_by_year.csv ({len(field_agg)} rows)")

    # Computing-focused subset
    computing_mask = field_agg["gss_code"].isin(COMPUTING_GSS_CODES.keys())
    computing_df = field_agg[computing_mask].copy()
    computing_df.to_csv(OUT_DIR / "gss_computing_by_year.csv", index=False)
    print(f"  -> gss_computing_by_year.csv ({len(computing_df)} rows)")

    # Intersectional breakdown for computing
    race_cols = ["gss_code", "field_label", "year", "n_institutions",
                 "ft_wmen_black_v", "ft_wmen_hisp_v", "ft_wmen_asian_v",
                 "ft_wmen_indian_v", "ft_wmen_white_v", "ft_wmen_multi_v",
                 "ft_wmen_forgn_v", "ft_tot_all_races_v"]
    available = [c for c in race_cols if c in computing_df.columns]
    intersect_df = computing_df[available].copy()
    intersect_df.to_csv(OUT_DIR / "gss_computing_intersectional.csv", index=False)
    print(f"  -> gss_computing_intersectional.csv ({len(intersect_df)} rows)")

    # Summary statistics
    print(f"\n[4/4] Summary - Women % in computing fields:")
    print("-" * 60)

    for code in COMPUTING_GSS_CODES:
        field_data = computing_df[computing_df["gss_code"] == code].sort_values("year")
        if field_data.empty:
            continue

        label = COMPUTING_GSS_CODES[code]
        if "pct_women_doctoral" in field_data.columns:
            pct_col = "pct_women_doctoral"
        elif "pct_women_all_grad" in field_data.columns:
            pct_col = "pct_women_all_grad"
        else:
            continue

        valid = field_data[field_data[pct_col].notna()]
        if len(valid) >= 2:
            first = valid.iloc[0]
            last = valid.iloc[-1]
            change = last[pct_col] - first[pct_col]
            print(f"  {label:25s}: {first[pct_col]:5.1f}% ({int(first['year'])}) -> "
                  f"{last[pct_col]:5.1f}% ({int(last['year'])})  [{change:+.1f}pp]")
        elif len(valid) == 1:
            row = valid.iloc[0]
            print(f"  {label:25s}: {row[pct_col]:5.1f}% ({int(row['year'])})")

    print(f"\nOK: Done. Outputs in {OUT_DIR}/")


if __name__ == "__main__":
    main()
