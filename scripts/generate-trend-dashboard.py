#!/usr/bin/env python3
"""
Azure Environment Advisor — Trend Dashboard Generator

Reads multiple assessment baseline JSON files and generates an interactive
HTML trend dashboard showing governance scores and findings over time.

Usage:
    python scripts/generate-trend-dashboard.py --baselines-dir baselines/
    python scripts/generate-trend-dashboard.py --baselines file1.json file2.json
    python scripts/generate-trend-dashboard.py --baselines-dir baselines/ --output trend.html

Requirements:
    - Python 3.9+
    - No external dependencies (stdlib only)

Exit codes:
    0 = dashboard generated successfully
    1 = error occurred
"""

import argparse
import json
import os
import sys
from pathlib import Path
from datetime import datetime


def load_baseline(path: str) -> dict:
    """Load and validate a baseline JSON file."""
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if "metadata" not in data:
        raise ValueError(f"Missing 'metadata' in {path}")
    return data


def calculate_score(baseline: dict) -> float:
    """Calculate overall score: passed / (passed + findings) * 100."""
    findings = len(baseline.get("findings", []))
    passed = len(baseline.get("passed", []))
    total = findings + passed
    if total == 0:
        return 100.0
    return round((passed / total) * 100, 1)


def count_by_severity(findings: list) -> dict:
    """Count findings by severity level."""
    counts = {"Critical": 0, "High": 0, "Medium": 0, "Low": 0}
    for f in findings:
        sev = f.get("severity", "Unknown").capitalize()
        if sev in counts:
            counts[sev] += 1
    return counts


def count_by_pillar(findings: list) -> dict:
    """Count findings by pillar."""
    counts = {}
    for f in findings:
        pillar = f.get("pillar", "Unknown")
        counts[pillar] = counts.get(pillar, 0) + 1
    return counts


def get_recurring_findings(baselines: list[dict]) -> list[str]:
    """Find rule IDs that appear in every assessment."""
    if len(baselines) < 2:
        return []
    all_rule_sets = []
    for b in baselines:
        rules = {f.get("rule_id") for f in b.get("findings", []) if f.get("rule_id")}
        all_rule_sets.append(rules)
    recurring = all_rule_sets[0]
    for rs in all_rule_sets[1:]:
        recurring = recurring & rs
    return sorted(recurring)


def compute_changes(prev: dict, curr: dict) -> dict:
    """Compute new/resolved between two consecutive baselines."""
    prev_rules = {f.get("rule_id") for f in prev.get("findings", [])}
    curr_rules = {f.get("rule_id") for f in curr.get("findings", [])}
    return {
        "new": len(curr_rules - prev_rules),
        "resolved": len(prev_rules - curr_rules),
    }


def generate_svg_line_chart(data_points: list[tuple], width=600, height=200) -> str:
    """Generate an SVG line chart. data_points = [(label, value), ...]"""
    if not data_points:
        return ""
    values = [v for _, v in data_points]
    min_v = max(0, min(values) - 10)
    max_v = min(100, max(values) + 10)
    v_range = max_v - min_v if max_v != min_v else 1

    pad_x, pad_y = 50, 20
    chart_w = width - pad_x * 2
    chart_h = height - pad_y * 2

    points = []
    labels_svg = []
    dots_svg = []
    for i, (label, val) in enumerate(data_points):
        x = pad_x + (i / max(len(data_points) - 1, 1)) * chart_w
        y = pad_y + chart_h - ((val - min_v) / v_range) * chart_h
        points.append(f"{x:.1f},{y:.1f}")
        dots_svg.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4" fill="var(--accent)"/>')
        dots_svg.append(f'<text x="{x:.1f}" y="{y:.1f}-12" text-anchor="middle" fill="var(--text-secondary)" font-size="11">{val}</text>')
        labels_svg.append(f'<text x="{x:.1f}" y="{height - 2}" text-anchor="middle" fill="var(--text-secondary)" font-size="10">{label}</text>')

    polyline = f'<polyline points="{" ".join(points)}" fill="none" stroke="var(--accent)" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>'

    # Y-axis labels
    y_labels = []
    for i in range(5):
        val = min_v + (v_range * i / 4)
        y = pad_y + chart_h - (i / 4) * chart_h
        y_labels.append(f'<text x="{pad_x - 8}" y="{y:.1f}" text-anchor="end" fill="var(--text-secondary)" font-size="10" dominant-baseline="middle">{val:.0f}</text>')
        y_labels.append(f'<line x1="{pad_x}" y1="{y:.1f}" x2="{width - pad_x}" y2="{y:.1f}" stroke="var(--border)" stroke-width="0.5" stroke-dasharray="4"/>')

    return f'''<svg viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg" style="width:100%;max-width:{width}px;">
    {"".join(y_labels)}
    {polyline}
    {"".join(dots_svg)}
    {"".join(labels_svg)}
  </svg>'''


