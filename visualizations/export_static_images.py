"""
Export all interactive Plotly charts as static PNG images for the report.

Requires: pip install kaleido

Run from repo root:
    python visualizations/export_static_images.py
"""

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from pathlib import Path
import sys

# Check for kaleido
try:
    import kaleido
    print("kaleido installed")
except ImportError:
    print("ERROR: kaleido not installed.")
    print("Install with: pip install -U kaleido")
    print("Or: conda install -c conda-forge python-kaleido")
    sys.exit(1)

# Output directory
OUTPUT_DIR = Path("visualizations/figures")
OUTPUT_DIR.mkdir(exist_ok=True)

# Image settings
WIDTH = 1200
HEIGHT = 800
SCALE = 2  # 2x for high-res

# Colors
COLORS = {
    'women': '#E15759',
    'men': '#4E79A7',
}

COMPANY_COLORS = {
    'Google': '#4285F4',
    'Apple': '#A2AAAD',
    'Microsoft': '#00A4EF',
    'Meta': '#0668E1',
    'Amazon': '#FF9900',
}

# =============================================================================
# Chart 1: BLS Age Cliff
# =============================================================================

def create_bls_age_cliff():
    """Create static version of BLS age cliff chart."""
    print("\n1. Creating BLS Age Cliff chart...")

    df = pd.read_csv("bls/processed_bls_data/bls_combined_clean.csv")
    df = df[df['age_bracket'] != 'total'].copy()

    # Calculate women count
    df['women_count_k'] = df['count_k'] * df['pct_women'] / 100

    # Age order and labels
    age_order = ['age_16_19', 'age_20_24', 'age_25_34', 'age_35_44', 'age_45_54', 'age_55_64', 'age_65_plus']
    age_labels = {
        'age_16_19': '16-19', 'age_20_24': '20-24', 'age_25_34': '25-34',
        'age_35_44': '35-44', 'age_45_54': '45-54', 'age_55_64': '55-64', 'age_65_plus': '65+'
    }

    # Filter to Software Developers, 2024
    data = df[(df['occupation'] == 'Software Developers') & (df['year'] == 2024)].copy()
    data['age_label'] = data['age_bracket'].map(age_labels)
    data = data.set_index('age_bracket').reindex(age_order).reset_index()

    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=data['age_label'],
        y=data['women_count_k'],
        marker_color=COLORS['women'],
        name='Women (estimated)',
        text=data['women_count_k'].round(0).astype(int),
        textposition='outside',
    ))

    fig.update_layout(
        title=dict(
            text='<b>Women in Software Development by Age (2024)</b><br><sup>The Mid-Career Cliff: Sharp decline after ages 25-34</sup>',
            font=dict(size=20),
            x=0.5,
        ),
        xaxis=dict(title='Age Bracket', tickfont=dict(size=14)),
        yaxis=dict(title='Employment (thousands)', tickfont=dict(size=14), rangemode='tozero'),
        showlegend=False,
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(family='Arial, sans-serif'),
        margin=dict(t=100, b=80, l=80, r=40),
        annotations=[
            dict(
                x='35-44', y=0.95, xref='x', yref='paper',
                text='<b>The Cliff</b><br>24% drop from peak',
                showarrow=True, arrowhead=2, ax=80, ay=-40,
                font=dict(size=12, color='#666'),
                bgcolor='white', bordercolor='#ccc', borderwidth=1,
            )
        ]
    )

    fig.update_xaxes(showgrid=False, showline=True, linecolor='#ccc')
    fig.update_yaxes(showgrid=True, gridcolor='#eee', showline=True, linecolor='#ccc')

    output_path = OUTPUT_DIR / "chart1_bls_age_cliff.png"
    fig.write_image(str(output_path), width=WIDTH, height=HEIGHT, scale=SCALE)
    print(f"   Saved: {output_path}")

    return fig

# =============================================================================
# Chart 2: NSCG Intersectional Heatmap
# =============================================================================

