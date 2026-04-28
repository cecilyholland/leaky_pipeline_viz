"""
sdr_preprocessing.py
Survey of Doctorate Recipients (SDR)
NSF NCSES Public Use Files — Act 3: The Data Gap

IMPORTANT — SDR data structure:
  Unit of observation: INDIVIDUAL survey respondent (person-level microdata)
  Each row = one doctorate holder in the U.S.
  Key variables: occupation, field of doctorate, sex, age, race/ethnicity

SDR is the doctorate-holder counterpart to NSCG (which covers all college grads).
It tracks the careers of people who earned doctorates in the U.S.

LIMITATION: Only 2023 data available (epsd23.csv).
Single-year analysis only — no longitudinal comparison possible.

Run from repo root:
  conda activate plda2
  python ncses/sdr_preprocessing.py
"""

import pandas as pd
import numpy as np
from pathlib import Path

RAW_DIR = Path("ncses/ncses_datasets/sdr")
OUT_DIR = Path("ncses/processed_sdr_data")
OUT_DIR.mkdir(exist_ok=True)

VAR_ALIASES = {
    "sex":        ["SEX", "GENDER"],
    "age_group":  ["AGEGRP", "AGEGR"],
    "occupation": ["N2OCPRMG", "NOCPRMG"],
    "occ_detail": ["N2OCPRNG"],
    "field_phd":  ["NDGMEMG", "ndgmemg"],
    "race_eth":   ["RACETHMP", "RACETHM"],
    "weight":     ["WTSURVY"],
    "salary":     ["SALARYP", "SALARY"],
    "earnings":   ["EARNP"],
    "empl_stat":  ["PDEMPL"],
}

OCC_LABELS = {
    1: "Computer & math scientists",
    2: "Biological/life scientists",
    3: "Physical scientists",
    4: "Social scientists",
    5: "Engineers",
    6: "S&E-related",
    7: "Non-S&E",
    8: "Non-S&E (mgmt/other)",
}

RACE_LABELS = {
    1: "Hispanic", 2: "Am. Indian/AK Native", 3: "Asian",
    4: "Black", 5: "White", 6: "Native Hawaiian/Pac. Isl.", 7: "Multiracial",
}

AGE_GROUP_LABELS = {
    25: "Under 30", 30: "30-34",
    35: "35-39", 40: "40-44",
    45: "45-49", 50: "50-54",
    55: "55-59", 60: "60-64",
    65: "65-69", 70: "70-75", 75: "75+",
}

AGE_BRACKETS = {
    25: "Under 35", 30: "Under 35",
    35: "35-44", 40: "35-44",
    45: "45-54", 50: "45-54",
    55: "55-64", 60: "55-64",
    65: "65+", 70: "65+", 75: "65+",
}


def find_col(df: pd.DataFrame, varname: str) -> str | None:
    aliases = VAR_ALIASES.get(varname, [varname])
    for alias in aliases:
        if alias in df.columns:
            return alias
        matches = [c for c in df.columns if c.upper() == alias.upper()]
        if matches:
            return matches[0]
    return None


def load_sdr_file(filepath: Path) -> pd.DataFrame | None:
    size_mb = filepath.stat().st_size // 1024 // 1024
    print(f"  Loading {filepath.name} ({size_mb} MB)...")

    try:
        header_df = pd.read_csv(filepath, nrows=0)
        wanted = []
        found_map = {}
        for varname in VAR_ALIASES:
            col = find_col(header_df, varname)
            if col:
                wanted.append(col)
                found_map[varname] = col

        print(f"  Variable mapping: {found_map}")
        df = pd.read_csv(filepath, usecols=wanted, dtype=str, low_memory=False)
        df.columns = df.columns.str.upper()
        print(f"  -> {len(df):,} respondents, {len(df.columns)} columns")
        return df

    except Exception as e:
        print(f"  ERROR: {e}")
        return None


