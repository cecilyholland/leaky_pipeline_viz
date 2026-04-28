"""
Chart 4: IPEDS Education Pipeline
Line chart showing women % in computing degrees over time by track and degree level.

Run from repo root:
    python visualizations/chart4_ipeds_pipeline.py
"""

import pandas as pd
import plotly.graph_objects as go
from pathlib import Path

# Paths
DATA_PATH = Path("ipeds/processed_ipeds_csv_files/ipeds_national_by_track.csv")
OUTPUT_PATH = Path("visualizations/chart4_ipeds_pipeline.html")

# Colors by degree level
DEGREE_COLORS = {
    "Associate's": '#76B7B2',
    "Bachelor's": '#59A14F',
    "Master's": '#EDC948',
    'Doctorate': '#B07AA1',
}

# Main tracks to show in dropdown
MAIN_TRACKS = [
    'Computer Science',
    'Cybersecurity',
    'Computer Engineering',
    'Electrical Engineering',
    'Information & Data Science',
    'IT & General Computing',
]

# Degree level order
DEGREE_ORDER = ["Associate's", "Bachelor's", "Master's", "Doctorate"]


def load_data():
    """Load and prepare IPEDS data."""
    df = pd.read_csv(DATA_PATH)

    # Aggregate by track + year + award_label (some tracks have multiple CIPs)
    agg = df.groupby(['year', 'track', 'award_label']).agg({
        'CTOTALT': 'sum',
        'CTOTALW': 'sum',
        'CTOTALM': 'sum',
    }).reset_index()

    # Recalculate pct_women
    agg['pct_women'] = (agg['CTOTALW'] / agg['CTOTALT'] * 100).round(1)

    return agg


def create_chart(df):
    """Create the interactive line chart."""

    years = sorted(df['year'].unique())
    default_track = 'Computer Science'

    fig = go.Figure()

    # Create traces for each track × degree level
    trace_info = []  # Track (track, degree, trace_idx) for visibility toggling

    for track in MAIN_TRACKS:
        track_data = df[df['track'] == track]

        for degree in DEGREE_ORDER:
            degree_data = track_data[track_data['award_label'] == degree].sort_values('year')

            if degree_data.empty:
                continue

            is_default = (track == default_track)

            fig.add_trace(go.Scatter(
                x=degree_data['year'],
                y=degree_data['pct_women'],
                mode='lines+markers',
                name=degree,
                line=dict(color=DEGREE_COLORS[degree], width=2.5),
                marker=dict(size=8),
                hovertemplate=(
                    f'<b>{track}</b><br>' +
                    f'{degree}<br>' +
                    'Year: %{x}<br>' +
                    'Women: %{y:.1f}%<br>' +
                    '<extra></extra>'
                ),
                legendgroup=degree,
                showlegend=is_default,
                visible=is_default,
            ))

            trace_info.append((track, degree, len(fig.data) - 1))

    # Create dropdown buttons for track selection
    dropdown_buttons = []
    for track in MAIN_TRACKS:
        # Set visibility: show only traces for this track
        visibility = [info[0] == track for info in trace_info]

        # Also update which traces show in legend (first occurrence of each degree)
        shown_degrees = set()
        showlegend_updates = []
        for info in trace_info:
            if info[0] == track and info[1] not in shown_degrees:
                showlegend_updates.append(True)
                shown_degrees.add(info[1])
            else:
                showlegend_updates.append(info[0] == track)

        dropdown_buttons.append(dict(
            args=[
                {'visible': visibility},
                {'title.text': f'Women in {track} by Degree Level'}
            ],
            label=track,
            method='update'
        ))

    # Calculate change annotation for default track
    cs_bachelors = df[(df['track'] == default_track) & (df['award_label'] == "Bachelor's")]
    if not cs_bachelors.empty:
        first_year = cs_bachelors['year'].min()
        last_year = cs_bachelors['year'].max()
        first_pct = cs_bachelors[cs_bachelors['year'] == first_year]['pct_women'].values[0]
        last_pct = cs_bachelors[cs_bachelors['year'] == last_year]['pct_women'].values[0]
        change = last_pct - first_pct
        change_text = f'+{change:.1f}pp since {first_year}' if change > 0 else f'{change:.1f}pp since {first_year}'

    # Layout
    fig.update_layout(
        title=dict(
            text=f'Women in {default_track} by Degree Level',
            font=dict(size=20),
            x=0.5,
            xanchor='center',
        ),
        xaxis=dict(
            title='Year',
            tickfont=dict(size=12),
            tickmode='array',
            tickvals=years,
            ticktext=[str(y) for y in years],
        ),
        yaxis=dict(
            title='% Women',
            tickfont=dict(size=12),
            range=[0, 35],
            ticksuffix='%',
        ),
        updatemenus=[
            dict(
                active=0,
                buttons=dropdown_buttons,
                direction='down',
                pad=dict(r=10, t=10),
                showactive=True,
                x=0.0,
                xanchor='left',
                y=1.12,
                yanchor='top',
                bgcolor='white',
                bordercolor='#666',
                font=dict(size=12),
            )
        ],
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=-0.18,
            xanchor='center',
            x=0.5,
            title=dict(text='Degree Level'),
        ),
        margin=dict(t=120, b=100, l=60, r=40),
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(family='Arial, sans-serif'),
        hovermode='x unified',

        # Annotation for change
        annotations=[
            dict(
                x=last_year,
                y=last_pct,
                xref='x',
                yref='y',
                text=change_text,
                showarrow=True,
                arrowhead=2,
                ax=50,
                ay=-30,
                font=dict(size=11, color='#666'),
            )
        ] if not cs_bachelors.empty else [],
    )

    # Grid
    fig.update_xaxes(showgrid=True, gridcolor='#eee', showline=True, linecolor='#ccc')
    fig.update_yaxes(showgrid=True, gridcolor='#eee', showline=True, linecolor='#ccc')

    return fig


def main():
    print("Loading IPEDS data...")
    df = load_data()
    print(f"  {len(df)} rows loaded")
    print(f"  Years: {sorted(df['year'].unique())}")
    print(f"  Tracks: {sorted(df['track'].unique())}")

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