def generate_svg_bar_chart(data: list[dict], width=600, height=220) -> str:
    """Generate stacked bar chart. data = [{label, critical, high, medium, low}, ...]"""
    if not data:
        return ""
    max_total = max(sum(d.get(s, 0) for s in ["critical", "high", "medium", "low"]) for d in data)
    if max_total == 0:
        max_total = 1

    pad_x, pad_y = 50, 20
    chart_w = width - pad_x * 2
    chart_h = height - pad_y * 2 - 20
    bar_w = min(40, chart_w / len(data) * 0.6)
    gap = chart_w / len(data)

    colors = {"critical": "#b60205", "high": "#d93f0b", "medium": "#f9d0c4", "low": "#c5def5"}
    bars = []

    for i, d in enumerate(data):
        x = pad_x + gap * i + (gap - bar_w) / 2
        y_offset = pad_y + chart_h
        for sev in ["low", "medium", "high", "critical"]:
            val = d.get(sev, 0)
            h = (val / max_total) * chart_h
            y_offset -= h
            if val > 0:
                bars.append(f'<rect x="{x:.1f}" y="{y_offset:.1f}" width="{bar_w:.1f}" height="{h:.1f}" fill="{colors[sev]}" rx="2"><title>{sev.capitalize()}: {val}</title></rect>')
        bars.append(f'<text x="{x + bar_w/2:.1f}" y="{pad_y + chart_h + 15}" text-anchor="middle" fill="var(--text-secondary)" font-size="10">{d["label"]}</text>')

    legend = []
    lx = pad_x
    for sev, color in [("Critical", "#b60205"), ("High", "#d93f0b"), ("Medium", "#f9d0c4"), ("Low", "#c5def5")]:
        legend.append(f'<rect x="{lx}" y="2" width="10" height="10" fill="{color}" rx="2"/>')
        legend.append(f'<text x="{lx + 14}" y="11" fill="var(--text-secondary)" font-size="10">{sev}</text>')
        lx += 70

    return f'''<svg viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg" style="width:100%;max-width:{width}px;">
    {"".join(legend)}
    {"".join(bars)}
  </svg>'''