def create_nscg_heatmap():
    """Create static version of NSCG intersectional heatmap."""
    print("\n2. Creating NSCG Intersectional Heatmap...")

    df = pd.read_csv("ncses/processed_nscg_data/nscg_intersectional_cliff.csv")

    # Filter to 2023
    df_2023 = df[df['year'] == 2023].copy()

    # Pivot for heatmap
    pivot = df_2023.pivot(index='race', columns='age_bracket', values='pct_women')

    # Reorder columns and rows
    col_order = ['Under 25', '25-34', '35-44', '45-54', '55-64', '65+']
    row_order = ['Asian', 'Black', 'Hispanic', 'Multiracial', 'White']

    # Reindex with available columns/rows
    available_cols = [c for c in col_order if c in pivot.columns]
    available_rows = [r for r in row_order if r in pivot.index]
    pivot = pivot.reindex(index=available_rows, columns=available_cols)

    # Create annotations
    annotations = []
    for i, race in enumerate(pivot.index):
        for j, age in enumerate(pivot.columns):
            val = pivot.loc[race, age]
            if pd.notna(val):
                annotations.append(dict(
                    x=j, y=i,
                    text=f'{val:.1f}%',
                    font=dict(size=12, color='white' if val > 30 else 'black'),
                    showarrow=False,
                ))
            else:
                annotations.append(dict(
                    x=j, y=i,
                    text='--',
                    font=dict(size=12, color='#666'),
                    showarrow=False,
                ))

    fig = go.Figure(data=go.Heatmap(
        z=pivot.values,
        x=pivot.columns.tolist(),
        y=pivot.index.tolist(),
        colorscale='YlOrRd',
        showscale=True,
        colorbar=dict(title='% Women', ticksuffix='%'),
        hoverongaps=False,
    ))

    fig.update_layout(
        title=dict(
            text='<b>Women in Computing by Race and Age (2023)</b><br><sup>NSCG Survey Data | Gray cells indicate insufficient sample size (n < 20)</sup>',
            font=dict(size=20),
            x=0.5,
        ),
        xaxis=dict(title='Age Bracket', tickfont=dict(size=14), side='bottom'),
        yaxis=dict(title='Race/Ethnicity', tickfont=dict(size=14), autorange='reversed'),
        annotations=annotations,
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(family='Arial, sans-serif'),
        margin=dict(t=100, b=80, l=120, r=100),
    )

    output_path = OUTPUT_DIR / "chart2_nscg_intersectional.png"
    fig.write_image(str(output_path), width=WIDTH, height=600, scale=SCALE)
    print(f"   Saved: {output_path}")

    return fig

# =============================================================================
# Chart 3: Big Tech Timeline
# =============================================================================

def create_bigtech_timeline():
    """Create static version of Big Tech timeline chart."""
    print("\n3. Creating Big Tech Timeline chart...")

    df = pd.read_csv("big_tech_diversity.csv")
    df['reporting_status'] = df['reporting_status'].str.strip()

    companies = ['Google', 'Apple', 'Microsoft', 'Meta', 'Amazon']

    fig = go.Figure()

    for company in companies:
        company_data = df[df['company'] == company].sort_values('year')

        # Technical roles (main focus)
        tech_data = company_data[company_data['women_technical_pct'].notna()]
        reported = tech_data[tech_data['reporting_status'] == 'reported']

        if not reported.empty:
            fig.add_trace(go.Scatter(
                x=reported['year'],
                y=reported['women_technical_pct'],
                mode='lines+markers',
                name=company,
                line=dict(color=COMPANY_COLORS[company], width=3),
                marker=dict(size=10, symbol='circle'),
            ))

    # Add markers for 2025 status
    for company in companies:
        company_data = df[(df['company'] == company) & (df['year'] == 2025)]
        if not company_data.empty:
            status = company_data['reporting_status'].values[0].strip()

            # Get last known tech value
            all_company = df[df['company'] == company]
            tech_vals = all_company[all_company['women_technical_pct'].notna()]['women_technical_pct']
            if len(tech_vals) > 0:
                last_tech = tech_vals.iloc[-1]
                symbol = 'star' if status == 'still_reporting' else 'x'

                fig.add_trace(go.Scatter(
                    x=[2025],
                    y=[last_tech],
                    mode='markers',
                    marker=dict(
                        size=16 if symbol == 'star' else 14,
                        symbol=symbol,
                        color=COMPANY_COLORS[company],
                        line=dict(width=2, color='white'),
                    ),
                    showlegend=False,
                ))

    # Vertical line at 2024.5
    fig.add_vline(x=2024.5, line=dict(color='#888', width=2, dash='dash'))

    fig.add_annotation(
        x=2024.5, y=38, xref='x', yref='y',
        text='<b>DEI Reporting</b><br><b>Cliff</b>',
        showarrow=False,
        font=dict(size=11, color='#666'),
        xanchor='left', xshift=8,
    )

    fig.update_layout(
        title=dict(
            text='<b>Big Tech Diversity Reporting: The Data Cliff</b><br><sup>Women in Technical Roles (%) | X = Stopped reporting | Star = Continuing</sup>',
            font=dict(size=20),
            x=0.5,
        ),
        xaxis=dict(title='Year', tickfont=dict(size=14), dtick=2, range=[2013.5, 2026]),
        yaxis=dict(title='% Women in Technical Roles', tickfont=dict(size=14), range=[10, 40], ticksuffix='%'),
        legend=dict(
            orientation='h', yanchor='top', y=-0.15, xanchor='center', x=0.5,
            font=dict(size=12),
        ),
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(family='Arial, sans-serif'),
        margin=dict(t=100, b=120, l=80, r=40),
    )

    fig.update_xaxes(showgrid=True, gridcolor='#eee', showline=True, linecolor='#ccc')
    fig.update_yaxes(showgrid=True, gridcolor='#eee', showline=True, linecolor='#ccc')

    # Add note
    fig.add_annotation(
        text='Note: Amazon reports overall workforce only (no technical breakdown)',
        xref='paper', yref='paper', x=0.5, y=-0.25,
        showarrow=False, font=dict(size=10, color='#666'), xanchor='center',
    )

    output_path = OUTPUT_DIR / "chart3_bigtech_timeline.png"
    fig.write_image(str(output_path), width=WIDTH, height=HEIGHT, scale=SCALE)
    print(f"   Saved: {output_path}")

    return fig

