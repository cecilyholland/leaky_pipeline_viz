"""
sdr_preprocessing.py
Survey of Doctorate Recipients (SDR)
NSF NCSES Public Use Files — Act 3: The Data Gap

DATA STRUCTURE (confirmed from epsd23.csv + Dpsd21.xlsx codebook):
  Unit of observation: individual doctorate holder (person-level microdata)
  Population: people with a US S&E or health doctorate, currently employed or seeking work
  Survey cycle: biennial (2003, 2006, 2008, 2010, 2013, 2015, 2017, 2019, 2021, 2023)
  ~80,000 respondents per wave

KEY VARIABLES (confirmed):
  SEX          — 'M' / 'F'
  AGEGRP       — 5-year age groups: 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70
  NDGMEMG      — Field of highest degree (major group): 1=CS/math, 2=bio, 3=phys,
                  4=social sci, 5=engineering, 6=S&E-related, 7=non-S&E
  NDGMENGP     — Field of highest degree (minor group) — more granular
  NBAMEMG      — Field of BA degree (same codes)
  N2OCPRMG     — Principal job occupation major group (same codes as NSCG)
  RACETHMP     — Race/ethnicity: 1=Hispanic, 2=AmInd, 3=Asian, 4=Black,
                  5=White, 6=NatHaw, 7=Multi
  WTSURVY      — Survey weight
  SALARYP      — Annual salary (9999998 = not applicable / not employed)
  LFSTAT       — Labor force status: 1=employed, 2=unemployed, 3=not in LF
  EMSECDT      — Employer sector: '11'=4-yr college/univ, '21'=for-profit,
                  '22'=nonprofit, '23'=self-employed, '31'=fed govt, etc.
  PDIX         — Currently in postdoc: 'Y'/'N' ('L'=not applicable)
  TENI         — Tenure status indicator: 'L'=not applicable (non-academic)
  TENSTA       — Tenure status: 1=tenured, 2=on track, 3=not on track, 4=no system
  OCEDRLP      — How related is job to PhD field (job-degree relatedness)

SDR-SPECIFIC STORY FOR ACT 3:
  Unlike BLS/NSCG, SDR tracks doctorate holders specifically — letting us see:
  1. The CS/math PhD salary gap: women median $115k vs men $140k (2023)
  2. The career trajectory cliff: women drop from 29% at age 30 to 15% by 70
  3. Tenure leaky pipeline: women's share at each tenure stage in CS academia
  4. Postdoc trap: whether women are disproportionately stuck in postdoc positions
  5. Intersectional: Black women (24.8%), Asian women (37.6%), Hispanic women (31.9%)

FILE LOCATIONS:
  Put Doctorate_Recipients_YYYY.zip files in ncses_datasets/sdr/
  2023 also has epsd23.csv directly — place that in ncses_datasets/sdr/ too
  DPSD xlsx codebooks are for reference only, not processed by this script

Run from repo root:
  conda activate plda2
  python sdr_preprocessing.py
"""

import zipfile
import pandas as pd
import numpy as np
from pathlib import Path

RAW_DIR = Path("ncses_datasets/sdr")
OUT_DIR = Path("processed_sdr_data")
OUT_DIR.mkdir(exist_ok=True)

# ── Confirmed variable mappings ───────────────────────────────────────────────
SEX_FEMALE = {"F", "f", "2", 2}

# NDGMEMG / N2OCPRMG major group codes (same across SDR and NSCG)
FIELD_LABELS = {
    1: "Computer science & math",
    2: "Biological/life sciences",
    3: "Physical sciences",
    4: "Social sciences",
    5: "Engineering",
    6: "S&E-related",
    7: "Non-S&E",
}
COMPUTING_FIELD_CODES = {1}   # CS/math — primary target

RACE_LABELS = {
    1: "Hispanic", 2: "Am. Indian/AK Native", 3: "Asian",
    4: "Black", 5: "White", 6: "Native Hawaiian/Pac. Isl.", 7: "Multiracial",
}

