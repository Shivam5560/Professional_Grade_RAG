"""
Chart generation service for analysis reports.
Uses Plotly for interactive visualizations with pluggable storage backends.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.utils import PlotlyJSONEncoder

from app.services.analysis.storage import get_chart_storage
from app.utils.logger import get_logger

logger = get_logger(__name__)

CHART_TYPE_MAP = {
    "bar": px.bar,
    "line": px.line,
    "scatter": px.scatter,
    "histogram": px.histogram,
    "box": px.box,
    "pie": px.pie,
    "area": px.area,
    "violin": px.violin,
}

LIGHT_CHART_BG = {
    "finance": "#f6faff",
    "healthcare": "#f4fbf7",
    "sales": "#fff6f0",
    "generic": "#f7f8fb",
    "tech": "#f4f6ff",
    "executive": "#fafafa",
}

DARK_CHART_BG = {
    "finance": "#0a1f39",
    "healthcare": "#0d2b1d",
    "sales": "#3d1a00",
    "generic": "#1a1a2e",
    "tech": "#0d1120",
    "executive": "#141414",
}

DARK_STYLES = {"aurora", "bold"}


def create_chart(
    spec: Dict[str, Any],
    df: pd.DataFrame,
    job_id: str,
    chart_id: str,
    bg_hex: str | None = None,
) -> str | None:
    """Create a chart from a spec and save via the configured storage backend. Returns None if data is weak."""
    if df is None or df.empty:
        logger.warning(f"Skipping chart {chart_id} due to empty dataframe.")
        return None
        
    df, spec = _repair_chart_spec(spec, df)
    
    # Check for zero variance on numeric y columns
    y_col = spec.get("y_column")
    if y_col and y_col in df.select_dtypes(include="number").columns:
        if df[y_col].nunique(dropna=True) <= 1:
            logger.warning(f"Skipping chart {chart_id} due to zero variance in y_column {y_col}.")
            return None
    chart_type = spec.get("chart_type", "bar")
    x_col = spec.get("x_column")
    y_col = spec.get("y_column")
    color_col = spec.get("color_column")
    title = spec.get("title", "Chart")
    colors = spec.get("colors")
    if not isinstance(colors, list):
        colors = None
    template_style = str(spec.get("template_style") or "editorial").lower()
    theme = str(spec.get("theme") or "generic").lower()
    typography = spec.get("typography") or {}

    kwargs: Dict[str, Any] = {"title": title}
    if colors:
        kwargs["color_discrete_sequence"] = colors

    if chart_type == "heatmap":
        fig = _build_heatmap(df, x_col, y_col, title)
    elif chart_type == "pie":
        fig = _build_pie(df, x_col, y_col, title)
    elif chart_type in CHART_TYPE_MAP:
        plot_fn = CHART_TYPE_MAP[chart_type]
        if x_col:
            kwargs["x"] = x_col
        if y_col:
            kwargs["y"] = y_col
        if color_col:
            kwargs["color"] = color_col
        try:
            fig = plot_fn(df, **kwargs)
        except Exception as exc:
            logger.log_error("Chart creation failed", exc, chart_type=chart_type, job_id=job_id)
            fig = go.Figure().update_layout(title=f"{title} (Error: {exc})")
    else:
        fig = go.Figure().update_layout(title=f"{title} (Unknown type: {chart_type})")

    _apply_chart_theme(fig, spec, theme, template_style, colors, typography, bg_hex=bg_hex)

    storage = get_chart_storage()

    # Save JSON (always works — for interactive rendering)
    json_path = storage.save_json(job_id, chart_id, json.loads(json.dumps(fig, cls=PlotlyJSONEncoder)))

    # Save PNG (for embedding in slides / reports)
    png_path = None
    try:
        png_bytes = fig.to_image(format="png", width=1200, height=700, scale=2)
        png_path = storage.save_png(job_id, chart_id, png_bytes)
    except Exception as exc:
        logger.log_error("Chart PNG export failed", exc, chart_id=chart_id, job_id=job_id)

    # Return PNG path for embedding; fall back to JSON for interactive use
    return png_path or json_path


def _build_heatmap(df: pd.DataFrame, x_col: str | None, y_col: str | None, title: str) -> go.Figure:
    if x_col and y_col and y_col in df.select_dtypes(include="number").columns:
        pivot = df.pivot_table(index=x_col, values=y_col, aggfunc="mean")
        return px.imshow(pivot, title=title, color_continuous_scale="Blues")
    numeric_df = df.select_dtypes(include="number")
    if numeric_df.shape[1] >= 2:
        return px.imshow(numeric_df.corr(numeric_only=True), title=title, color_continuous_scale="Blues")
    return go.Figure().update_layout(title=f"{title} (Insufficient data for heatmap)")


def _build_pie(df: pd.DataFrame, x_col: str | None, y_col: str | None, title: str) -> go.Figure:
    value_col = y_col or (df.select_dtypes(include="number").columns[0] if len(df.select_dtypes(include="number").columns) > 0 else None)
    name_col = x_col or (df.select_dtypes(include="object").columns[0] if len(df.select_dtypes(include="object").columns) > 0 else None)
    if value_col and name_col:
        return px.pie(df, names=name_col, values=value_col, title=title)
    return go.Figure().update_layout(title=title)


def _repair_chart_spec(spec: Dict[str, Any], df: pd.DataFrame) -> tuple[pd.DataFrame, Dict[str, Any]]:
    """Repair LLM-proposed chart columns so Plotly only sees real dataframe fields."""
    repaired = dict(spec)
    chart_type = str(repaired.get("chart_type") or "bar").lower()
    if chart_type not in CHART_TYPE_MAP and chart_type not in {"heatmap", "pie"}:
        chart_type = "bar"
    repaired["chart_type"] = chart_type

    columns = set(df.columns)
    numeric_cols = list(df.select_dtypes(include="number").columns)
    categorical_cols = list(df.select_dtypes(exclude="number").columns)
    if not categorical_cols:
        low_cardinality_numeric = [c for c in numeric_cols if df[c].nunique(dropna=True) <= 12]
        categorical_cols = low_cardinality_numeric

    x_col = _valid_column(repaired.get("x_column"), columns)
    y_col = _valid_column(repaired.get("y_column"), columns)
    color_col = _valid_column(repaired.get("color_column"), columns)

    target_col = _find_binary_target(df)
    requested_y = str(repaired.get("y_column") or "").lower()
    requested_x = str(repaired.get("x_column") or "").lower()

    if chart_type in {"bar", "line", "area"} and y_col is None and target_col and any(token in requested_y for token in ("rate", "default", "churn", "conversion")):
        group_col = x_col or _choose_group_column(df, categorical_cols, exclude={target_col})
        if group_col:
            plot_df = (
                df.groupby(group_col, dropna=False)[target_col]
                .mean()
                .reset_index()
                .rename(columns={target_col: "rate"})
            )
            repaired["x_column"] = group_col
            repaired["y_column"] = "rate"
            repaired["chart_type"] = "bar"
            repaired["title"] = repaired.get("title") or f"{target_col} rate by {group_col}"
            return plot_df, repaired

    if chart_type == "histogram":
        repaired["x_column"] = x_col or _choose_numeric(numeric_cols) or _choose_group_column(df, categorical_cols)
        repaired.pop("y_column", None)
    elif chart_type == "heatmap":
        repaired["x_column"] = x_col
        repaired["y_column"] = y_col
    elif chart_type == "pie":
        repaired["x_column"] = x_col or _choose_group_column(df, categorical_cols)
        repaired["y_column"] = y_col or _choose_numeric(numeric_cols, exclude={repaired.get("x_column")})
    elif chart_type in {"line", "area"}:
        plot_df = df
        if x_col is None or requested_x in {"month_index", "row_index", "index", "time"}:
            plot_df = df.reset_index(drop=True).copy()
            plot_df["row_index"] = range(1, len(plot_df) + 1)
            x_col = "row_index"
        repaired["x_column"] = x_col
        repaired["y_column"] = y_col or _choose_numeric(numeric_cols, exclude={x_col})
        repaired["color_column"] = color_col
        return plot_df, repaired
    elif chart_type in {"scatter", "box", "violin"}:
        repaired["x_column"] = x_col or _choose_group_column(df, categorical_cols)
        repaired["y_column"] = y_col or _choose_numeric(numeric_cols, exclude={repaired.get("x_column")})
    else:
        repaired["x_column"] = x_col or _choose_group_column(df, categorical_cols) or _choose_numeric(numeric_cols)
        repaired["y_column"] = y_col or _choose_numeric(numeric_cols, exclude={repaired.get("x_column")})

    if color_col:
        repaired["color_column"] = color_col
    else:
        repaired.pop("color_column", None)

    if repaired.get("x_column") is None:
        repaired.pop("x_column", None)
    if repaired.get("y_column") is None:
        repaired.pop("y_column", None)

    return df, repaired


def _valid_column(value: Any, columns: set[str]) -> str | None:
    if not value:
        return None
    text = str(value)
    return text if text in columns else None


def _choose_numeric(numeric_cols: List[str], exclude: set[str | None] | None = None) -> str | None:
    exclude = exclude or set()
    for col in numeric_cols:
        if col not in exclude and col.upper() != "ID":
            return col
    for col in numeric_cols:
        if col not in exclude:
            return col
    return None


def _choose_group_column(df: pd.DataFrame, categorical_cols: List[str], exclude: set[str | None] | None = None) -> str | None:
    exclude = exclude or set()
    for col in categorical_cols:
        if col in exclude:
            continue
        unique_count = df[col].nunique(dropna=True)
        if 2 <= unique_count <= 20:
            return col
    return categorical_cols[0] if categorical_cols else None


def _find_binary_target(df: pd.DataFrame) -> str | None:
    preferred = [c for c in df.columns if "default" in str(c).lower() or "churn" in str(c).lower()]
    candidates = preferred + list(df.select_dtypes(include="number").columns)
    seen = set()
    for col in candidates:
        if col in seen:
            continue
        seen.add(col)
        values = set(df[col].dropna().unique().tolist())
        if values and values.issubset({0, 1, 0.0, 1.0, False, True}):
            return col
    return None


def _apply_chart_theme(
    fig: go.Figure,
    spec: Dict[str, Any],
    theme: str,
    template_style: str,
    colors: List[str] | None,
    typography: Dict[str, Any],
    bg_hex: str | None = None,
) -> None:
    """Make exported chart images feel native to the chosen slide template."""
    dark = template_style in DARK_STYLES
    paper_bg = bg_hex if bg_hex else (DARK_CHART_BG.get(theme, DARK_CHART_BG["generic"]) if dark else LIGHT_CHART_BG.get(theme, LIGHT_CHART_BG["generic"]))
    plot_bg = paper_bg
    text_color = "#f8fbff" if dark else "#1e2430"
    muted_grid = "rgba(255,255,255,0.14)" if dark else "rgba(30,36,48,0.12)"
    accent = colors[0] if colors else ("#6c5ce7" if dark else "#1f4e79")
    font_family = typography.get("body_font") or "Calibri"
    title_font = typography.get("title_font") or font_family

    fig.update_layout(
        template="plotly_dark" if dark else "plotly_white",
        paper_bgcolor=paper_bg,
        plot_bgcolor=plot_bg,
        font={"family": font_family, "color": text_color, "size": 16},
        title={
            "text": spec.get("title", ""),
            "font": {"family": title_font, "color": text_color, "size": 28},
            "x": 0.02,
            "xanchor": "left",
        },
        margin={"l": 72, "r": 44, "t": 92, "b": 72},
        legend={
            "bgcolor": "rgba(0,0,0,0)",
            "font": {"color": text_color, "family": font_family},
            "orientation": "h",
            "yanchor": "bottom",
            "y": 1.02,
            "xanchor": "right",
            "x": 1,
        },
    )
    fig.update_xaxes(showgrid=True, gridcolor=muted_grid, zerolinecolor=muted_grid, linecolor=accent)
    fig.update_yaxes(showgrid=True, gridcolor=muted_grid, zerolinecolor=muted_grid, linecolor=accent)

    if colors:
        fig.update_layout(colorway=colors)
        if len(colors) >= 2:
            fig.update_layout(coloraxis={"colorscale": [[0, colors[0]], [1, colors[-1]]]})


def generate_charts(
    chart_specs: List[Dict[str, Any]],
    df: pd.DataFrame,
    job_id: str,
    bg_hex: str | None = None,
) -> List[str]:
    """Generate multiple charts from specs."""
    paths: List[str] = []
    for idx, spec in enumerate(chart_specs):
        chart_id = spec.get("chart_id") or f"chart_{idx}"
        try:
            path = create_chart(spec, df, job_id, chart_id, bg_hex=bg_hex)
            if path:
                paths.append(path)
        except Exception as exc:
            logger.log_error("Chart generation skipped", exc, chart_id=chart_id, job_id=job_id)
    return paths
