"""
Chart 1: BLS Age Cliff
Interactive bar chart showing women in tech by age bracket, occupation, and year.

Run from repo root:
    python visualizations/chart1_bls_age_cliff.py
"""

import pandas as pd
import plotly.graph_objects as go
from pathlib import Path

# Paths
DATA_PATH = Path("bls/processed_bls_data/bls_combined_clean.csv")
OUTPUT_PATH = Path("visualizations/chart1_bls_age_cliff.html")

# Colors
COLORS = {
    'women': '#E15759',
    'men': '#4E79A7',
    'highlight': '#F28E2B',
}

# Age bracket display order and labels
AGE_ORDER = ['age_16_19', 'age_20_24', 'age_25_34', 'age_35_44', 'age_45_54', 'age_55_64', 'age_65_plus']
AGE_LABELS = {
    'age_16_19': '16-19',
    'age_20_24': '20-24',
    'age_25_34': '25-34',
    'age_35_44': '35-44',
    'age_45_54': '45-54',
    'age_55_64': '55-64',
    'age_65_plus': '65+',
}

# Occupation display names
OCC_LABELS = {
    'Software Developers': 'Software Developers',
    'CS & Math (all)': 'All Computer & Math Occupations',
    'Computer Systems Analysts': 'Computer Systems Analysts',
    'Database Administrators': 'Database Administrators',
    'Information Security Analysts': 'Information Security Analysts',
    'Computer Programmers': 'Computer Programmers',
    'Network & Systems Admins': 'Network & Systems Admins',
    'Computer Support Specialists': 'Computer Support Specialists',
    'Web Developers': 'Web Developers',
    'Computer Network Architects': 'Computer Network Architects',
    'Computer Hardware Engineers': 'Computer Hardware Engineers',
    'CS Managers': 'Computer & IS Managers',
}


def load_data():
    """Load and prepare BLS data."""
    df = pd.read_csv(DATA_PATH)

    # Filter out 'total' rows
    df = df[df['age_bracket'] != 'total'].copy()

    # Calculate men count
    df['men_count_k_approx'] = df['count_k'] - df['women_count_k_approx']

    # Add display labels
    df['age_label'] = df['age_bracket'].map(AGE_LABELS)
    df['occ_label'] = df['occupation'].map(OCC_LABELS)

    return df


def create_chart(df):
    """Create the interactive Plotly chart."""
    return create_chart_v2(df)