# EMSECDT employer sector codes
SECTOR_LABELS = {
    "11": "4-yr college/university",
    "12": "2-yr college",
    "13": "Other educational institution",
    "21": "For-profit business",
    "22": "Nonprofit organization",
    "23": "Self-employed",
    "31": "Federal government",
    "32": "State/local government",
    "40": "Military",
}

# TENSTA tenure status
TENURE_LABELS = {
    "1": "Tenured", "2": "On tenure track", "3": "Not on track", "4": "No system",
    1: "Tenured", 2: "On tenure track", 3: "Not on track", 4: "No system",
}

# Age bracket mapping (AGEGRP 5-yr codes)
AGE_BRACKETS = {
    20: "Under 30", 25: "Under 30",
    30: "30-39", 35: "30-39",
    40: "40-49", 45: "40-49",
    50: "50-59", 55: "50-59",
    60: "60+", 65: "60+", 70: "60+",
}


# ── File loading ──────────────────────────────────────────────────────────────
def find_sdr_files():
    """Find all SDR data files under ncses_datasets/sdr/."""
    found = []

    # Direct CSVs (only 2023 has this)
    for csv in sorted(RAW_DIR.rglob("epsd*.csv") ):
        stem  = csv.stem.lower().replace("epsd", "")
        year  = f"20{stem}" if len(stem) == 2 else stem
        found.append((year, csv))
        print(f"  [CSV]  {csv.relative_to(RAW_DIR)}  → year {year}")

    # Zipped files for all other years
    for zf in sorted(RAW_DIR.rglob("Doctorate_Recipients_*.zip")):
        year = zf.stem.split("_")[-1]
        dest = zf.parent / year
        dest.mkdir(exist_ok=True)
        if not any(dest.iterdir()):
            print(f"  [UNZIP] {zf.name}")
            with zipfile.ZipFile(zf) as z:
                z.extractall(dest)
        # Find data file inside
        for pat in ["*.csv", "*.CSV", "*.dta", "*.sas7bdat"]:
            matches = [f for f in dest.rglob(pat)
                       if not any(x in f.name.lower()
                                  for x in ["codebook", "readme", "guide", "dpsd", "layout"])]
            if matches:
                fp = max(matches, key=lambda f: f.stat().st_size)
                found.append((year, fp))
                print(f"  [ZIP→]  {fp.name}  → year {year}")
                break

    return found


def load_sdr_file(filepath: Path, year: str) -> pd.DataFrame | None:
    suffix = filepath.suffix.lower()
    size_mb = filepath.stat().st_size // 1024 // 1024
    print(f"    Loading {filepath.name} ({size_mb} MB)...")
    try:
        if suffix == ".csv":
            df = pd.read_csv(filepath, low_memory=False)
        elif suffix == ".dta":
            df = pd.read_stata(filepath)
        elif suffix == ".sas7bdat":
            df = pd.read_sas(filepath, format="sas7bdat", encoding="latin-1")
        else:
            print(f"    Unknown format: {suffix}")
            return None

        df.columns = df.columns.str.upper()
        df["SURVEY_YEAR"] = int(year)
        print(f"    → {len(df):,} respondents, {len(df.columns)} columns")
        return df
    except Exception as e:
        print(f"    ERROR: {e}")
        return None


