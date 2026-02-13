"""
InsightForge - Visualization Module
Creates interactive Plotly charts and static Matplotlib/Seaborn visualizations
for business data analysis.
"""

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import matplotlib.pyplot as plt
import seaborn as sns
from typing import List, Optional, Tuple
import io


# ── Color Palette ───────────────────────────────────────────

INSIGHTFORGE_COLORS = [
    "#00E5FF",  # Electric Cyan
    "#2979FF",  # Cobalt Blue
    "#651FFF",  # Deep Violet
    "#F50057",  # Neon Pink
    "#00E676",  # Bright Green
    "#FFD600",  # Neon Yellow
    "#FF9100",  # Orange
    "#D500F9",  # Purple
]

PLOTLY_TEMPLATE = "plotly_dark"


class Visualizer:
    """Creates professional business visualizations using Plotly and Seaborn."""

    def __init__(self):
        self.colors = INSIGHTFORGE_COLORS
        self.template = PLOTLY_TEMPLATE

    # ── Automatic Visualization ─────────────────────────────

    def auto_visualize(self, df: pd.DataFrame) -> List[go.Figure]:
        """Automatically generate the most relevant charts for a given DataFrame."""
        figures = []
        numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
        categorical_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()
        datetime_cols = df.select_dtypes(include=["datetime"]).columns.tolist()

        # Try to detect date-like string columns
        for col in categorical_cols[:]:
            try:
                parsed = pd.to_datetime(df[col], errors="coerce")
                if parsed.notna().sum() > len(df) * 0.5:
                    df[col] = parsed
                    datetime_cols.append(col)
                    categorical_cols.remove(col)
            except Exception:
                pass

        # 1. Distribution of numeric columns (histogram)
        if numeric_cols:
            fig = self.create_distribution_chart(df, numeric_cols[:4])
            figures.append(("Distribution Analysis", fig))

        # 2. Correlation heatmap for numeric columns
        if len(numeric_cols) >= 2:
            fig = self.create_correlation_heatmap(df, numeric_cols)
            figures.append(("Correlation Heatmap", fig))

        # 3. Top categorical breakdowns (bar charts)
        if categorical_cols and numeric_cols:
            for cat_col in categorical_cols[:2]:
                if df[cat_col].nunique() <= 20:
                    fig = self.create_bar_chart(
                        df, x=cat_col, y=numeric_cols[0],
                        title=f"{numeric_cols[0]} by {cat_col}"
                    )
                    figures.append((f"{numeric_cols[0]} by {cat_col}", fig))

        # 4. Time series if datetime columns exist
        if datetime_cols and numeric_cols:
            fig = self.create_line_chart(
                df, x=datetime_cols[0], y=numeric_cols[:3],
                title=f"Trend Over Time"
            )
            figures.append(("Trend Over Time", fig))

        # 5. Pie chart for first categorical column
        if categorical_cols:
            for cat_col in categorical_cols[:1]:
                if 2 <= df[cat_col].nunique() <= 10:
                    fig = self.create_pie_chart(df, cat_col, title=f"{cat_col} Distribution")
                    figures.append((f"{cat_col} Distribution", fig))

        # 6. Scatter plot for numeric pairs
        if len(numeric_cols) >= 2:
            color_col = categorical_cols[0] if categorical_cols and df[categorical_cols[0]].nunique() <= 10 else None
            fig = self.create_scatter_plot(
                df, x=numeric_cols[0], y=numeric_cols[1],
                color=color_col,
                title=f"{numeric_cols[0]} vs {numeric_cols[1]}"
            )
            figures.append((f"{numeric_cols[0]} vs {numeric_cols[1]}", fig))

        return figures

    # ── Chart Builders ──────────────────────────────────────

    def create_bar_chart(self, df: pd.DataFrame, x: str, y: str,
                         title: str = "", color: str = None,
                         orientation: str = "v") -> go.Figure:
        """Create an interactive bar chart."""
        agg_df = df.groupby(x)[y].sum().reset_index().sort_values(y, ascending=False)

        fig = px.bar(
            agg_df, x=x, y=y, color=color,
            title=title or f"{y} by {x}",
            color_discrete_sequence=self.colors,
            template=self.template,
        )
        fig.update_layout(
            font=dict(family="Inter, sans-serif"),
            title_font_size=18,
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(t=60, b=40, l=40, r=20),
        )
        return fig

    def create_line_chart(self, df: pd.DataFrame, x: str, y: list,
                          title: str = "") -> go.Figure:
        """Create an interactive line chart (supports multiple y columns)."""
        fig = go.Figure()
        for i, col in enumerate(y):
            sorted_df = df.sort_values(x)
            fig.add_trace(go.Scatter(
                x=sorted_df[x], y=sorted_df[col],
                mode="lines+markers",
                name=col,
                line=dict(color=self.colors[i % len(self.colors)], width=2),
                marker=dict(size=5),
            ))
        fig.update_layout(
            title=title or "Trend Analysis",
            template=self.template,
            font=dict(family="Inter, sans-serif"),
            title_font_size=18,
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(t=60, b=40, l=40, r=20),
            hovermode="x unified",
        )
        return fig

    def create_scatter_plot(self, df: pd.DataFrame, x: str, y: str,
                            color: str = None, size: str = None,
                            title: str = "") -> go.Figure:
        """Create an interactive scatter plot."""
        fig = px.scatter(
            df, x=x, y=y, color=color, size=size,
            title=title or f"{x} vs {y}",
            color_discrete_sequence=self.colors,
            template=self.template,
        )
        fig.update_layout(
            font=dict(family="Inter, sans-serif"),
            title_font_size=18,
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(t=60, b=40, l=40, r=20),
        )
        return fig

    def create_pie_chart(self, df: pd.DataFrame, column: str,
                         title: str = "") -> go.Figure:
        """Create an interactive pie/donut chart."""
        value_counts = df[column].value_counts().head(10)

        fig = go.Figure(data=[go.Pie(
            labels=value_counts.index.tolist(),
            values=value_counts.values.tolist(),
            hole=0.4,
            marker=dict(colors=self.colors[:len(value_counts)]),
            textinfo="label+percent",
            textposition="outside",
        )])
        fig.update_layout(
            title=title or f"{column} Distribution",
            template=self.template,
            font=dict(family="Inter, sans-serif"),
            title_font_size=18,
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(t=60, b=40, l=40, r=20),
            showlegend=True,
        )
        return fig

    def create_distribution_chart(self, df: pd.DataFrame,
                                   columns: list) -> go.Figure:
        """Create histogram distributions for numeric columns."""
        n = len(columns)
        fig = make_subplots(rows=1, cols=n, subplot_titles=columns)

        for i, col in enumerate(columns, 1):
            fig.add_trace(
                go.Histogram(
                    x=df[col].dropna(),
                    name=col,
                    marker_color=self.colors[i - 1],
                    opacity=0.8,
                ),
                row=1, col=i,
            )

        fig.update_layout(
            title="Distribution Analysis",
            template=self.template,
            font=dict(family="Inter, sans-serif"),
            title_font_size=18,
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(t=80, b=40, l=40, r=20),
            showlegend=False,
            height=400,
        )
        return fig

    def create_correlation_heatmap(self, df: pd.DataFrame,
                                    columns: list = None) -> go.Figure:
        """Create a correlation heatmap."""
        if columns:
            corr = df[columns].corr()
        else:
            corr = df.select_dtypes(include=["number"]).corr()

        fig = go.Figure(data=go.Heatmap(
            z=corr.values,
            x=corr.columns.tolist(),
            y=corr.index.tolist(),
            colorscale="RdBu_r",
            zmid=0,
            text=np.round(corr.values, 2),
            texttemplate="%{text}",
            textfont={"size": 11},
        ))
        fig.update_layout(
            title="Correlation Heatmap",
            template=self.template,
            font=dict(family="Inter, sans-serif"),
            title_font_size=18,
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(t=60, b=40, l=100, r=20),
            height=500,
        )
        return fig

    def create_box_plot(self, df: pd.DataFrame, y: str,
                        x: str = None, title: str = "") -> go.Figure:
        """Create a box plot for outlier analysis."""
        fig = px.box(
            df, x=x, y=y,
            title=title or f"{y} Box Plot",
            color=x,
            color_discrete_sequence=self.colors,
            template=self.template,
        )
        fig.update_layout(
            font=dict(family="Inter, sans-serif"),
            title_font_size=18,
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(t=60, b=40, l=40, r=20),
        )
        return fig

    # ── KPI Cards Data ──────────────────────────────────────

    @staticmethod
    def compute_kpi_cards(df: pd.DataFrame) -> list:
        """Compute basic KPI metrics from a DataFrame."""
        kpis = []
        numeric_cols = df.select_dtypes(include=["number"]).columns

        kpis.append({"label": "Total Records", "value": f"{len(df):,}", "icon": "📊"})
        kpis.append({"label": "Columns", "value": str(len(df.columns)), "icon": "📋"})

        if len(numeric_cols) > 0:
            # Use the first numeric column as primary metric
            primary_col = numeric_cols[0]
            total = df[primary_col].sum()
            avg = df[primary_col].mean()
            kpis.append({"label": f"Total {primary_col}", "value": f"{total:,.2f}", "icon": "💰"})
            kpis.append({"label": f"Avg {primary_col}", "value": f"{avg:,.2f}", "icon": "📈"})

        missing = df.isnull().sum().sum()
        completeness = ((1 - missing / (df.shape[0] * df.shape[1])) * 100)
        kpis.append({"label": "Data Completeness", "value": f"{completeness:.1f}%", "icon": "✅"})

        return kpis