def create_chart_v2(df):
    """Create chart using animation frames for years and dropdown for occupation."""

    years = sorted(df['year'].unique())
    occupations = ['Software Developers', 'CS & Math (all)', 'Computer Systems Analysts',
                   'Database Administrators', 'Information Security Analysts',
                   'Computer Programmers', 'Network & Systems Admins']

    default_occ = 'Software Developers'

    fig = go.Figure()

    # Add initial trace for default occupation, latest year
    init_data = df[(df['occupation'] == default_occ) & (df['year'] == years[-1])].copy()
    init_data = init_data.set_index('age_bracket').reindex(AGE_ORDER).reset_index()

    # Calculate peak and cliff for annotation
    peak_idx = init_data['women_count_k_approx'].idxmax()
    peak_bracket = init_data.loc[peak_idx, 'age_label']
    peak_value = init_data.loc[peak_idx, 'women_count_k_approx']

    # Women bars
    fig.add_trace(go.Bar(
        name='Women (estimated)',
        x=init_data['age_label'],
        y=init_data['women_count_k_approx'],
        marker_color=COLORS['women'],
        hovertemplate='<b>Age %{x}</b><br>Women: %{y:.0f}k<extra></extra>',
    ))

    # Create frames for animation (years)
    frames = []
    for year in years:
        year_data = df[(df['occupation'] == default_occ) & (df['year'] == year)].copy()
        year_data = year_data.set_index('age_bracket').reindex(AGE_ORDER).reset_index()

        frames.append(go.Frame(
            data=[go.Bar(
                x=year_data['age_label'],
                y=year_data['women_count_k_approx'],
                marker_color=COLORS['women'],
            )],
            name=str(year),
        ))

    fig.frames = frames

    # Create dropdown buttons for occupation
    dropdown_buttons = []
    for occ in occupations:
        # Get latest year data for this occupation
        occ_data = df[(df['occupation'] == occ) & (df['year'] == years[-1])].copy()
        occ_data = occ_data.set_index('age_bracket').reindex(AGE_ORDER).reset_index()

        # Create new frames for this occupation
        new_frames = []
        for year in years:
            year_data = df[(df['occupation'] == occ) & (df['year'] == year)].copy()
            year_data = year_data.set_index('age_bracket').reindex(AGE_ORDER).reset_index()
            new_frames.append(go.Frame(
                data=[go.Bar(
                    x=year_data['age_label'],
                    y=year_data['women_count_k_approx'],
                    marker_color=COLORS['women'],
                )],
                name=str(year),
            ))

        dropdown_buttons.append(dict(
            args=[
                {'y': [occ_data['women_count_k_approx']]},
                {'title.text': f'Women in Tech by Age: {OCC_LABELS.get(occ, occ)}'}
            ],
            label=OCC_LABELS.get(occ, occ),
            method='update'
        ))

    # Animation slider
    sliders = [dict(
        active=len(years) - 1,
        yanchor='top',
        xanchor='left',
        currentvalue=dict(
            font=dict(size=16),
            prefix='Year: ',
            visible=True,
            xanchor='right'
        ),
        transition=dict(duration=300),
        pad=dict(b=10, t=50),
        len=0.9,
        x=0.05,
        y=0,
        steps=[
            dict(
                args=[[str(year)], dict(
                    frame=dict(duration=300, redraw=True),
                    mode='immediate',
                    transition=dict(duration=300)
                )],
                label=str(year),
                method='animate'
            )
            for year in years
        ]
    )]

    # Play/pause buttons
    updatemenus = [
        # Play/Pause buttons
        dict(
            type='buttons',
            showactive=False,
            y=0,
            x=0.0,
            xanchor='right',
            yanchor='top',
            pad=dict(t=50, r=10),
            buttons=[
                dict(
                    label='▶ Play',
                    method='animate',
                    args=[None, dict(
                        frame=dict(duration=500, redraw=True),
                        fromcurrent=True,
                        transition=dict(duration=300)
                    )]
                ),
                dict(
                    label='⏸ Pause',
                    method='animate',
                    args=[[None], dict(
                        frame=dict(duration=0, redraw=False),
                        mode='immediate',
                        transition=dict(duration=0)
                    )]
                )
            ]
        ),
        # Occupation dropdown
        dict(
            active=0,
            buttons=dropdown_buttons,
            direction='down',
            pad=dict(r=10, t=10),
            showactive=True,
            x=0.0,
            xanchor='left',
            y=1.15,
            yanchor='top',
            bgcolor='white',
            bordercolor='#666',
            font=dict(size=12),
        )
    ]

    # Layout
    fig.update_layout(
        title=dict(
            text=f'Women in Tech by Age: {OCC_LABELS[default_occ]}',
            font=dict(size=20),
            x=0.5,
            xanchor='center',
        ),
        xaxis=dict(
            title='Age Bracket',
            tickfont=dict(size=12),
        ),
        yaxis=dict(
            title='Employment (thousands)',
            tickfont=dict(size=12),
            rangemode='tozero',
        ),
        updatemenus=updatemenus,
        sliders=sliders,
        showlegend=True,
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=1.02,
            xanchor='right',
            x=1
        ),
        margin=dict(t=150, b=100, l=60, r=40),
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(family='Arial, sans-serif'),

        # Add annotation for the cliff
        annotations=[
            dict(
                x='35-44',
                y=0,
                xref='x',
                yref='paper',
                text='← The Cliff: Sharp drop after 25-34',
                showarrow=True,
                arrowhead=2,
                ax=80,
                ay=-30,
                font=dict(size=11, color='#666'),
            )
        ]
    )

    # Grid lines
    fig.update_xaxes(showgrid=False, showline=True, linecolor='#ccc')
    fig.update_yaxes(showgrid=True, gridcolor='#eee', showline=True, linecolor='#ccc')

    return fig


def main():
    print("Loading BLS data...")
    df = load_data()
    print(f"  {len(df)} rows loaded")

    print("Creating interactive chart...")
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