# ── Analysis functions ────────────────────────────────────────────────────────
def prep_core(df: pd.DataFrame) -> pd.DataFrame:
    """Add derived columns used across all analyses."""
    df = df.copy()
    df["is_woman"]   = (df["SEX"].astype(str).str.upper() == "F").astype(int)
    df["wt"]         = pd.to_numeric(df.get("WTSURVY", pd.Series(1, index=df.index)),
                                      errors="coerce").fillna(1)
    df["field_num"]  = pd.to_numeric(df.get("NDGMEMG"), errors="coerce")
    df["occ_num"]    = pd.to_numeric(df.get("N2OCPRMG"), errors="coerce")
    df["race_num"]   = pd.to_numeric(df.get("RACETHMP"), errors="coerce")
    df["agegr_num"]  = pd.to_numeric(df.get("AGEGRP"), errors="coerce")
    df["age_bracket"] = df["agegr_num"].map(AGE_BRACKETS).fillna("Unknown")
    df["field_label"] = df["field_num"].map(FIELD_LABELS).fillna("Other")
    df["race_label"]  = df["race_num"].map(RACE_LABELS).fillna("Other")
    return df


def compute_age_cliff(df: pd.DataFrame, year: int) -> pd.DataFrame:
    """Women % by age bracket for CS/math doctorate holders."""
    cs = df[df["field_num"].isin(COMPUTING_FIELD_CODES)].copy()
    if len(cs) == 0:
        return pd.DataFrame()

    records = []
    for bracket in ["Under 30", "30-39", "40-49", "50-59", "60+"]:
        grp = cs[cs["age_bracket"] == bracket]
        if len(grp) < 20:
            continue
        tw = grp["wt"].sum()
        ww = grp.loc[grp["is_woman"] == 1, "wt"].sum()
        records.append({
            "year": year, "age_bracket": bracket,
            "n": len(grp), "pct_women": round(ww / tw * 100, 1) if tw > 0 else np.nan,
        })
    return pd.DataFrame(records)


def compute_salary_gap(df: pd.DataFrame, year: int) -> pd.DataFrame:
    """Median salary gap women vs men for CS/math PhDs."""
    cs = df[(df["field_num"].isin(COMPUTING_FIELD_CODES)) & (df["LFSTAT"].astype(str) == "1")].copy()
    cs["sal"] = pd.to_numeric(cs.get("SALARYP"), errors="coerce")
    cs = cs[cs["sal"] < 9_999_990]
    if len(cs) < 50:
        return pd.DataFrame()

    records = []
    for sex, grp in cs.groupby("SEX"):
        tw = grp["wt"].sum()
        # Weighted median via sorted cumulative weights
        s = grp.sort_values("sal")
        cum = s["wt"].cumsum()
        med_idx = cum.searchsorted(tw / 2)
        median_sal = s["sal"].iloc[min(med_idx, len(s) - 1)]
        records.append({
            "year": year,
            "sex": "Women" if str(sex).upper() == "F" else "Men",
            "median_salary": median_sal,
            "n": len(grp),
        })

    result = pd.DataFrame(records)
    if len(result) == 2:
        women_sal = result.loc[result.sex == "Women", "median_salary"].values
        men_sal   = result.loc[result.sex == "Men",   "median_salary"].values
        if len(women_sal) and len(men_sal) and men_sal[0] > 0:
            result["salary_ratio"] = round(women_sal[0] / men_sal[0], 3)
    return result


def compute_tenure_pipeline(df: pd.DataFrame, year: int) -> pd.DataFrame:
    """
    Women % at each tenure stage in CS/math academia.
    The 'tenure funnel' — should show women leaking at each stage.
    """
    # Filter: CS/math PhDs, employed in 4-yr colleges
    acad = df[
        (df["field_num"].isin(COMPUTING_FIELD_CODES)) &
        (df.get("EMSECDT", pd.Series("", index=df.index)).astype(str) == "11") &
        (df.get("TENI",    pd.Series("L", index=df.index)).astype(str) != "L")
    ].copy()

    if len(acad) < 30:
        return pd.DataFrame()

    records = []
    for stage, grp in acad.groupby("TENSTA"):
        label = TENURE_LABELS.get(stage, TENURE_LABELS.get(str(stage), f"Stage {stage}"))
        tw = grp["wt"].sum()
        ww = grp.loc[grp["is_woman"] == 1, "wt"].sum()
        records.append({
            "year": year, "tenure_stage": label,
            "n": len(grp), "pct_women": round(ww / tw * 100, 1) if tw > 0 else np.nan,
        })
    return pd.DataFrame(records)