def generate_html(baselines: list[dict], output_path: str):
    """Generate the trend dashboard HTML."""
    # Sort by date
    baselines.sort(key=lambda b: b.get("metadata", {}).get("date", ""))

    dates = [b["metadata"].get("date", "?") for b in baselines]
    scores = [calculate_score(b) for b in baselines]
    severity_data = []
    pillar_data = []
    changes = []

    for i, b in enumerate(baselines):
        findings = b.get("findings", [])
        sev = count_by_severity(findings)
        severity_data.append({
            "label": dates[i][-5:],  # MM-DD
            "critical": sev["Critical"],
            "high": sev["High"],
            "medium": sev["Medium"],
            "low": sev["Low"],
        })
        pillar_data.append(count_by_pillar(findings))
        if i > 0:
            changes.append(compute_changes(baselines[i-1], b))

    recurring = get_recurring_findings(baselines)
    score_trend = "improving" if len(scores) > 1 and scores[-1] > scores[0] else "declining" if len(scores) > 1 and scores[-1] < scores[0] else "stable"
    total_resolved = sum(c["resolved"] for c in changes)
    total_new = sum(c["new"] for c in changes)

    # Build score chart
    score_points = [(d[-5:], s) for d, s in zip(dates, scores)]
    score_chart = generate_svg_line_chart(score_points)
    bar_chart = generate_svg_bar_chart(severity_data)

    # Pillar trend table
    all_pillars = sorted(set(p for pd in pillar_data for p in pd))
    pillar_rows = ""
    for pillar in all_pillars:
        cells = ""
        prev = None
        for pd in pillar_data:
            val = pd.get(pillar, 0)
            arrow = ""
            if prev is not None:
                if val < prev:
                    arrow = ' <span style="color:#28a745">▼</span>'
                elif val > prev:
                    arrow = ' <span style="color:#d73a4a">▲</span>'
            cells += f"<td>{val}{arrow}</td>"
            prev = val
        pillar_rows += f"<tr><td><strong>{pillar}</strong></td>{cells}</tr>"

    # Changes table
    changes_rows = ""
    for i, c in enumerate(changes):
        changes_rows += f"<tr><td>{dates[i]} → {dates[i+1]}</td><td style='color:#d73a4a'>+{c['new']}</td><td style='color:#28a745'>-{c['resolved']}</td></tr>"

    # Recurring findings
    recurring_html = ""
    if recurring:
        recurring_html = "<ul>" + "".join(f"<li><code>{r}</code></li>" for r in recurring) + "</ul>"
    else:
        recurring_html = "<p style='color:var(--text-secondary)'>No findings appear in every assessment — great progress! 🎉</p>"

    # Executive summary
    exec_summary = f"""Over <strong>{len(baselines)} assessments</strong> ({dates[0]} → {dates[-1]}),
    your governance score {"improved" if score_trend == "improving" else "declined" if score_trend == "declining" else "remained stable"}
    from <strong>{scores[0]}</strong> to <strong>{scores[-1]}</strong>.
    {total_resolved} findings were resolved and {total_new} new findings appeared.""" if len(baselines) > 1 else f"Single assessment on {dates[0]} with a score of {scores[0]}."

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Azure Environment Advisor — Trend Dashboard</title>
<style>
  :root {{
    --bg: #ffffff; --card-bg: #f6f8fa; --text: #1f2328; --text-secondary: #656d76;
    --border: #d0d7de; --accent: #0969da; --green: #28a745; --red: #d73a4a;
  }}
  @media (prefers-color-scheme: dark) {{
    :root {{
      --bg: #0d1117; --card-bg: #161b22; --text: #e6edf3; --text-secondary: #8b949e;
      --border: #30363d; --accent: #58a6ff; --green: #3fb950; --red: #f85149;
    }}
  }}
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif; background: var(--bg); color: var(--text); padding: 2rem; max-width: 900px; margin: 0 auto; }}
  h1 {{ font-size: 1.8rem; margin-bottom: 0.5rem; }}
  h2 {{ font-size: 1.3rem; margin: 1.5rem 0 0.8rem; border-bottom: 1px solid var(--border); padding-bottom: 0.3rem; }}
  .card {{ background: var(--card-bg); border: 1px solid var(--border); border-radius: 8px; padding: 1.2rem; margin-bottom: 1rem; }}
  .summary {{ font-size: 1.05rem; line-height: 1.6; }}
  .score-big {{ font-size: 3rem; font-weight: 700; color: var(--accent); }}
  .score-label {{ font-size: 0.9rem; color: var(--text-secondary); }}
  .metrics {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 1rem; margin: 1rem 0; }}
  .metric {{ text-align: center; }}
  .metric-value {{ font-size: 1.8rem; font-weight: 700; }}
  .metric-label {{ font-size: 0.8rem; color: var(--text-secondary); }}
  table {{ width: 100%; border-collapse: collapse; font-size: 0.9rem; }}
  th, td {{ padding: 0.5rem 0.8rem; text-align: left; border-bottom: 1px solid var(--border); }}
  th {{ font-weight: 600; color: var(--text-secondary); font-size: 0.8rem; text-transform: uppercase; }}
  code {{ background: var(--card-bg); padding: 0.15rem 0.4rem; border-radius: 3px; font-size: 0.85rem; }}
  .footer {{ margin-top: 2rem; padding-top: 1rem; border-top: 1px solid var(--border); color: var(--text-secondary); font-size: 0.85rem; text-align: center; }}
  a {{ color: var(--accent); text-decoration: none; }}
