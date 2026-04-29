"""
Chart 3: Big Tech Timeline
Multi-line chart showing women % in tech companies over time,
highlighting the "data cliff" where companies stopped reporting.

Run from repo root:
    python visualizations/chart3_bigtech_timeline.py
"""

import pandas as pd
import plotly.graph_objects as go
from pathlib import Path

# Paths
DATA_PATH = Path("big_tech_diversity.csv")
OUTPUT_PATH = Path("visualizations/chart3_bigtech_timeline.html")

# Company colors
COMPANY_COLORS = {
    'Google': '#4285F4',
    'Apple': '#A2AAAD',
    'Microsoft': '#00A4EF',
    'Meta': '#0668E1',
    'Amazon': '#FF9900',
}


def load_data():
    """Load and prepare Big Tech diversity data."""
    df = pd.read_csv(DATA_PATH)
    df['reporting_status'] = df['reporting_status'].str.strip()
    return df


def create_chart(df):
    """Create the interactive timeline chart."""

    companies = ['Google', 'Apple', 'Microsoft', 'Meta', 'Amazon']

    fig = go.Figure()

    # Default metric: technical roles
    default_metric = 'women_technical_pct'
    alt_metric = 'women_overall_pct'

    for company in companies:
        company_data = df[df['company'] == company].copy()
        company_data = company_data.sort_values('year')

        # Split into reported and not reported
        reported = company_data[company_data['reporting_status'] == 'reported']
        not_reported = company_data[company_data['reporting_status'].isin(['not_reported', 'still_reporting'])]

        # Technical roles - reported (solid line)
        if not reported.empty:
            fig.add_trace(go.Scatter(
                x=reported['year'],
                y=reported[default_metric],
                mode='lines+markers',
                name=company,
                line=dict(color=COMPANY_COLORS[company], width=2),
                marker=dict(size=8, symbol='circle'),
                hovertemplate=(
                    f'<b>{company}</b><br>' +
                    'Year: %{x}<br>' +
                    'Technical: %{y:.1f}%<br>' +
                    '<extra></extra>'
                ),
                legendgroup=company,
                visible=True,
            ))

            # Connect last reported to first not-reported with dashed line
            if not not_reported.empty:
                last_reported_year = reported['year'].max()
                last_reported_val = reported[reported['year'] == last_reported_year][default_metric].values[0]
                first_not_year = not_reported['year'].min()

                # Add connecting dashed segment
                fig.add_trace(go.Scatter(
                    x=[last_reported_year, first_not_year],
                    y=[last_reported_val, last_reported_val],
                    mode='lines',
                    line=dict(color=COMPANY_COLORS[company], width=2, dash='dash'),
                    hoverinfo='skip',
                    legendgroup=company,
                    showlegend=False,
                    visible=True,
                ))

        # Not reported marker (X or star)
        if not not_reported.empty:
            # Use the last known value for positioning (or NaN)
            for _, row in not_reported.iterrows():
                status = row['reporting_status']
                symbol = 'star' if status == 'still_reporting' else 'x'

                # Get y value - use last known or None
                if pd.notna(row[default_metric]):
                    y_val = row[default_metric]
                else:
                    # Use last reported value
                    last_val = reported[default_metric].iloc[-1] if not reported.empty else None
                    y_val = last_val

                hover_text = f'<b>{company}</b><br>Year: {row["year"]}<br>'
                if status == 'still_reporting':
                    hover_text += 'Status: Still reporting<br>'
                else:
                    hover_text += 'Status: Not reported<br>'
                hover_text += '<extra></extra>'

                if y_val is not None:
                    fig.add_trace(go.Scatter(
                        x=[row['year']],
                        y=[y_val],
                        mode='markers',
                        marker=dict(
                            size=12 if symbol == 'star' else 10,
                            symbol=symbol,
                            color=COMPANY_COLORS[company],
                            line=dict(width=2, color=COMPANY_COLORS[company]),
                        ),
                        hovertemplate=hover_text,
                        legendgroup=company,
                        showlegend=False,
                        visible=True,
                    ))

        # Overall workforce traces (hidden by default)
        if not reported.empty:
            fig.add_trace(go.Scatter(
                x=reported['year'],
                y=reported[alt_metric],
                mode='lines+markers',
                name=f'{company} (Overall)',
                line=dict(color=COMPANY_COLORS[company], width=2),
                marker=dict(size=8, symbol='circle'),
                hovertemplate=(
                    f'<b>{company}</b><br>' +
                    'Year: %{x}<br>' +
                    'Overall: %{y:.1f}%<br>' +
                    '<extra></extra>'
                ),
                legendgroup=f'{company}_overall',
                visible=False,
            ))

    # Add vertical line at 2024/2025 boundary
    fig.add_vline(
        x=2024.5,
        line=dict(color='#888', width=2, dash='dash'),
        annotation=dict(
            text='DEI Reporting Stops',
            font=dict(size=11, color='#666'),
            textangle=-90,
            yshift=60,
        ),
    )

    # Create buttons for metric toggle
    # Count traces per company for visibility toggling
    # Structure: each company has 2-3 traces for technical, plus 1 for overall

    # Simpler approach: rebuild with cleaner trace structure
    return create_chart_v2(df)