def compute_intersectional(df: pd.DataFrame, year: int) -> pd.DataFrame:
    """Women % by race/ethnicity among CS/math doctorate holders."""
    cs = df[df["field_num"].isin(COMPUTING_FIELD_CODES)].copy()
    records = []
    for race_code, label in RACE_LABELS.items():
        grp = cs[cs["race_num"] == race_code]
        if len(grp) < 15:
            continue
        tw = grp["wt"].sum()
        ww = grp.loc[grp["is_woman"] == 1, "wt"].sum()
        records.append({
            "year": year, "race": label,
            "n": len(grp), "pct_women": round(ww / tw * 100, 1) if tw > 0 else np.nan,
        })
    return pd.DataFrame(records)


def compute_postdoc_trap(df: pd.DataFrame, year: int) -> pd.DataFrame:
    """
    Are women disproportionately stuck in postdocs?
    Among CS/math PhDs currently in postdoc (PDIX == 'Y'), what's the sex breakdown?
    Also: time-since-PhD for postdocs vs non-postdocs.
    """
    cs = df[df["field_num"].isin(COMPUTING_FIELD_CODES)].copy()
    cs["in_postdoc"] = cs.get("PDIX", pd.Series("N", index=cs.index)).astype(str).str.upper() == "Y"

    records = []
    for pd_status, grp in cs.groupby("in_postdoc"):
        tw = grp["wt"].sum()
        ww = grp.loc[grp["is_woman"] == 1, "wt"].sum()
        records.append({
            "year": year,
            "postdoc_status": "In postdoc" if pd_status else "Not in postdoc",
            "n": len(grp),
            "pct_women": round(ww / tw * 100, 1) if tw > 0 else np.nan,
        })
    return pd.DataFrame(records)


