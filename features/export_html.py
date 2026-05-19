"""Generate a standalone HTML report with activation & QSO statistics."""

from __future__ import annotations

import html
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import plotly.io as pio


def _fig_to_html(fig, cls: str = "") -> str:
    if fig is None:
        return ""
    fig = fig.to_dict()
    fig["layout"] = {**fig.get("layout", {}), "autosize": True}
    import plotly.graph_objects as go
    fig_obj = go.Figure(fig)
    inner = pio.to_html(
        fig_obj, full_html=False, include_plotlyjs=False,
        config={"displayModeBar": False, "responsive": True},
    )
    if cls:
        return f'<div class="{cls}">{inner}</div>'
    return inner


def _format_duration(seconds: int | None) -> str:
    if seconds is None or seconds < 0:
        return "0m"
    h = seconds // 3600
    m = (seconds % 3600) // 60
    if h > 0:
        return f"{h}h {m}m"
    return f"{m}m"


def generate_stats_html(
    award: Dict[str, Any],
    act_stats: Dict[str, Any],
    qso_stats: Dict[str, Any],
    by_date_qso: List[Dict],
    by_hour_qso: List[Dict],
    bm_matrix: Optional[List],
    by_dxcc: List[Dict],
    t: Dict[str, str],
) -> str:
    """Build a self-contained HTML string with all stats and charts.

    Args:
        award: Award dict (name, start_date, end_date, …).
        act_stats: Result of get_activation_stats().
        qso_stats: Result of get_qso_stats() (total, unique_calls, by_band, by_mode, by_operator).
        by_date_qso: QSO timeline data.
        by_hour_qso: QSO hourly data.
        bm_matrix: Band/mode matrix.
        by_dxcc: DXCC entity data.
        t: Translations dict.
    """
    from ui.charts import (
        create_activation_timeline_chart,
        create_activation_operator_chart,
        create_activation_band_chart,
        create_activation_mode_chart,
        create_activation_hourly_chart,
        create_qso_timeline_chart,
        create_qso_band_mode_heatmap,
        create_qso_hourly_chart,
        create_qso_band_chart,
        create_qso_mode_chart,
        create_qso_operator_chart,
        create_qso_dxcc_chart,
    )

    award_name = html.escape(award.get("name", ""))
    period = ""
    if award.get("start_date") and award.get("end_date"):
        period = f"{award['start_date']}  —  {award['end_date']}"

    generated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    # --- Activation metrics ---------------------------------------------------
    total_act = act_stats.get("total_activations", 0)
    total_sec = act_stats.get("total_seconds", 0)
    avg_sec = total_sec // total_act if total_act else 0
    n_operators = len(act_stats.get("by_operator", {}))

    # --- Activation charts ----------------------------------------------------
    act_timeline_html = ""
    if act_stats.get("by_date") and len(act_stats["by_date"]) > 1:
        act_timeline_html = _fig_to_html(
            create_activation_timeline_chart(act_stats["by_date"], t)
        )

    act_operator_html = ""
    if act_stats.get("by_operator"):
        act_operator_html = _fig_to_html(
            create_activation_operator_chart(act_stats["by_operator"], t)
        )

    act_band_html = ""
    if act_stats.get("by_band"):
        act_band_html = _fig_to_html(
            create_activation_band_chart(act_stats["by_band"], t), cls="half",
        )

    act_mode_html = ""
    if act_stats.get("by_mode"):
        act_mode_html = _fig_to_html(
            create_activation_mode_chart(act_stats["by_mode"], t), cls="half",
        )

    act_hourly_html = ""
    if act_stats.get("by_hour"):
        act_hourly_html = _fig_to_html(
            create_activation_hourly_chart(act_stats["by_hour"], t)
        )

    # --- QSO metrics ----------------------------------------------------------
    qso_total = qso_stats.get("total", 0)
    qso_unique = qso_stats.get("unique_calls", 0)
    top_band = next(iter(qso_stats.get("by_band", {})), "—")
    top_mode = next(iter(qso_stats.get("by_mode", {})), "—")

    # QSO insights
    insights_html = ""
    if by_date_qso:
        busiest = max(by_date_qso, key=lambda r: r["count"])
        avg_daily = qso_total / len(by_date_qso)
        peak = max(by_hour_qso, key=lambda r: r["count"]) if by_hour_qso else None
        peak_str = f"{peak['hour']:02d}:00" if peak else "—"
        insights_html = f"""
        <div class="metrics">
            <div class="metric">
                <div class="metric-label">{html.escape(t.get('qso_insight_busiest_day', 'Busiest day'))}</div>
                <div class="metric-value">{html.escape(busiest['date'])}</div>
                <div class="metric-sub">{busiest['count']} QSOs</div>
            </div>
            <div class="metric">
                <div class="metric-label">{html.escape(t.get('qso_insight_avg_daily', 'Avg QSOs/day'))}</div>
                <div class="metric-value">{avg_daily:.1f}</div>
            </div>
            <div class="metric">
                <div class="metric-label">{html.escape(t.get('qso_insight_peak_hour', 'Peak hour (UTC)'))}</div>
                <div class="metric-value">{peak_str}</div>
                <div class="metric-sub">{peak['count'] if peak else 0} QSOs</div>
            </div>
            <div class="metric">
                <div class="metric-label">{html.escape(t.get('qso_insight_active_days', 'Active days'))}</div>
                <div class="metric-value">{len(by_date_qso)}</div>
            </div>
        </div>"""

    # --- QSO charts -----------------------------------------------------------
    qso_timeline_html = ""
    if by_date_qso and len(by_date_qso) > 1:
        qso_timeline_html = _fig_to_html(
            create_qso_timeline_chart(by_date_qso, t)
        )

    qso_bm_html = ""
    if bm_matrix:
        qso_bm_html = _fig_to_html(
            create_qso_band_mode_heatmap(bm_matrix, t), cls="half",
        )

    qso_mode_html = ""
    if qso_stats.get("by_mode"):
        qso_mode_html = _fig_to_html(
            create_qso_mode_chart(qso_stats["by_mode"], t), cls="half",
        )

    qso_band_html = ""
    if qso_stats.get("by_band"):
        qso_band_html = _fig_to_html(
            create_qso_band_chart(qso_stats["by_band"], t)
        )

    qso_hourly_html = ""
    if by_hour_qso:
        qso_hourly_html = _fig_to_html(
            create_qso_hourly_chart(by_hour_qso, t)
        )

    qso_dxcc_html = ""
    dxcc_count = 0
    if by_dxcc:
        fig_dxcc, dxcc_count = create_qso_dxcc_chart(by_dxcc, t)
        qso_dxcc_html = _fig_to_html(fig_dxcc)

    qso_operator_html = ""
    if qso_stats.get("by_operator"):
        qso_operator_html = _fig_to_html(
            create_qso_operator_chart(qso_stats["by_operator"], t)
        )

    # --- Build sections -------------------------------------------------------
    def _section(title: str, *chart_blocks: str) -> str:
        content = "".join(c for c in chart_blocks if c)
        if not content:
            return ""
        return f'<h3>{html.escape(title)}</h3>\n{content}'

    act_bm_content = act_band_html + act_mode_html
    act_bm_section = ""
    if act_bm_content:
        act_bm_section = (
            f'<h3>{html.escape(t.get("act_subtab_band_mode", "Band / Mode"))}</h3>\n'
            f'<div class="side-by-side">{act_bm_content}</div>'
        )

    act_sections = "".join(filter(None, [
        _section(t.get("act_chart_timeline", "Timeline"), act_timeline_html),
        _section(t.get("act_chart_operator_title", "Time per operator"), act_operator_html),
        act_bm_section,
        _section(t.get("act_chart_hourly_title", "Activations by hour"), act_hourly_html),
    ]))

    dxcc_caption = ""
    if dxcc_count:
        dxcc_caption = (
            f'<p class="caption">'
            f'{html.escape(t.get("qso_dxcc_unique", "DXCC entities: {count}").format(count=dxcc_count))}'
            f'</p>'
        )

    qso_bm_content = qso_bm_html + qso_mode_html
    qso_bm_section = ""
    if qso_bm_content:
        qso_bm_section = (
            f'<h3>{html.escape(t.get("qso_chart_band_mode", "Band / Mode"))}</h3>\n'
            f'<div class="side-by-side">{qso_bm_content}</div>'
        )

    qso_sections = "".join(filter(None, [
        _section(t.get("qso_chart_activity", "Activity over time"), qso_timeline_html),
        qso_bm_section,
        _section(t.get("qso_chart_bands", "Bands"), qso_band_html),
        _section(t.get("qso_chart_hourly", "Hourly"), qso_hourly_html),
        _section(t.get("qso_chart_dxcc", "DXCC"), dxcc_caption, qso_dxcc_html),
        _section(t.get("qso_chart_operators", "Operators"), qso_operator_html),
    ]))

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{award_name} — Stats Report</title>
<script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
<style>
  :root {{ --bg: #0e1117; --card: #1a1c23; --text: #fafafa; --muted: #a0a0a0; --accent: #4FC3F7; }}
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ background: var(--bg); color: var(--text); font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; padding: 2rem; }}
  h1 {{ font-size: 1.8rem; margin-bottom: .3rem; }}
  h2 {{ font-size: 1.3rem; margin: 2rem 0 1rem; border-bottom: 1px solid #333; padding-bottom: .4rem; }}
  h3 {{ font-size: 1.05rem; color: var(--accent); margin: 1.5rem 0 .5rem; }}
  .subtitle {{ color: var(--muted); margin-bottom: 1.5rem; }}
  .metrics {{ display: flex; flex-wrap: wrap; gap: 1rem; margin: 1rem 0; }}
  .metric {{ background: var(--card); border-radius: 8px; padding: 1rem 1.5rem; min-width: 140px; flex: 1; }}
  .metric-label {{ font-size: .78rem; color: var(--muted); text-transform: uppercase; letter-spacing: .04em; }}
  .metric-value {{ font-size: 1.6rem; font-weight: 700; margin-top: .2rem; }}
  .metric-sub {{ font-size: .82rem; color: var(--muted); }}
  .side-by-side {{ display: flex; gap: 1rem; flex-wrap: wrap; }}
  .half {{ flex: 1 1 45%; min-width: 300px; }}
  .half .js-plotly-plot, .half .plotly-graph-div {{ width: 100% !important; }}
  .js-plotly-plot .plotly .modebar {{ display: none !important; }}
  .plotly-graph-div {{ width: 100% !important; }}
  .caption {{ color: var(--muted); font-size: .85rem; margin-bottom: .5rem; }}
  .footer {{ margin-top: 3rem; color: var(--muted); font-size: .8rem; text-align: center; }}
  @media (max-width: 600px) {{
    body {{ padding: 1rem; }}
    .metrics {{ flex-direction: column; }}
    .side-by-side {{ flex-direction: column; }}
  }}
</style>
</head>
<body>

<h1>{award_name}</h1>
<div class="subtitle">{html.escape(period)}</div>

<!-- ============ ACTIVATION STATS ============ -->
<h2>{html.escape(t.get('act_stats_title', 'Activation Statistics'))}</h2>

<div class="metrics">
  <div class="metric">
    <div class="metric-label">{html.escape(t.get('act_total_activations', 'Activations'))}</div>
    <div class="metric-value">{total_act:,}</div>
  </div>
  <div class="metric">
    <div class="metric-label">{html.escape(t.get('act_total_time', 'Total time'))}</div>
    <div class="metric-value">{_format_duration(total_sec)}</div>
  </div>
  <div class="metric">
    <div class="metric-label">{html.escape(t.get('act_avg_duration', 'Avg duration'))}</div>
    <div class="metric-value">{_format_duration(avg_sec)}</div>
  </div>
  <div class="metric">
    <div class="metric-label">{html.escape(t.get('act_operators_count', 'Operators'))}</div>
    <div class="metric-value">{n_operators}</div>
  </div>
</div>

{act_sections}

<!-- ============ QSO STATS ============ -->
<h2>{html.escape(t.get('qso_log_title', 'QSO Log'))}</h2>

<div class="metrics">
  <div class="metric">
    <div class="metric-label">{html.escape(t.get('qso_total', 'Total QSOs'))}</div>
    <div class="metric-value">{qso_total:,}</div>
  </div>
  <div class="metric">
    <div class="metric-label">{html.escape(t.get('qso_unique_calls', 'Unique Calls'))}</div>
    <div class="metric-value">{qso_unique:,}</div>
  </div>
  <div class="metric">
    <div class="metric-label">{html.escape(t.get('qso_top_band', 'Top Band'))}</div>
    <div class="metric-value">{html.escape(top_band)}</div>
  </div>
  <div class="metric">
    <div class="metric-label">{html.escape(t.get('qso_chart_modes', 'Top Mode'))}</div>
    <div class="metric-value">{html.escape(top_mode)}</div>
  </div>
</div>

{insights_html}

{qso_sections}

<div class="footer">{html.escape(t.get('export_generated', 'Report generated'))} {generated}</div>

<script>
window.addEventListener('load', function() {{
  document.querySelectorAll('.plotly-graph-div').forEach(function(el) {{
    Plotly.Plots.resize(el);
  }});
}});
window.addEventListener('resize', function() {{
  document.querySelectorAll('.plotly-graph-div').forEach(function(el) {{
    Plotly.Plots.resize(el);
  }});
}});
</script>

</body>
</html>"""