def compute_age_cliff(df: pd.DataFrame) -> pd.DataFrame:
    """Women % by age bracket for computing occupations (N2OCPRMG=1)."""
    sex_col = find_col(df, "sex") or "SEX"
    age_col = find_col(df, "age_group") or "AGEGRP"
    occ_col = find_col(df, "occupation") or "N2OCPRMG"
    wt_col = find_col(df, "weight") or "WTSURVY"

    comp_df = df[pd.to_numeric(df[occ_col], errors="coerce") == 1].copy()
    if len(comp_df) == 0:
        print(f"  WARNING: No computing occupation records found")
        return pd.DataFrame()

    comp_df["is_woman"] = (comp_df[sex_col].astype(str).str.upper() == "F").astype(int)
    comp_df["wt"] = pd.to_numeric(comp_df.get(wt_col, pd.Series(1, index=comp_df.index)),
                                   errors="coerce").fillna(1)
    comp_df["agegr_num"] = pd.to_numeric(comp_df[age_col], errors="coerce")
    comp_df["age_bracket"] = comp_df["agegr_num"].map(AGE_BRACKETS).fillna("Unknown")

    records = []
    bracket_order = ["Under 35", "35-44", "45-54", "55-64", "65+"]
    for bracket in bracket_order:
        grp = comp_df[comp_df["age_bracket"] == bracket]
        if len(grp) == 0:
            continue
        total_wt = grp["wt"].sum()
        women_wt = grp.loc[grp["is_woman"] == 1, "wt"].sum()
        records.append({
            "age_bracket": bracket,
            "total_n": len(grp),
            "women_n": int(grp["is_woman"].sum()),
            "total_wt": round(total_wt, 0),
            "pct_women": round(women_wt / total_wt * 100, 1) if total_wt > 0 else np.nan,
        })

    return pd.DataFrame(records)