def compute_field_comparison(df: pd.DataFrame, year: int) -> pd.DataFrame:
    """
    Women % across ALL S&E fields for the data gap context chart.
    Shows CS as an outlier vs other fields.
    """
    records = []
    for field_code, label in FIELD_LABELS.items():
        grp = df[df["field_num"] == field_code]
        if len(grp) < 30:
            continue
        tw = grp["wt"].sum()
        ww = grp.loc[grp["is_woman"] == 1, "wt"].sum()
        records.append({
            "year": year, "field": label, "field_code": field_code,
            "n": len(grp), "pct_women": round(ww / tw * 100, 1) if tw > 0 else np.nan,
        })
    return pd.DataFrame(records)


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    print("=" * 65)
    print("SDR Public Use File — Preprocessing")
    print("Survey of Doctorate Recipients (NSF NCSES)")
    print("=" * 65)

    if not RAW_DIR.exists():
        print(f"\n⚠ Directory not found: {RAW_DIR}")
        print("  Create ncses_datasets/sdr/ and add:")
        print("  - epsd23.csv  (2023 microdata CSV)")
        print("  - Doctorate_Recipients_YYYY.zip  (other years)")
        return

    print(f"\n[1/3] Finding SDR files in {RAW_DIR}/")
    files = find_sdr_files()
    if not files:
        print("  No SDR files found.")
        return

    # Collect output frames
    age_cliff_frames      = []
    salary_gap_frames     = []
    tenure_frames         = []
    intersectional_frames = []
    postdoc_frames        = []
    field_comp_frames     = []

    print(f"\n[2/3] Processing {len(files)} wave(s)...")
    for year, filepath in sorted(files):
        print(f"\n  [{year}]  {filepath.name}")
        df = load_sdr_file(filepath, year)
        if df is None:
            continue

        df = prep_core(df)
        yr = int(year)

        age_cliff = compute_age_cliff(df, yr)
        if not age_cliff.empty:
            age_cliff_frames.append(age_cliff)
            print(f"    Age cliff: {len(age_cliff)} brackets")

        salary = compute_salary_gap(df, yr)
        if not salary.empty:
            salary_gap_frames.append(salary)
            ratio = salary["salary_ratio"].values[0] if "salary_ratio" in salary.columns else "n/a"
            print(f"    Salary gap: women/men ratio = {ratio}")

        tenure = compute_tenure_pipeline(df, yr)
        if not tenure.empty:
            tenure_frames.append(tenure)
            print(f"    Tenure pipeline: {len(tenure)} stages")

        intersect = compute_intersectional(df, yr)
        if not intersect.empty:
            intersectional_frames.append(intersect)
            print(f"    Intersectional: {len(intersect)} groups")

        postdoc = compute_postdoc_trap(df, yr)
        if not postdoc.empty:
            postdoc_frames.append(postdoc)

        field_comp = compute_field_comparison(df, yr)
        if not field_comp.empty:
            field_comp_frames.append(field_comp)

    print(f"\n[3/3] Saving outputs to {OUT_DIR}/")

    def save(frames, name):
        if frames:
            df = pd.concat(frames, ignore_index=True)
            df.to_csv(OUT_DIR / name, index=False)
            print(f"  → {name}  ({len(df)} rows)")
            return df
        return pd.DataFrame()

    age_df    = save(age_cliff_frames,      "sdr_age_cliff_cs.csv")
    sal_df    = save(salary_gap_frames,     "sdr_salary_gap_cs.csv")
    ten_df    = save(tenure_frames,         "sdr_tenure_pipeline_cs.csv")
    int_df    = save(intersectional_frames, "sdr_intersectional_cs.csv")
    pd_df     = save(postdoc_frames,        "sdr_postdoc_trap_cs.csv")
    field_df  = save(field_comp_frames,     "sdr_field_comparison.csv")

    # ── Print key findings ────────────────────────────────────────────────────
    print("\n" + "=" * 65)
    print("KEY FINDINGS (2023)")
    print("=" * 65)

    if not age_df.empty:
        latest = age_df[age_df["year"] == age_df["year"].max()]
        print(f"\nAge cliff — CS/math PhD holders ({latest['year'].max()}):")
        for _, row in latest.sort_values("age_bracket").iterrows():
            bar = "█" * int(row["pct_women"] / 2)
            print(f"  {row['age_bracket']:10s}: {row['pct_women']:5.1f}%  {bar}")

    if not sal_df.empty:
        latest = sal_df[sal_df["year"] == sal_df["year"].max()]
        print(f"\nSalary gap — CS/math PhDs ({latest['year'].max()}):")
        for _, row in latest.iterrows():
            print(f"  {row['sex']:6s}: ${row['median_salary']:>9,.0f}  (n={row['n']:,})")
        if "salary_ratio" in latest.columns:
            ratio = latest["salary_ratio"].dropna().values
            if len(ratio):
                print(f"  Women earn {ratio[0]:.1%} of men's median salary")

    if not ten_df.empty:
        latest = ten_df[ten_df["year"] == ten_df["year"].max()]
        print(f"\nTenure pipeline — CS/math in academia ({latest['year'].max()}):")
        for _, row in latest.iterrows():
            bar = "█" * int(row["pct_women"] / 2)
            print(f"  {row['tenure_stage']:20s}: {row['pct_women']:5.1f}%  {bar}")

    if not int_df.empty:
        latest = int_df[int_df["year"] == int_df["year"].max()]
        print(f"\nIntersectional — CS/math PhDs by race ({latest['year'].max()}):")
        for _, row in latest.sort_values("pct_women", ascending=False).iterrows():
            print(f"  {row['race']:25s}: {row['pct_women']:5.1f}%  (n={row['n']:,})")

    print(f"\n✓ Done. All outputs in {OUT_DIR}/")


if __name__ == "__main__":
    main()