# =============================================================================
# Chart 4: IPEDS Education Pipeline
# =============================================================================

def create_ipeds_pipeline():
    """Create static version of IPEDS education pipeline chart."""
    print("\n4. Creating IPEDS Education Pipeline chart...")

    df = pd.read_csv("ipeds/processed_ipeds_csv_files/ipeds_bachelors_by_track.csv")

    # Select key tracks
    tracks = ['Computer Science', 'Cybersecurity', 'Information & Data Science',
              'IT & General Computing', 'Software & Media Applications']

    track_colors = {
        'Computer Science': '#4E79A7',
        'Cybersecurity': '#E15759',
        'Information & Data Science': '#59A14F',
        'IT & General Computing': '#EDC948',
        'Software & Media Applications': '#B07AA1',
    }

    fig = go.Figure()

    for track in tracks:
        track_data = df[df['track'] == track].sort_values('year')

        fig.add_trace(go.Scatter(
            x=track_data['year'],
            y=track_data['pct_women'],
            mode='lines+markers',
            name=track,
            line=dict(color=track_colors.get(track, '#666'), width=3),
            marker=dict(size=10),
        ))

    fig.update_layout(
        title=dict(
            text="<b>Women in Computing Education: Bachelor's Degrees</b><br><sup>Percentage of degrees awarded to women by field, 2010-2024</sup>",
            font=dict(size=20),
            x=0.5,
        ),
        xaxis=dict(title='Year', tickfont=dict(size=14), dtick=3),
        yaxis=dict(title="% Women (Bachelor's)", tickfont=dict(size=14), range=[0, 50], ticksuffix='%'),
        legend=dict(
            orientation='h', yanchor='top', y=-0.15, xanchor='center', x=0.5,
            font=dict(size=11),
        ),
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(family='Arial, sans-serif'),
        margin=dict(t=100, b=140, l=80, r=40),
    )

    fig.update_xaxes(showgrid=True, gridcolor='#eee', showline=True, linecolor='#ccc')
    fig.update_yaxes(showgrid=True, gridcolor='#eee', showline=True, linecolor='#ccc')

    # Add annotation for CS progress
    fig.add_annotation(
        x=2024, y=21.6, xref='x', yref='y',
        text='CS: +8.8pp<br>in 14 years',
        showarrow=True, arrowhead=2, ax=-60, ay=-40,
        font=dict(size=10, color='#666'),
        bgcolor='white', bordercolor='#ccc', borderwidth=1,
    )

    output_path = OUTPUT_DIR / "chart4_ipeds_pipeline.png"
    fig.write_image(str(output_path), width=WIDTH, height=HEIGHT, scale=SCALE)
    print(f"   Saved: {output_path}")

    return fig

# =============================================================================
# Chart 5: BLS Workforce Trends (Supplementary)
# =============================================================================

