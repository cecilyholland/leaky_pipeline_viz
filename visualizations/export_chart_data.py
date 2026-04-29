"""
Export chart data and configs as JSON for embedding in index.html.

Run from repo root:
    python visualizations/export_chart_data.py
"""

import json
import pandas as pd
import numpy as np
from pathlib import Path

OUTPUT_DIR = Path("visualizations/chart_data")
OUTPUT_DIR.mkdir(exist_ok=True)


def export_bls_chart():
    """Export BLS Age Cliff chart data."""
    df = pd.read_csv("bls/processed_bls_data/bls_combined_clean.csv")
    df = df[df['age_bracket'] != 'total'].copy()
    df['men_count_k_approx'] = df['count_k'] - df['women_count_k_approx']

    AGE_ORDER = ['age_16_19', 'age_20_24', 'age_25_34', 'age_35_44', 'age_45_54', 'age_55_64', 'age_65_plus']
    AGE_LABELS = {
        'age_16_19': '16-19', 'age_20_24': '20-24', 'age_25_34': '25-34',
        'age_35_44': '35-44', 'age_45_54': '45-54', 'age_55_64': '55-64', 'age_65_plus': '65+',
    }

    occupations = ['Software Developers', 'CS & Math (all)', 'Computer Systems Analysts',
                   'Database Administrators', 'Information Security Analysts',
                   'Computer Programmers', 'Network & Systems Admins']

    years = sorted(df['year'].unique())

    # Build data structure
    chart_data = {
        'years': [int(y) for y in years],
        'age_labels': [AGE_LABELS[a] for a in AGE_ORDER],
        'occupations': occupations,
        'data': {}
    }

    for occ in occupations:
        chart_data['data'][occ] = {}
        for year in years:
            year_data = df[(df['occupation'] == occ) & (df['year'] == year)].copy()
            year_data = year_data.set_index('age_bracket').reindex(AGE_ORDER)
            values = year_data['women_count_k_approx'].fillna(0).tolist()
            chart_data['data'][occ][int(year)] = [round(v, 1) for v in values]

    with open(OUTPUT_DIR / "bls_chart.json", 'w') as f:
        json.dump(chart_data, f)

    print(f"Exported BLS chart data")


def export_nscg_chart():
    """Export NSCG Intersectional heatmap data."""
    df = pd.read_csv("ncses/processed_nscg_data/nscg_intersectional_cliff.csv")

    AGE_ORDER = ['Under 25', '25-34', '35-44', '45-54', '55-64', '65+']
    RACE_ORDER = ['Asian', 'Black', 'Hispanic', 'Multiracial', 'White']

    # Calculate totals
    totals = df.groupby(['year', 'age_bracket']).agg({
        'n': 'sum',
        'pct_women': lambda x: np.average(x, weights=df.loc[x.index, 'n']) if df.loc[x.index, 'n'].sum() > 0 else np.nan
    }).reset_index()
    totals['race'] = 'All Women'
    totals['pct_women'] = totals['pct_women'].round(1)
    df = pd.concat([df, totals], ignore_index=True)

    RACE_ORDER_WITH_TOTAL = RACE_ORDER + ['All Women']

    chart_data = {
        'years': [2019, 2023],
        'age_labels': AGE_ORDER,
        'race_labels': RACE_ORDER_WITH_TOTAL,
        'data': {}
    }

    for year in [2019, 2023]:
        chart_data['data'][year] = {'pct': [], 'n': []}
        for race in RACE_ORDER_WITH_TOTAL:
            pct_row = []
            n_row = []
            for age in AGE_ORDER:
                cell = df[(df['year'] == year) & (df['race'] == race) & (df['age_bracket'] == age)]
                if len(cell) > 0:
                    pct_row.append(round(cell['pct_women'].values[0], 1) if pd.notna(cell['pct_women'].values[0]) else None)
                    n_row.append(int(cell['n'].values[0]) if pd.notna(cell['n'].values[0]) else None)
                else:
                    pct_row.append(None)
                    n_row.append(None)
            chart_data['data'][year]['pct'].append(pct_row)
            chart_data['data'][year]['n'].append(n_row)

    with open(OUTPUT_DIR / "nscg_chart.json", 'w') as f:
        json.dump(chart_data, f)

    print(f"Exported NSCG chart data")


def export_bigtech_chart():
    """Export Big Tech timeline data."""
    df = pd.read_csv("big_tech_diversity.csv")
    df['reporting_status'] = df['reporting_status'].str.strip()

    companies = ['Google', 'Apple', 'Microsoft', 'Meta', 'Amazon']

    chart_data = {
        'companies': companies,
        'colors': {
            'Google': '#4285F4', 'Apple': '#A2AAAD', 'Microsoft': '#00A4EF',
            'Meta': '#0668E1', 'Amazon': '#FF9900'
        },
        'data': {}
    }

    for company in companies:
        company_df = df[df['company'] == company].sort_values('year')
        chart_data['data'][company] = {
            'years': company_df['year'].tolist(),
            'technical': [None if pd.isna(v) else round(v, 1) for v in company_df['women_technical_pct']],
            'overall': [None if pd.isna(v) else round(v, 1) for v in company_df['women_overall_pct']],
            'status': company_df['reporting_status'].tolist()
        }

    with open(OUTPUT_DIR / "bigtech_chart.json", 'w') as f:
        json.dump(chart_data, f)

    print(f"Exported Big Tech chart data")


def export_ipeds_chart():
    """Export IPEDS pipeline data."""
    df = pd.read_csv("ipeds/processed_ipeds_csv_files/ipeds_national_by_track.csv")

    # Aggregate by track + year + award_label
    agg = df.groupby(['year', 'track', 'award_label']).agg({
        'CTOTALT': 'sum', 'CTOTALW': 'sum'
    }).reset_index()
    agg['pct_women'] = (agg['CTOTALW'] / agg['CTOTALT'] * 100).round(1)

    tracks = ['Computer Science', 'Cybersecurity', 'Computer Engineering',
              'Electrical Engineering', 'Information & Data Science', 'IT & General Computing']
    degrees = ["Associate's", "Bachelor's", "Master's", "Doctorate"]
    years = sorted(agg['year'].unique())

    chart_data = {
        'years': [int(y) for y in years],
        'tracks': tracks,
        'degrees': degrees,
        'colors': {
            "Associate's": '#76B7B2', "Bachelor's": '#59A14F',
            "Master's": '#EDC948', "Doctorate": '#B07AA1'
        },
        'data': {}
    }

    for track in tracks:
        chart_data['data'][track] = {}
        for degree in degrees:
            subset = agg[(agg['track'] == track) & (agg['award_label'] == degree)].sort_values('year')
            chart_data['data'][track][degree] = {
                'years': [int(y) for y in subset['year'].tolist()],
                'values': [v if pd.notna(v) else None for v in subset['pct_women'].tolist()]
            }

    with open(OUTPUT_DIR / "ipeds_chart.json", 'w') as f:
        json.dump(chart_data, f)

    print(f"Exported IPEDS chart data")


def main():
    print("Exporting chart data...")
    export_bls_chart()
    export_nscg_chart()
    export_bigtech_chart()
    export_ipeds_chart()
    print("Done!")


if __name__ == '__main__':
    main()