def compute_occ_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Women % by occupation group — all doctorate holders."""
    sex_col = find_col(df, "sex") or "SEX"
    occ_col = find_col(df, "occupation") or "N2OCPRMG"
    wt_col = find_col(df, "weight") or "WTSURVY"

    df = df.copy()
    df["is_woman"] = (df[sex_col].astype(str).str.upper() == "F").astype(int)
    df["wt"] = pd.to_numeric(df.get(wt_col, pd.Series(1, index=df.index)),
                              errors="coerce").fillna(1)
    df["occ_num"] = pd.to_numeric(df[occ_col], errors="coerce")
    df["occ_label"] = df["occ_num"].map(OCC_LABELS)

    records = []
    for occ, grp in df.groupby("occ_label"):
        if pd.isna(occ):
            continue
        total_wt = grp["wt"].sum()
        women_wt = grp.loc[grp["is_woman"] == 1, "wt"].sum()
        records.append({
            "occupation": occ,
            "total_n": len(grp),
            "women_n": int(grp["is_woman"].sum()),
            "pct_women": round(women_wt / total_wt * 100, 1) if total_wt > 0 else np.nan,
        })

    return pd.DataFrame(records).sort_values("pct_women", ascending=False)


def compute_intersectional(df: pd.DataFrame) -> pd.DataFrame:
    """Women % by race/ethnicity in computing occupations."""
    sex_col = find_col(df, "sex") or "SEX"
    occ_col = find_col(df, "occupation") or "N2OCPRMG"
    race_col = find_col(df, "race_eth") or "RACETHMP"
    wt_col = find_col(df, "weight") or "WTSURVY"

    comp_df = df[pd.to_numeric(df[occ_col], errors="coerce") == 1].copy()
    comp_df["is_woman"] = (comp_df[sex_col].astype(str).str.upper() == "F").astype(int)
    comp_df["wt"] = pd.to_numeric(comp_df.get(wt_col, pd.Series(1, index=comp_df.index)),
                                   errors="coerce").fillna(1)
    comp_df["race_num"] = pd.to_numeric(comp_df[race_col], errors="coerce")
    comp_df["race_label"] = comp_df["race_num"].map(RACE_LABELS)

    records = []
    for race, grp in comp_df.groupby("race_label"):
        if pd.isna(race) or len(grp) < 20:
            continue
        total_wt = grp["wt"].sum()
        women_wt = grp.loc[grp["is_woman"] == 1, "wt"].sum()
        records.append({
            "race": race,
            "total_n": len(grp),
            "women_n": int(grp["is_woman"].sum()),
            "pct_women": round(women_wt / total_wt * 100, 1) if total_wt > 0 else np.nan,
        })

    return pd.DataFrame(records).sort_values("pct_women", ascending=False)


def compute_salary_gap(df: pd.DataFrame) -> pd.DataFrame:
    """Median salary by sex for computing doctorate holders."""
    sex_col = find_col(df, "sex") or "SEX"
    occ_col = find_col(df, "occupation") or "N2OCPRMG"
    salary_col = find_col(df, "salary") or find_col(df, "earnings") or "SALARYP"

    if salary_col not in df.columns:
        print(f"  WARNING: No salary column found")
        return pd.DataFrame()

    comp_df = df[pd.to_numeric(df[occ_col], errors="coerce") == 1].copy()
    comp_df["sex_label"] = comp_df[sex_col].astype(str).str.upper().map({"F": "Women", "M": "Men"})
    comp_df["salary_num"] = pd.to_numeric(comp_df[salary_col], errors="coerce")
    comp_df = comp_df[comp_df["salary_num"] > 0]

    records = []
    for sex, grp in comp_df.groupby("sex_label"):
        if pd.isna(sex):
            continue
        records.append({
            "sex": sex,
            "n": len(grp),
            "median_salary": grp["salary_num"].median(),
            "mean_salary": grp["salary_num"].mean(),
        })

    result = pd.DataFrame(records)
    if len(result) == 2:
        women_sal = result.loc[result.sex == "Women", "median_salary"].values
        men_sal = result.loc[result.sex == "Men", "median_salary"].values
        if len(women_sal) and len(men_sal) and men_sal[0] > 0:
            result["salary_ratio"] = round(women_sal[0] / men_sal[0], 3)

    return result


def main():
    print("=" * 65)
    print("SDR Public Use File — Preprocessing (2023)")
    print("Survey of Doctorate Recipients")
    print("=" * 65)

    csvs = list(RAW_DIR.glob("epsd*.csv")) + list(RAW_DIR.glob("EPSD*.csv"))
    if not csvs:
        print(f"\nWARNING: No SDR CSV files found in {RAW_DIR}/")
        print("  Expected: epsd23.csv")
        print("  Download from: https://ncsesdata.nsf.gov/datadownload/")
        return

    print(f"\n[1/5] Found {len(csvs)} SDR file(s)")
    filepath = csvs[0]
    df = load_sdr_file(filepath)
    if df is None:
        return

    print(f"\n[2/5] Computing age cliff for doctorate holders in computing...")
    age_cliff = compute_age_cliff(df)
    if not age_cliff.empty:
        age_cliff.to_csv(OUT_DIR / "sdr_age_cliff_computing.csv", index=False)
        print(f"  -> sdr_age_cliff_computing.csv ({len(age_cliff)} rows)")

    print(f"\n[3/5] Computing occupation summary...")
    occ_summary = compute_occ_summary(df)
    if not occ_summary.empty:
        occ_summary.to_csv(OUT_DIR / "sdr_occupation_summary.csv", index=False)
        print(f"  -> sdr_occupation_summary.csv ({len(occ_summary)} rows)")

    print(f"\n[4/5] Computing intersectional breakdown...")
    intersect = compute_intersectional(df)
    if not intersect.empty:
        intersect.to_csv(OUT_DIR / "sdr_intersectional_computing.csv", index=False)
        print(f"  -> sdr_intersectional_computing.csv ({len(intersect)} rows)")

    print(f"\n[5/5] Computing salary gap...")
    salary = compute_salary_gap(df)
    if not salary.empty:
        salary.to_csv(OUT_DIR / "sdr_salary_gap_computing.csv", index=False)
        print(f"  -> sdr_salary_gap_computing.csv ({len(salary)} rows)")

    print(f"\n" + "=" * 65)
    print("Summary — Doctorate holders in computing (2023)")
    print("=" * 65)

    if not age_cliff.empty:
        print("\nWomen % by age bracket:")
        for _, row in age_cliff.iterrows():
            bar = "#" * int(row["pct_women"] / 2)
            print(f"  {row['age_bracket']:<12}: {row['pct_women']:5.1f}%  {bar}")

    if not occ_summary.empty:
        print("\nWomen % by occupation (all doctorate holders):")
        for _, row in occ_summary.iterrows():
            print(f"  {row['occupation']:<30}: {row['pct_women']:5.1f}%")

    if not salary.empty and "salary_ratio" in salary.columns:
        ratio = salary["salary_ratio"].dropna().values
        if len(ratio):
            print(f"\nSalary ratio (women/men) in computing: {ratio[0]:.1%}")

    print(f"\nOK: Done. Outputs in {OUT_DIR}/")


if __name__ == "__main__":
    main()