def create_bls_trends():
    """Create supplementary chart showing workforce trends over time."""
    print("\n5. Creating BLS Workforce Trends chart...")

    df = pd.read_csv("bls/processed_bls_data/bls_tech_by_sex.csv")

    occupations = ['Software Developers', 'CS & Math (all)', 'Computer Systems Analysts',
                   'Information Security Analysts']

    occ_colors = {
        'Software Developers': '#4E79A7',
        'CS & Math (all)': '#E15759',
        'Computer Systems Analysts': '#59A14F',
        'Information Security Analysts': '#EDC948',
    }

    fig = go.Figure()

    for occ in occupations:
        occ_data = df[df['occupation'] == occ].sort_values('year')

        fig.add_trace(go.Scatter(
            x=occ_data['year'],
            y=occ_data['pct_women'],
            mode='lines+markers',
            name=occ,
            line=dict(color=occ_colors.get(occ, '#666'), width=3),
            marker=dict(size=8),
        ))

    fig.update_layout(
        title=dict(
            text='<b>Women in Tech Occupations Over Time</b><br><sup>BLS Current Population Survey, 2015-2024</sup>',
            font=dict(size=20),
            x=0.5,
        ),
        xaxis=dict(title='Year', tickfont=dict(size=14), dtick=2),
        yaxis=dict(title='% Women', tickfont=dict(size=14), range=[15, 45], ticksuffix='%'),
        legend=dict(
            orientation='h', yanchor='top', y=-0.15, xanchor='center', x=0.5,
            font=dict(size=11),
        ),
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(family='Arial, sans-serif'),
        margin=dict(t=100, b=120, l=80, r=40),
    )

    fig.update_xaxes(showgrid=True, gridcolor='#eee', showline=True, linecolor='#ccc')
    fig.update_yaxes(showgrid=True, gridcolor='#eee', showline=True, linecolor='#ccc')

    output_path = OUTPUT_DIR / "chart5_bls_trends.png"
    fig.write_image(str(output_path), width=WIDTH, height=HEIGHT, scale=SCALE)
    print(f"   Saved: {output_path}")

    return fig

# =============================================================================
# Chart 6: IPEDS Degree Ladder (Supplementary)
# =============================================================================

def create_degree_ladder():
    """Create chart showing women % across degree levels for CS."""
    print("\n6. Creating IPEDS Degree Ladder chart...")

    df = pd.read_csv("ipeds/processed_ipeds_csv_files/ipeds_national_by_track.csv")

    # Filter to CS, latest year
    cs_data = df[(df['track'] == 'Computer Science') & (df['year'] == 2024)].copy()

    degree_order = ["Associate's", "Bachelor's", "Master's", "Doctorate"]
    cs_data = cs_data.set_index('award_label').reindex(degree_order).reset_index()

    colors = ['#76B7B2', '#59A14F', '#EDC948', '#B07AA1']

    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=cs_data['award_label'],
        y=cs_data['pct_women'],
        marker_color=colors,
        text=cs_data['pct_women'].round(1).astype(str) + '%',
        textposition='outside',
    ))

    fig.update_layout(
        title=dict(
            text='<b>Women in Computer Science by Degree Level (2024)</b><br><sup>Percentage of degrees awarded to women</sup>',
            font=dict(size=20),
            x=0.5,
        ),
        xaxis=dict(title='Degree Level', tickfont=dict(size=14)),
        yaxis=dict(title='% Women', tickfont=dict(size=14), range=[0, 40], ticksuffix='%'),
        showlegend=False,
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(family='Arial, sans-serif'),
        margin=dict(t=100, b=80, l=80, r=40),
    )

    fig.update_xaxes(showgrid=False, showline=True, linecolor='#ccc')
    fig.update_yaxes(showgrid=True, gridcolor='#eee', showline=True, linecolor='#ccc')

    output_path = OUTPUT_DIR / "chart6_degree_ladder.png"
    fig.write_image(str(output_path), width=WIDTH, height=600, scale=SCALE)
    print(f"   Saved: {output_path}")

    return fig

# =============================================================================
# Main
# =============================================================================

def main():
    print("=" * 60)
    print("Exporting Static Images for Report")
    print("=" * 60)
    print(f"Output directory: {OUTPUT_DIR.absolute()}")

    create_bls_age_cliff()
    create_nscg_heatmap()
    create_bigtech_timeline()
    create_ipeds_pipeline()
    create_bls_trends()
    create_degree_ladder()

    print("\n" + "=" * 60)
    print("All images exported successfully!")
    print("=" * 60)
    print(f"\nFiles saved to: {OUTPUT_DIR.absolute()}")
    print("\nTo use in LaTeX, copy the figures folder to your Overleaf project")
    print("and update the \\includegraphics paths in project_report.tex")


if __name__ == '__main__':
    main()