</style>
</head>
<body>

<h1>📈 Governance Trend Dashboard</h1>
<p style="color:var(--text-secondary)">Azure Environment Advisor — {dates[0]} to {dates[-1]} ({len(baselines)} assessments)</p>

<div class="card summary">
  <p>{exec_summary}</p>
</div>

<div class="metrics">
  <div class="metric">
    <div class="metric-value" style="color:var(--accent)">{scores[-1]}</div>
    <div class="metric-label">Current Score</div>
  </div>
  <div class="metric">
    <div class="metric-value">{len(baselines[-1].get("findings", []))}</div>
    <div class="metric-label">Open Findings</div>
  </div>
  <div class="metric">
    <div class="metric-value" style="color:var(--green)">{total_resolved}</div>
    <div class="metric-label">Total Resolved</div>
  </div>
  <div class="metric">
    <div class="metric-value" style="color:var(--red)">{len(recurring)}</div>
    <div class="metric-label">Recurring</div>
  </div>
</div>

<h2>Score Trend</h2>
<div class="card">{score_chart}</div>

<h2>Findings by Severity</h2>
<div class="card">{bar_chart}</div>

<h2>Pillar Breakdown</h2>
<div class="card">
  <table>
    <tr><th>Pillar</th>{"".join(f"<th>{d[-5:]}</th>" for d in dates)}</tr>
    {pillar_rows}
  </table>
</div>

<h2>New vs Resolved</h2>
<div class="card">
  <table>
    <tr><th>Period</th><th>🆕 New</th><th>✅ Resolved</th></tr>
    {changes_rows if changes_rows else "<tr><td colspan='3' style='color:var(--text-secondary)'>Need at least 2 assessments to show changes</td></tr>"}
  </table>
</div>

<h2>Recurring Findings</h2>
<div class="card">
  <p style="color:var(--text-secondary); margin-bottom:0.5rem;">Findings present in every assessment (never fixed):</p>
  {recurring_html}
</div>

<div class="footer">
  <p>Generated by <strong>Azure Environment Advisor</strong> · <a href="https://github.com/ricmmartins/azure-environment-advisor">GitHub</a></p>
  <p>Dashboard generated {datetime.now().strftime("%Y-%m-%d %H:%M")} from {len(baselines)} baseline files</p>
</div>

</body>
</html>"""

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Trend dashboard saved to: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Generate trend dashboard from assessment baselines")
    parser.add_argument("--baselines-dir", help="Directory containing baseline JSON files")
    parser.add_argument("--baselines", nargs="+", help="Explicit list of baseline JSON files")
    parser.add_argument("--output", default="trend-dashboard.html", help="Output HTML file (default: trend-dashboard.html)")
    args = parser.parse_args()

    if not args.baselines_dir and not args.baselines:
        print("Error: Provide --baselines-dir or --baselines", file=sys.stderr)
        sys.exit(1)

    # Collect baseline files
    files = []
    if args.baselines:
        files = args.baselines
    elif args.baselines_dir:
        baselines_dir = Path(args.baselines_dir)
        if not baselines_dir.exists():
            print(f"Error: Directory not found: {baselines_dir}", file=sys.stderr)
            sys.exit(1)
        files = sorted(str(p) for p in baselines_dir.glob("baseline-*.json"))

    if not files:
        print("No baseline files found.")
        sys.exit(1)

    # Load baselines
    baselines = []
    for f in files:
        try:
            b = load_baseline(f)
            baselines.append(b)
        except Exception as e:
            print(f"Warning: Skipping {f}: {e}", file=sys.stderr)

    if not baselines:
        print("Error: No valid baselines loaded.", file=sys.stderr)
        sys.exit(1)

    print(f"Loaded {len(baselines)} baselines")
    generate_html(baselines, args.output)


if __name__ == "__main__":
    main()
