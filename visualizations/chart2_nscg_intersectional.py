"""
Chart 2: NSCG Intersectional Heatmap
Heatmap showing women in computing by race × age bracket.

Run from repo root:
    python visualizations/chart2_nscg_intersectional.py
"""

import pandas as pd
import plotly.graph_objects as go
from pathlib import Path
import numpy as np

# Paths
DATA_PATH = Path("ncses/processed_nscg_data/nscg_intersectional_cliff.csv")
OUTPUT_PATH = Path("visualizations/chart2_nscg_intersectional.html")

# Age bracket order
AGE_ORDER = ['Under 25', '25-34', '35-44', '45-54', '55-64', '65+']

# Race display order (with Total at bottom)
RACE_ORDER = ['Asian', 'Black', 'Hispanic', 'Multiracial', 'White', 'All Women']

# Color scales
COLORSCALE_PCT = 'YlOrRd'
COLORSCALE_CHANGE = 'RdYlGn'


def load_data():
    """Load and prepare NSCG intersectional data, adding total row."""
    df = pd.read_csv(DATA_PATH)

    # Calculate "All Women" totals by year and age bracket
    totals = df.groupby(['year', 'age_bracket']).agg({
        'n': 'sum',
        'pct_women': lambda x: np.average(x, weights=df.loc[x.index, 'n'])
    }).reset_index()
    totals['race'] = 'All Women'
    totals['pct_women'] = totals['pct_women'].round(1)

    # Combine
    df = pd.concat([df, totals], ignore_index=True)

    return df


def create_matrix(df, year):
    """Create a matrix of pct_women values for heatmap."""
    matrix_df = df[df['year'] == year].pivot(
        index='race',
        columns='age_bracket',
        values='pct_women'
    )
    matrix_df = matrix_df.reindex(index=RACE_ORDER, columns=AGE_ORDER)
    return matrix_df


def create_n_matrix(df, year):
    """Create matrix of sample sizes for hover info."""
    matrix_df = df[df['year'] == year].pivot(
        index='race',
        columns='age_bracket',
        values='n'
    )
    matrix_df = matrix_df.reindex(index=RACE_ORDER, columns=AGE_ORDER)
    return matrix_df