def create_chart_v2(df):
    """Create chart with cleaner trace structure."""

    companies = ['Google', 'Apple', 'Microsoft', 'Meta', 'Amazon']

    fig = go.Figure()

    for company in companies:
        company_data = df[df['company'] == company].sort_values('year')

        # Technical roles
        tech_data = company_data[company_data['women_technical_pct'].notna()]
        if not tech_data.empty:
            # Determine line style based on last status
            reported = tech_data[tech_data['reporting_status'] == 'reported']

            if not reported.empty:
                fig.add_trace(go.Scatter(
                    x=reported['year'],
                    y=reported['women_technical_pct'],
                    mode='lines+markers',
                    name=company,
                    line=dict(color=COMPANY_COLORS[company], width=2.5),
                    marker=dict(size=8, symbol='circle'),
                    hovertemplate=(
                        f'<b>{company}</b><br>' +
                        'Year: %{x}<br>' +
                        'Technical roles: %{y:.1f}% women<br>' +
                        '<extra></extra>'
                    ),
                    legendgroup=company,
                    visible=True,
                ))

        # Overall workforce (separate trace, hidden by default)
        overall_data = company_data[company_data['women_overall_pct'].notna()]
        if not overall_data.empty:
            reported_overall = overall_data[overall_data['reporting_status'] == 'reported']
            if not reported_overall.empty:
                fig.add_trace(go.Scatter(
                    x=reported_overall['year'],
                    y=reported_overall['women_overall_pct'],
                    mode='lines+markers',
                    name=f'{company}',
                    line=dict(color=COMPANY_COLORS[company], width=2.5),
                    marker=dict(size=8, symbol='circle'),
                    hovertemplate=(
                        f'<b>{company}</b><br>' +
                        'Year: %{x}<br>' +
                        'Overall workforce: %{y:.1f}% women<br>' +
                        '<extra></extra>'
                    ),
                    legendgroup=company,
                    visible=False,
                ))

    # Add 2025 status markers
    for company in companies:
        company_data = df[(df['company'] == company) & (df['year'] == 2025)]
        if not company_data.empty:
            status = company_data['reporting_status'].values[0].strip()

            # Get last known values (may be None for some companies)
            all_company = df[df['company'] == company]
            tech_vals = all_company[all_company['women_technical_pct'].notna()]['women_technical_pct']
            overall_vals = all_company[all_company['women_overall_pct'].notna()]['women_overall_pct']

            last_tech = tech_vals.iloc[-1] if len(tech_vals) > 0 else None
            last_overall = overall_vals.iloc[-1] if len(overall_vals) > 0 else None

            symbol = 'star' if status == 'still_reporting' else 'x'
            symbol_name = 'Continuing' if status == 'still_reporting' else 'Stopped'

            # Technical marker (only if we have data)
            if last_tech is not None:
                fig.add_trace(go.Scatter(
                    x=[2025],
                    y=[last_tech],
                    mode='markers',
                    marker=dict(
                        size=14 if symbol == 'star' else 12,
                        symbol=symbol,
                        color=COMPANY_COLORS[company],
                        line=dict(width=2, color='white' if symbol == 'star' else COMPANY_COLORS[company]),
                    ),
                    name=f'{company} ({symbol_name})',
                    hovertemplate=(
                        f'<b>{company}</b><br>' +
                        f'2025 Status: {symbol_name}<br>' +
                        f'Last reported: {last_tech:.1f}%<br>' +
                        '<extra></extra>'
                    ),
                    legendgroup=company,
                    showlegend=False,
                    visible=True,
                ))

            # Overall marker (only if we have data)
            if last_overall is not None:
                fig.add_trace(go.Scatter(
                    x=[2025],
                    y=[last_overall],
                    mode='markers',
                    marker=dict(
                        size=14 if symbol == 'star' else 12,
                        symbol=symbol,
                        color=COMPANY_COLORS[company],
                        line=dict(width=2, color='white' if symbol == 'star' else COMPANY_COLORS[company]),
                    ),
                    hovertemplate=(
                        f'<b>{company}</b><br>' +
                        f'2025 Status: {symbol_name}<br>' +
                        f'Last reported: {last_overall:.1f}%<br>' +
                        '<extra></extra>'
                    ),
                    legendgroup=company,
                    showlegend=False,
                    visible=False,
                ))

    # Build visibility arrays dynamically based on trace names
    # We'll use legendgroup to track which traces belong to tech vs overall
    tech_visible = []
    overall_visible = []

    for trace in fig.data:
        is_tech = trace.visible is True or trace.visible is None
        tech_visible.append(is_tech)
        overall_visible.append(not is_tech)

    buttons = [
        dict(
            args=[{'visible': tech_visible}],
            label='  Technical Roles                ',
            method='update'
        ),
        dict(
            args=[{'visible': overall_visible}],
            label='  Overall Workforce              ',
            method='update'
        ),
    ]

    # Add vertical line at 2024/2025
    fig.add_vline(
        x=2024.5,
        line=dict(color='#888', width=2, dash='dash'),
    )

    # Add annotation for the vertical line
    fig.add_annotation(
        x=2024.5,
        y=0.95,
        xref='x',
        yref='paper',
        text='DEI Reporting<br>Cliff',
        showarrow=False,
        font=dict(size=11, color='#666'),
        xanchor='left',
        xshift=5,
    )

    # Layout
    fig.update_layout(
        title=dict(
            text='Big Tech Diversity Reporting: The Data Cliff',
            font=dict(size=20),
            x=0.5,
            xanchor='center',
        ),
        xaxis=dict(
            title='Year',
            tickfont=dict(size=12),
            dtick=2,
            range=[2013.5, 2026],
        ),
        yaxis=dict(
            title='% Women',
            tickfont=dict(size=12),
            range=[15, 50],
            ticksuffix='%',
        ),
        updatemenus=[
            dict(
                type='dropdown',
                active=0,
                x=0.0,
                xanchor='left',
                y=1.15,
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
        legend=dict(
            orientation='h',
            yanchor='top',
            y=-0.15,
            xanchor='center',
            x=0.5,
            font=dict(size=11),
            entrywidth=100,
            entrywidthmode='pixels',
        ),
        margin=dict(t=100, b=160, l=60, r=40),
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(family='Arial, sans-serif'),
        hovermode='x unified',
    )

    # Grid
    fig.update_xaxes(showgrid=True, gridcolor='#eee', showline=True, linecolor='#ccc')
    fig.update_yaxes(showgrid=True, gridcolor='#eee', showline=True, linecolor='#ccc')

    # Add note below the legend
    fig.add_annotation(
        text='X = Stopped reporting | Star = Continuing to report | Amazon: Overall workforce data only (no technical breakdown)',
        xref='paper', yref='paper',
        x=0.5, y=-0.32,
        showarrow=False,
        font=dict(size=10, color='#666'),
        xanchor='center',
    )

    return fig


def main():
    print("Loading Big Tech diversity data...")
    df = load_data()
    print(f"  {len(df)} rows loaded")
    print(f"  Companies: {sorted(df['company'].unique())}")
    print(f"  Years: {sorted(df['year'].unique())}")

    print("Creating interactive timeline...")
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
