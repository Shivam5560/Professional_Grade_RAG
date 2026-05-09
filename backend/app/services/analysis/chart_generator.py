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


def create_chart(
    spec: Dict[str, Any],
    df: pd.DataFrame,
    job_id: str,
    chart_id: str,
) -> str:
    """Create a chart from a spec and save via the configured storage backend."""
    chart_type = spec.get("chart_type", "bar")
    x_col = spec.get("x_column")
    y_col = spec.get("y_column")
    color_col = spec.get("color_column")
    title = spec.get("title", "Chart")
    colors = spec.get("colors")

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

    storage = get_chart_storage()

    # Save JSON (always works)
    json_path = storage.save_json(job_id, chart_id, json.loads(json.dumps(fig, cls=PlotlyJSONEncoder)))

    # Save PNG (best-effort)
    try:
        png_bytes = fig.to_image(format="png", width=1200, height=700, scale=2)
        storage.save_png(job_id, chart_id, png_bytes)
    except Exception as exc:
        logger.log_error("Chart PNG export failed", exc, chart_id=chart_id, job_id=job_id)

    return json_path


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


def generate_charts(
    chart_specs: List[Dict[str, Any]],
    df: pd.DataFrame,
    job_id: str,
) -> List[str]:
    """Generate multiple charts from specs."""
    paths: List[str] = []
    for idx, spec in enumerate(chart_specs):
        chart_id = spec.get("chart_id") or f"chart_{idx}"
        try:
            path = create_chart(spec, df, job_id, chart_id)
            paths.append(path)
        except Exception as exc:
            logger.log_error("Chart generation skipped", exc, chart_id=chart_id, job_id=job_id)
    return paths