def create_chart(df):
    """Create the interactive heatmap."""

    years = sorted(df['year'].unique())

    # Create matrices for each year
    matrices = {year: create_matrix(df, year) for year in years}
    n_matrices = {year: create_n_matrix(df, year) for year in years}

    # Calculate change matrix (2023 - 2019)
    change_matrix = matrices[2023] - matrices[2019] if 2019 in years and 2023 in years else None

    # Create custom hover text
    def make_hover_text(z, n, year_label):
        hover = []
        for i, race in enumerate(RACE_ORDER):
            row = []
            for j, age in enumerate(AGE_ORDER):
                val = z[i, j]
                n_val = n[i, j] if not np.isnan(n[i, j]) else 0
                if np.isnan(val):
                    row.append(f'{race}, {age}<br>Suppressed (n < 20)')
                else:
                    row.append(f'{race}, {age}<br>{val:.1f}% women<br>n = {int(n_val)}<br>{year_label}')
            hover.append(row)
        return hover

    hover_2023 = make_hover_text(matrices[2023].values, n_matrices[2023].values, '2023')
    hover_2019 = make_hover_text(matrices[2019].values, n_matrices[2019].values, '2019')

    # Change hover text
    hover_change = []
    if change_matrix is not None:
        for i, race in enumerate(RACE_ORDER):
            row = []
            for j, age in enumerate(AGE_ORDER):
                delta = change_matrix.values[i, j]
                val_2019 = matrices[2019].values[i, j]
                val_2023 = matrices[2023].values[i, j]
                if np.isnan(delta):
                    row.append(f'{race}, {age}<br>Change unavailable')
                else:
                    sign = '+' if delta > 0 else ''
                    row.append(f'{race}, {age}<br>Change: {sign}{delta:.1f}pp<br>2019: {val_2019:.1f}%<br>2023: {val_2023:.1f}%')
            hover_change.append(row)

    fig = go.Figure()

    # Add heatmap for 2023 (default visible)
    fig.add_trace(go.Heatmap(
        z=matrices[2023].values,
        x=AGE_ORDER,
        y=RACE_ORDER,
        colorscale=COLORSCALE_PCT,
        zmin=10,
        zmax=45,
        text=hover_2023,
        hoverinfo='text',
        colorbar=dict(title=dict(text='% Women', side='right')),
        visible=True,
        name='2023',
    ))

    # Add heatmap for 2019
    fig.add_trace(go.Heatmap(
        z=matrices[2019].values,
        x=AGE_ORDER,
        y=RACE_ORDER,
        colorscale=COLORSCALE_PCT,
        zmin=10,
        zmax=45,
        text=hover_2019,
        hoverinfo='text',
        colorbar=dict(title=dict(text='% Women', side='right')),
        visible=False,
        name='2019',
    ))

    # Add change heatmap
    if change_matrix is not None:
        fig.add_trace(go.Heatmap(
            z=change_matrix.values,
            x=AGE_ORDER,
            y=RACE_ORDER,
            colorscale=COLORSCALE_CHANGE,
            zmid=0,
            zmin=-15,
            zmax=15,
            text=hover_change,
            hoverinfo='text',
            colorbar=dict(title=dict(text='Change (pp)', side='right')),
            visible=False,
            name='Change',
        ))

    # Build cell annotations for each view
    def make_annotations(matrix, is_change=False):
        annotations = []
        for i, race in enumerate(RACE_ORDER):
            for j, age in enumerate(AGE_ORDER):
                val = matrix.values[i, j]
                if np.isnan(val):
                    text = '--'
                    color = '#666'
                elif is_change:
                    sign = '+' if val > 0 else ''
                    text = f'{sign}{val:.0f}'
                    color = 'white' if abs(val) > 8 else 'black'
                else:
                    text = f'{val:.0f}%'
                    color = 'white' if val > 30 else 'black'

                annotations.append(dict(
                    x=age, y=race, text=text,
                    font=dict(color=color, size=12),
                    showarrow=False,
                ))
        return annotations

    annotations_2023 = make_annotations(matrices[2023])
    annotations_2019 = make_annotations(matrices[2019])
    annotations_change = make_annotations(change_matrix, is_change=True) if change_matrix is not None else []

    # Create dropdown menu for view selection
    buttons = [
        dict(
            args=[
                {'visible': [True, False, False]},
                {'annotations': annotations_2023,
                 'title.text': 'Women in Computing by Race & Age (2023)'}
            ],
            label='2023   ',
            method='update'
        ),
        dict(
            args=[
                {'visible': [False, True, False]},
                {'annotations': annotations_2019,
                 'title.text': 'Women in Computing by Race & Age (2019)'}
            ],
            label='2019   ',
            method='update'
        ),
        dict(
            args=[
                {'visible': [False, False, True]},
                {'annotations': annotations_change,
                 'title.text': 'Change in Women % (2019 to 2023)'}
            ],
            label='Change ',
            method='update'
        ),
    ]

    # Layout
    fig.update_layout(
        title=dict(
            text='Women in Computing by Race & Age (2023)',
            font=dict(size=18),
            x=0.5,
            xanchor='center',
        ),
        xaxis=dict(
            title='Age Bracket',
            tickfont=dict(size=12),
            side='bottom',
        ),
        yaxis=dict(
            title='Race/Ethnicity',
            tickfont=dict(size=12),
            autorange='reversed',
        ),
        updatemenus=[
            dict(
                type='dropdown',
                active=0,
                x=0.0,
                xanchor='left',
                y=1.18,
                yanchor='top',
                buttons=buttons,
                pad=dict(r=10, t=10),
                showactive=True,
                bgcolor='white',
                bordercolor='#666',
                borderwidth=1,
                font=dict(size=12),
            )
        ],
        annotations=annotations_2023,
        margin=dict(t=120, b=100, l=120, r=80),
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(family='Arial, sans-serif'),
        width=850,
        height=550,
    )

    # Add note about suppression
    fig.add_annotation(
        text='Gray cells (--) = sample size < 20, suppressed per NCSES guidelines. "All Women" row shows weighted average across all races.',
        xref='paper', yref='paper',
        x=0.5, y=-0.22,
        showarrow=False,
        font=dict(size=10, color='#666'),
        xanchor='center',
    )

    return fig


def main():
    print("Loading NSCG intersectional data...")
    df = load_data()
    print(f"  {len(df)} rows loaded")
    print(f"  Years: {sorted(df['year'].unique())}")
    print(f"  Races: {sorted(df['race'].unique())}")

    print("Creating interactive heatmap...")
    fig = create_chart(df)

    print(f"Saving to {OUTPUT_PATH}...")
    fig.write_html(
        OUTPUT_PATH,
        include_plotlyjs=True,
        full_html=True,
        config={
            'displayModeBar': True,
            'toImageButtonOptions': {'format': 'png', 'scale': 2},
            'modeBarButtonsToRemove': ['lasso2d', 'select2d'],
        }
    )

    print(f"Done! Open {OUTPUT_PATH} in a browser.")


if __name__ == '__main__':
    main()
