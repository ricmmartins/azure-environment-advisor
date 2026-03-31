#!/usr/bin/env python3
"""
Azure Environment Advisor — Trend Dashboard Generator

Generates a self-contained HTML trend dashboard from multiple assessment baselines.
Shows score trends, finding counts by severity, pillar breakdowns, and drift analysis.

Usage:
    python scripts/generate-trend-dashboard.py --baselines-dir baselines/ --output trend-dashboard.html
    python scripts/generate-trend-dashboard.py --baselines file1.json file2.json --output trend-dashboard.html

The generated dashboard includes:
    - Overall Score Trend (line chart)
    - Finding Counts by Severity (stacked bar chart)
    - Pillar Score Breakdown (table with trend arrows)
    - New vs Resolved findings between consecutive assessments
    - Top Recurring Findings (never fixed)
    - Executive Summary
    - Filter buttons for time range (Last 4, Last 8, All)

Requirements:
    - Python 3.9+ (stdlib only, no pip dependencies)

Exit codes:
    0 = success
    1 = error
"""

import sys
import json
import argparse
from pathlib import Path
from datetime import datetime


# --- Constants ---

PILLAR_MAP = {
    "SEC": "Security",
    "REL": "Reliability",
    "COST": "Cost Optimization",
    "OPS": "Operational Excellence",
    "PERF": "Performance",
    "GOV": "Governance",
}

SEVERITY_LEVELS = ["Critical", "High", "Medium", "Low"]
SEVERITY_ORDER = {"Critical": 4, "High": 3, "Medium": 2, "Low": 1, "Informational": 0}


# --- Helpers ---

def rule_id_to_pillar(rule_id):
    """Derive pillar name from rule ID prefix."""
    prefix = rule_id.split("-")[0] if "-" in rule_id else ""
    return PILLAR_MAP.get(prefix, "Other")


def parse_date(date_str):
    """Parse a date string, returning datetime.min on failure."""
    for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%SZ"):
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    return datetime.min


def format_date(date_str):
    """Format a date string for display."""
    dt = parse_date(date_str)
    if dt == datetime.min:
        return date_str or "Unknown"
    return dt.strftime("%b %d, %Y")


def escape_html(text):
    """Escape HTML special characters."""
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


# --- Data Loading ---

def load_baseline(path):
    """Load and validate a baseline JSON file."""
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if "metadata" not in data or "findings" not in data:
        raise ValueError(f"Invalid baseline: missing 'metadata' or 'findings' in {path}")
    return data


# --- Analysis ---

def calculate_score(baseline):
    """Calculate overall assessment score: passed / (passed + findings) * 100."""
    findings = [f for f in baseline.get("findings", [])
                if f.get("status", "finding") != "exception"]
    passed = baseline.get("passed", [])
    total = len(passed) + len(findings)
    if total == 0:
        return 100.0
    return round((len(passed) / total) * 100, 1)


def calculate_pillar_scores(baseline):
    """Calculate per-pillar scores based on rule ID prefixes."""
    findings = [f for f in baseline.get("findings", [])
                if f.get("status", "finding") != "exception"]
    passed = baseline.get("passed", [])

    pillar_findings = {}
    for f in findings:
        pillar = f.get("pillar", rule_id_to_pillar(f.get("rule_id", "")))
        pillar_findings[pillar] = pillar_findings.get(pillar, 0) + 1

    pillar_passed = {}
    for rule_id in passed:
        pillar = rule_id_to_pillar(rule_id)
        pillar_passed[pillar] = pillar_passed.get(pillar, 0) + 1

    all_pillars = sorted(set(pillar_findings.keys()) | set(pillar_passed.keys()))
    scores = {}
    for pillar in all_pillars:
        p = pillar_passed.get(pillar, 0)
        f = pillar_findings.get(pillar, 0)
        total = p + f
        scores[pillar] = round((p / total) * 100, 1) if total > 0 else 100.0
    return scores


def severity_counts(baseline):
    """Count findings by severity level."""
    findings = [f for f in baseline.get("findings", [])
                if f.get("status", "finding") != "exception"]
    counts = {s: 0 for s in SEVERITY_LEVELS}
    for f in findings:
        sev = f.get("severity", "Low")
        if sev in counts:
            counts[sev] += 1
    return counts


def diff_findings(old_baseline, new_baseline):
    """Compute new, resolved, escalated, de-escalated findings between two baselines."""
    old_ids = {f["rule_id"]: f for f in old_baseline.get("findings", [])
               if f.get("status", "finding") != "exception"}
    new_ids = {f["rule_id"]: f for f in new_baseline.get("findings", [])
               if f.get("status", "finding") != "exception"}

    result = {"new": [], "resolved": [], "escalated": [], "de_escalated": []}

    for rid in sorted(set(old_ids) | set(new_ids)):
        old = old_ids.get(rid)
        new = new_ids.get(rid)
        if new and not old:
            result["new"].append(new)
        elif old and not new:
            result["resolved"].append(old)
        elif old and new:
            o = SEVERITY_ORDER.get(old.get("severity", ""), 0)
            n = SEVERITY_ORDER.get(new.get("severity", ""), 0)
            if n > o:
                result["escalated"].append({
                    "rule_id": rid, "title": new.get("title", ""),
                    "from": old.get("severity", ""), "to": new.get("severity", ""),
                })
            elif n < o:
                result["de_escalated"].append({
                    "rule_id": rid, "title": new.get("title", ""),
                    "from": old.get("severity", ""), "to": new.get("severity", ""),
                })

    return result


def find_recurring_findings(baselines):
    """Find findings present in every single assessment."""
    if len(baselines) < 2:
        return []
    finding_sets = []
    for b in baselines:
        ids = {f["rule_id"] for f in b.get("findings", [])
               if f.get("status", "finding") != "exception"}
        finding_sets.append(ids)

    recurring = finding_sets[0]
    for s in finding_sets[1:]:
        recurring = recurring & s

    latest = baselines[-1]
    result = []
    for f in latest.get("findings", []):
        if f["rule_id"] in recurring:
            result.append(f)
    return sorted(result, key=lambda x: SEVERITY_ORDER.get(x.get("severity", ""), 0), reverse=True)


# --- HTML Generation ---

def generate_html(data):
    """Generate the complete self-contained HTML dashboard."""
    data_json = json.dumps(data, indent=None, ensure_ascii=False)
    subscription = escape_html(data.get("subscription", "Unknown"))
    profile = escape_html(data.get("profile", ""))
    n = len(data["assessments"])
    title = f"Trend Dashboard — {subscription}"
    profile_text = f" — Profile: {profile.title()}" if profile else ""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<style>
  :root {{
    --critical: #d13438;
    --high: #e97548;
    --medium: #eaa300;
    --low: #0078d4;
    --pass: #107c10;
    --bg: #fafafa;
    --card: #ffffff;
    --text: #242424;
    --text-secondary: #616161;
    --border: #e0e0e0;
    --hover: #f5f5f5;
    --accent: #0078d4;
    --improving: #107c10;
    --declining: #d13438;
    --stable: #616161;
  }}
  @media (prefers-color-scheme: dark) {{
    :root {{
      --bg: #1a1a1a;
      --card: #2d2d2d;
      --text: #e0e0e0;
      --text-secondary: #a0a0a0;
      --border: #404040;
      --hover: #333333;
    }}
  }}
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, sans-serif; background: var(--bg); color: var(--text); line-height: 1.5; }}

  .header {{ background: linear-gradient(135deg, #0078d4, #005a9e); color: white; padding: 2rem 2rem 1.5rem; }}
  .header h1 {{ font-size: 1.75rem; font-weight: 600; margin-bottom: 0.25rem; }}
  .header .subtitle {{ opacity: 0.85; font-size: 0.95rem; }}
  .header .meta {{ display: flex; gap: 2rem; margin-top: 1rem; font-size: 0.85rem; opacity: 0.8; flex-wrap: wrap; }}
  .header .meta span {{ display: flex; align-items: center; gap: 0.35rem; }}

  .filters {{ padding: 1rem 2rem; display: flex; gap: 0.5rem; flex-wrap: wrap; align-items: center; }}
  .filters label {{ font-size: 0.85rem; font-weight: 600; margin-right: 0.5rem; }}
  .filter-btn {{ padding: 0.35rem 0.85rem; border-radius: 20px; border: 1px solid var(--border); background: var(--card); font-size: 0.8rem; cursor: pointer; transition: all 0.15s; color: var(--text); }}
  .filter-btn:hover {{ background: var(--hover); }}
  .filter-btn.active {{ background: #0078d4; color: white; border-color: #0078d4; }}

  .section {{ padding: 1.5rem 2rem; }}
  .section h2 {{ font-size: 1.25rem; font-weight: 600; margin-bottom: 1rem; display: flex; align-items: center; gap: 0.5rem; }}
  .card {{ background: var(--card); border-radius: 12px; padding: 1.5rem; box-shadow: 0 1px 4px rgba(0,0,0,0.08); margin-bottom: 1rem; }}

  .summary-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 1rem; padding: 1.5rem 2rem; margin-top: -1rem; }}
  .summary-card {{ background: var(--card); border-radius: 12px; padding: 1.25rem; box-shadow: 0 1px 4px rgba(0,0,0,0.08); border-left: 4px solid var(--border); }}
  .summary-card .count {{ font-size: 2rem; font-weight: 700; }}
  .summary-card .label {{ font-size: 0.8rem; color: var(--text-secondary); text-transform: uppercase; letter-spacing: 0.05em; }}

  .executive {{ background: var(--card); border-radius: 12px; padding: 1.5rem; box-shadow: 0 1px 4px rgba(0,0,0,0.08); border-left: 4px solid var(--accent); font-size: 0.95rem; line-height: 1.7; }}
  .executive .trend-up {{ color: var(--improving); font-weight: 600; }}
  .executive .trend-down {{ color: var(--declining); font-weight: 600; }}

  .chart-container {{ background: var(--card); border-radius: 12px; padding: 1.5rem; box-shadow: 0 1px 4px rgba(0,0,0,0.08); overflow-x: auto; }}
  .chart-container svg {{ display: block; margin: 0 auto; }}

  .pillar-table {{ width: 100%; border-collapse: collapse; background: var(--card); border-radius: 12px; overflow: hidden; box-shadow: 0 1px 4px rgba(0,0,0,0.08); }}
  .pillar-table th, .pillar-table td {{ padding: 0.75rem 1rem; text-align: center; border-bottom: 1px solid var(--border); font-size: 0.85rem; }}
  .pillar-table th {{ background: var(--hover); font-weight: 600; text-transform: uppercase; font-size: 0.75rem; letter-spacing: 0.03em; color: var(--text-secondary); }}
  .pillar-table th:first-child, .pillar-table td:first-child {{ text-align: left; font-weight: 600; }}
  .pillar-table tr:last-child td {{ border-bottom: none; }}
  .trend-arrow {{ font-size: 0.8rem; margin-left: 0.25rem; }}
  .trend-arrow.up {{ color: var(--improving); }}
  .trend-arrow.down {{ color: var(--declining); }}

  .diff-section {{ margin-bottom: 1.5rem; }}
  .diff-section h3 {{ font-size: 1rem; font-weight: 600; margin-bottom: 0.75rem; padding-bottom: 0.5rem; border-bottom: 1px solid var(--border); }}
  .diff-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(90px, 1fr)); gap: 0.75rem; margin-bottom: 0.75rem; }}
  .diff-stat {{ text-align: center; padding: 0.75rem; background: var(--hover); border-radius: 8px; }}
  .diff-stat .num {{ font-size: 1.5rem; font-weight: 700; }}
  .diff-stat .lbl {{ font-size: 0.7rem; color: var(--text-secondary); text-transform: uppercase; }}

  .finding-item {{ display: flex; align-items: center; gap: 0.75rem; padding: 0.5rem 0; border-bottom: 1px solid var(--border); }}
  .finding-item:last-child {{ border-bottom: none; }}
  .sev-badge {{ padding: 0.15rem 0.5rem; border-radius: 4px; font-size: 0.7rem; font-weight: 600; text-transform: uppercase; color: white; white-space: nowrap; }}
  .sev-badge.critical {{ background: var(--critical); }}
  .sev-badge.high {{ background: var(--high); }}
  .sev-badge.medium {{ background: var(--medium); }}
  .sev-badge.low {{ background: var(--low); }}
  .finding-text {{ font-size: 0.85rem; }}
  .finding-rule {{ font-size: 0.75rem; color: var(--text-secondary); margin-right: 0.5rem; font-weight: 600; }}

  .empty-state {{ text-align: center; padding: 2rem; color: var(--text-secondary); font-size: 0.9rem; }}

  .footer {{ padding: 2rem; text-align: center; color: var(--text-secondary); font-size: 0.8rem; border-top: 1px solid var(--border); margin-top: 1rem; }}
  .footer a {{ color: #0078d4; text-decoration: none; }}

  @media print {{
    .filters {{ display: none !important; }}
    body {{ background: white; }}
    .card, .chart-container, .executive {{ box-shadow: none; border: 1px solid #ddd; }}
  }}
  @media (max-width: 600px) {{
    .section {{ padding: 1rem; }}
    .header {{ padding: 1.5rem 1rem 1rem; }}
    .summary-grid {{ padding: 1rem; }}
    .filters {{ padding: 0.75rem 1rem; }}
  }}
</style>
</head>
<body>

<div class="header">
  <h1>\\U0001f4c8 Azure Environment Trend Dashboard</h1>
  <div class="subtitle">{subscription}{profile_text}</div>
  <div class="meta">
    <span>\\U0001f4ca {n} assessment{"s" if n != 1 else ""} analyzed</span>
    <span id="meta-range"></span>
  </div>
</div>

<div class="filters">
  <label>Time range:</label>
  <button class="filter-btn active" onclick="applyFilter('all')">All</button>
  <button class="filter-btn" onclick="applyFilter(8)">Last 8</button>
  <button class="filter-btn" onclick="applyFilter(4)">Last 4</button>
</div>

<div id="executive-section" class="section">
  <h2>\\U0001f4cb Executive Summary</h2>
  <div id="executive" class="executive"></div>
</div>

<div class="section">
  <h2>\\U0001f4c8 Overall Score Trend</h2>
  <div id="score-chart" class="chart-container"></div>
</div>

<div class="section">
  <h2>\\U0001f4ca Finding Counts by Severity</h2>
  <div id="bar-chart" class="chart-container"></div>
</div>

<div class="section">
  <h2>\\U0001f3db\\ufe0f Pillar Score Breakdown</h2>
  <div id="pillar-table"></div>
</div>

<div class="section">
  <h2>\\U0001f504 New vs Resolved</h2>
  <div id="new-resolved"></div>
</div>

<div class="section">
  <h2>\\U0001f501 Top Recurring Findings</h2>
  <div id="recurring"></div>
</div>

<div class="footer">
  Generated by <a href="#">Azure Environment Advisor</a> — Trend Dashboard
</div>

<script>
var DATA = {data_json};

var currentFilter = 'all';

function getFiltered(range) {{
  var a = DATA.assessments;
  if (range === 'all' || a.length <= range) return {{ assessments: a, diffs: DATA.diffs, offset: 0 }};
  var offset = a.length - range;
  return {{
    assessments: a.slice(offset),
    diffs: DATA.diffs.slice(Math.max(0, offset - 1)),
    offset: offset
  }};
}}

function applyFilter(range) {{
  currentFilter = range;
  document.querySelectorAll('.filter-btn').forEach(function(b) {{
    b.classList.toggle('active',
      (range === 'all' && b.textContent.trim() === 'All') ||
      (range === 8 && b.textContent.trim() === 'Last 8') ||
      (range === 4 && b.textContent.trim() === 'Last 4'));
  }});
  renderAll();
}}

function renderAll() {{
  var f = getFiltered(currentFilter);
  renderMeta(f.assessments);
  renderExecutive(f.assessments, f.diffs);
  renderLineChart(f.assessments);
  renderBarChart(f.assessments);
  renderPillarTable(f.assessments);
  renderNewResolved(f.diffs);
  renderRecurring();
}}

function renderMeta(assessments) {{
  var el = document.getElementById('meta-range');
  if (assessments.length >= 2) {{
    el.textContent = '\\U0001f4c5 ' + assessments[0].dateLabel + ' \\u2192 ' + assessments[assessments.length - 1].dateLabel;
  }} else if (assessments.length === 1) {{
    el.textContent = '\\U0001f4c5 ' + assessments[0].dateLabel;
  }}
}}

function renderExecutive(assessments, diffs) {{
  var el = document.getElementById('executive');
  var n = assessments.length;
  if (n === 0) {{ el.innerHTML = '<p class="empty-state">No assessment data available.</p>'; return; }}
  if (n === 1) {{
    var a = assessments[0];
    var total = a.findingCount + a.passedCount;
    el.innerHTML = '<p>Single assessment on <strong>' + a.dateLabel + '</strong>. ' +
      'Score: <strong>' + a.score.toFixed(1) + '%</strong> with ' +
      a.findingCount + ' finding' + (a.findingCount !== 1 ? 's' : '') + ' across ' + total + ' checks. ' +
      'Add more assessments to see trends.</p>';
    return;
  }}
  var first = assessments[0], last = assessments[n - 1];
  var diff = last.score - first.score;
  var trend = diff > 2 ? 'improved' : diff < -2 ? 'declined' : 'remained stable';
  var cls = diff > 2 ? 'trend-up' : diff < -2 ? 'trend-down' : '';
  var totalNew = 0, totalResolved = 0;
  diffs.forEach(function(d) {{ totalNew += d['new'].length; totalResolved += d.resolved.length; }});
  el.innerHTML = '<p>Over <strong>' + n + ' assessments</strong> (' + first.dateLabel + ' \\u2192 ' + last.dateLabel + '), ' +
    'your score <span class="' + cls + '">' + trend + ' from ' + first.score.toFixed(1) + '% to ' + last.score.toFixed(1) + '%</span>. ' +
    totalResolved + ' finding' + (totalResolved !== 1 ? 's were' : ' was') + ' resolved and ' +
    totalNew + ' new finding' + (totalNew !== 1 ? 's' : '') + ' appeared.' +
    (last.severityCounts.Critical > 0 ? ' <strong style="color:var(--critical)">' + last.severityCounts.Critical + ' critical finding' + (last.severityCounts.Critical !== 1 ? 's' : '') + ' remain.</strong>' : '') +
    '</p>';
}}

function renderLineChart(assessments) {{
  var el = document.getElementById('score-chart');
  var n = assessments.length;
  if (n === 0) {{ el.innerHTML = '<p class="empty-state">No data.</p>'; return; }}

  var W = 700, H = 280;
  var pL = 55, pR = 20, pT = 30, pB = 50;
  var cW = W - pL - pR, cH = H - pT - pB;

  var svg = '<svg viewBox="0 0 ' + W + ' ' + H + '" xmlns="http://www.w3.org/2000/svg" style="width:100%;max-width:720px;">';
  svg += '<defs><linearGradient id="lg" x1="0" y1="0" x2="0" y2="1">';
  svg += '<stop offset="0%" stop-color="#0078d4" stop-opacity="0.15"/>';
  svg += '<stop offset="100%" stop-color="#0078d4" stop-opacity="0.01"/>';
  svg += '</linearGradient></defs>';

  for (var pct = 0; pct <= 100; pct += 25) {{
    var gy = pT + cH - (pct / 100) * cH;
    svg += '<line x1="' + pL + '" y1="' + gy.toFixed(1) + '" x2="' + (W - pR) + '" y2="' + gy.toFixed(1) + '" stroke="var(--border)" stroke-width="0.5" stroke-dasharray="4,4"/>';
    svg += '<text x="' + (pL - 8) + '" y="' + (gy + 4).toFixed(1) + '" text-anchor="end" fill="var(--text-secondary)" font-size="11">' + pct + '</text>';
  }}

  var pts = assessments.map(function(a, i) {{
    return {{
      x: n > 1 ? pL + i * cW / (n - 1) : pL + cW / 2,
      y: pT + cH - (a.score / 100) * cH,
      score: a.score,
      label: a.dateLabel
    }};
  }});

  if (n > 1) {{
    var area = 'M ' + pts[0].x.toFixed(1) + ',' + pts[0].y.toFixed(1);
    for (var i = 1; i < pts.length; i++) area += ' L ' + pts[i].x.toFixed(1) + ',' + pts[i].y.toFixed(1);
    area += ' L ' + pts[pts.length - 1].x.toFixed(1) + ',' + (pT + cH) + ' L ' + pts[0].x.toFixed(1) + ',' + (pT + cH) + ' Z';
    svg += '<path d="' + area + '" fill="url(#lg)"/>';
    var line = 'M ' + pts.map(function(p) {{ return p.x.toFixed(1) + ',' + p.y.toFixed(1); }}).join(' L ');
    svg += '<path d="' + line + '" fill="none" stroke="#0078d4" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>';
  }}

  pts.forEach(function(p) {{
    svg += '<circle cx="' + p.x.toFixed(1) + '" cy="' + p.y.toFixed(1) + '" r="5" fill="#0078d4" stroke="var(--card)" stroke-width="2"/>';
    svg += '<text x="' + p.x.toFixed(1) + '" y="' + (p.y - 12).toFixed(1) + '" text-anchor="middle" fill="var(--text)" font-size="12" font-weight="600">' + p.score.toFixed(1) + '%</text>';
    svg += '<text x="' + p.x.toFixed(1) + '" y="' + (H - 8) + '" text-anchor="middle" fill="var(--text-secondary)" font-size="10">' + p.label + '</text>';
  }});

  svg += '</svg>';
  el.innerHTML = svg;
}}

function renderBarChart(assessments) {{
  var el = document.getElementById('bar-chart');
  var n = assessments.length;
  if (n === 0) {{ el.innerHTML = '<p class="empty-state">No data.</p>'; return; }}

  var W = 700, H = 300;
  var pL = 55, pR = 20, pT = 35, pB = 50;
  var cW = W - pL - pR, cH = H - pT - pB;

  var sevOrder = ['Critical', 'High', 'Medium', 'Low'];
  var sevColors = {{ Critical: 'var(--critical)', High: 'var(--high)', Medium: 'var(--medium)', Low: 'var(--low)' }};

  var maxTotal = 1;
  assessments.forEach(function(a) {{
    var t = sevOrder.reduce(function(s, k) {{ return s + (a.severityCounts[k] || 0); }}, 0);
    if (t > maxTotal) maxTotal = t;
  }});
  var niceMax = Math.ceil(maxTotal / 5) * 5;

  var svg = '<svg viewBox="0 0 ' + W + ' ' + H + '" xmlns="http://www.w3.org/2000/svg" style="width:100%;max-width:720px;">';

  var lx = pL;
  sevOrder.forEach(function(sev) {{
    svg += '<rect x="' + lx + '" y="8" width="12" height="12" rx="2" fill="' + sevColors[sev] + '"/>';
    svg += '<text x="' + (lx + 16) + '" y="18" fill="var(--text-secondary)" font-size="10">' + sev + '</text>';
    lx += sev.length * 6.5 + 28;
  }});

  for (var frac = 0; frac <= 1.001; frac += 0.25) {{
    var gy = pT + cH - frac * cH;
    var val = Math.round(niceMax * frac);
    svg += '<line x1="' + pL + '" y1="' + gy.toFixed(1) + '" x2="' + (W - pR) + '" y2="' + gy.toFixed(1) + '" stroke="var(--border)" stroke-width="0.5"' + (frac > 0 ? ' stroke-dasharray="4,4"' : '') + '/>';
    svg += '<text x="' + (pL - 8) + '" y="' + (gy + 4).toFixed(1) + '" text-anchor="end" fill="var(--text-secondary)" font-size="11">' + val + '</text>';
  }}

  var barW = Math.min(60, (cW - 20) / n - 10);
  assessments.forEach(function(a, i) {{
    var cx = pL + (i + 0.5) * cW / n;
    var bx = cx - barW / 2;
    var yOff = 0;
    var total = 0;
    sevOrder.forEach(function(sev) {{
      var count = a.severityCounts[sev] || 0;
      total += count;
      if (count === 0) return;
      var bh = (count / niceMax) * cH;
      var by = pT + cH - yOff - bh;
      svg += '<rect x="' + bx.toFixed(1) + '" y="' + by.toFixed(1) + '" width="' + barW.toFixed(1) + '" height="' + bh.toFixed(1) + '" rx="2" fill="' + sevColors[sev] + '"/>';
      if (bh > 14) svg += '<text x="' + cx.toFixed(1) + '" y="' + (by + bh / 2 + 4).toFixed(1) + '" text-anchor="middle" fill="white" font-size="10" font-weight="600">' + count + '</text>';
      yOff += bh;
    }});
    svg += '<text x="' + cx.toFixed(1) + '" y="' + (pT + cH - yOff - 6).toFixed(1) + '" text-anchor="middle" fill="var(--text)" font-size="11" font-weight="600">' + total + '</text>';
    svg += '<text x="' + cx.toFixed(1) + '" y="' + (H - 8) + '" text-anchor="middle" fill="var(--text-secondary)" font-size="10">' + a.dateLabel + '</text>';
  }});

  svg += '</svg>';
  el.innerHTML = svg;
}}

function renderPillarTable(assessments) {{
  var el = document.getElementById('pillar-table');
  var n = assessments.length;
  if (n === 0) {{ el.innerHTML = '<p class="empty-state">No data.</p>'; return; }}

  var allPillars = {{}};
  assessments.forEach(function(a) {{ Object.keys(a.pillarScores).forEach(function(p) {{ allPillars[p] = true; }}); }});
  var pillars = Object.keys(allPillars).sort();

  var html = '<table class="pillar-table"><thead><tr><th>Pillar</th>';
  assessments.forEach(function(a) {{ html += '<th>' + a.dateLabel + '</th>'; }});
  html += '<th>Trend</th></tr></thead><tbody>';

  pillars.forEach(function(pillar) {{
    html += '<tr><td>' + pillar + '</td>';
    var scores = assessments.map(function(a) {{ return a.pillarScores[pillar] !== undefined ? a.pillarScores[pillar] : null; }});
    scores.forEach(function(s) {{
      if (s === null) {{ html += '<td>\\u2014</td>'; return; }}
      var color = s >= 80 ? 'var(--pass)' : s >= 60 ? 'var(--medium)' : s >= 40 ? 'var(--high)' : 'var(--critical)';
      html += '<td style="color:' + color + ';font-weight:600">' + s.toFixed(1) + '%</td>';
    }});
    var valid = scores.filter(function(s) {{ return s !== null; }});
    if (valid.length >= 2) {{
      var diff = valid[valid.length - 1] - valid[0];
      if (diff > 2) html += '<td><span class="trend-arrow up">\\u25b2 +' + diff.toFixed(1) + '</span></td>';
      else if (diff < -2) html += '<td><span class="trend-arrow down">\\u25bc ' + diff.toFixed(1) + '</span></td>';
      else html += '<td><span class="trend-arrow" style="color:var(--stable)">\\u2014 stable</span></td>';
    }} else html += '<td>\\u2014</td>';
    html += '</tr>';
  }});

  html += '</tbody></table>';
  el.innerHTML = html;
}}

function renderNewResolved(diffs) {{
  var el = document.getElementById('new-resolved');
  if (!diffs || diffs.length === 0) {{
    el.innerHTML = '<div class="card"><p class="empty-state">Need at least 2 assessments to compare.</p></div>';
    return;
  }}
  var html = '';
  diffs.forEach(function(d) {{
    html += '<div class="card diff-section">';
    html += '<h3>' + d.fromDate + ' \\u2192 ' + d.toDate + '</h3>';
    html += '<div class="diff-grid">';
    html += '<div class="diff-stat"><div class="num" style="color:var(--critical)">' + d['new'].length + '</div><div class="lbl">New</div></div>';
    html += '<div class="diff-stat"><div class="num" style="color:var(--pass)">' + d.resolved.length + '</div><div class="lbl">Resolved</div></div>';
    html += '<div class="diff-stat"><div class="num" style="color:var(--high)">' + d.escalated.length + '</div><div class="lbl">Escalated</div></div>';
    html += '<div class="diff-stat"><div class="num" style="color:var(--low)">' + d.deEscalated.length + '</div><div class="lbl">De-escalated</div></div>';
    html += '</div>';

    if (d['new'].length > 0) {{
      html += '<div style="margin-bottom:0.5rem"><strong style="font-size:0.8rem;color:var(--text-secondary)">NEW FINDINGS:</strong></div>';
      d['new'].forEach(function(f) {{
        var cls = f.severity ? f.severity.toLowerCase() : 'low';
        html += '<div class="finding-item"><span class="sev-badge ' + cls + '">' + (f.severity || '') + '</span><span class="finding-rule">' + f.rule_id + '</span><span class="finding-text">' + (f.title || '') + '</span></div>';
      }});
    }}
    if (d.resolved.length > 0) {{
      html += '<div style="margin-top:0.75rem;margin-bottom:0.5rem"><strong style="font-size:0.8rem;color:var(--text-secondary)">RESOLVED:</strong></div>';
      d.resolved.forEach(function(f) {{
        html += '<div class="finding-item"><span style="color:var(--pass);font-weight:600;font-size:0.85rem">\\u2713</span><span class="finding-rule">' + f.rule_id + '</span><span class="finding-text">' + (f.title || '') + '</span></div>';
      }});
    }}
    if (d.escalated.length > 0) {{
      html += '<div style="margin-top:0.75rem;margin-bottom:0.5rem"><strong style="font-size:0.8rem;color:var(--text-secondary)">ESCALATED:</strong></div>';
      d.escalated.forEach(function(f) {{
        html += '<div class="finding-item"><span style="color:var(--high);font-weight:600;font-size:0.85rem">\\u2b06</span><span class="finding-rule">' + f.rule_id + '</span><span class="finding-text">' + (f.title || '') + ' (' + f.from + ' \\u2192 ' + f.to + ')</span></div>';
      }});
    }}
    if (d.deEscalated.length > 0) {{
      html += '<div style="margin-top:0.75rem;margin-bottom:0.5rem"><strong style="font-size:0.8rem;color:var(--text-secondary)">DE-ESCALATED:</strong></div>';
      d.deEscalated.forEach(function(f) {{
        html += '<div class="finding-item"><span style="color:var(--pass);font-weight:600;font-size:0.85rem">\\u2b07</span><span class="finding-rule">' + f.rule_id + '</span><span class="finding-text">' + (f.title || '') + ' (' + f.from + ' \\u2192 ' + f.to + ')</span></div>';
      }});
    }}
    html += '</div>';
  }});
  el.innerHTML = html;
}}

function renderRecurring() {{
  var el = document.getElementById('recurring');
  var r = DATA.recurring;
  if (!r || r.length === 0) {{
    el.innerHTML = '<div class="card"><p class="empty-state">No findings appear in every assessment. Great improvement! \\U0001f389</p></div>';
    return;
  }}
  var html = '<div class="card"><p style="font-size:0.85rem;color:var(--text-secondary);margin-bottom:1rem;">These findings have appeared in <strong>every</strong> assessment and have never been resolved:</p>';
  r.forEach(function(f) {{
    var cls = f.severity ? f.severity.toLowerCase() : 'low';
    html += '<div class="finding-item"><span class="sev-badge ' + cls + '">' + (f.severity || '') + '</span><span class="finding-rule">' + f.rule_id + '</span><span class="finding-text">' + (f.title || '') + '</span><span style="font-size:0.75rem;color:var(--text-secondary);margin-left:auto">' + (f.pillar || '') + '</span></div>';
  }});
  html += '</div>';
  el.innerHTML = html;
}}

renderAll();
</script>
</body>
</html>"""


# --- Main ---

def main():
    parser = argparse.ArgumentParser(
        description="Generate a self-contained HTML trend dashboard from multiple assessment baselines",
        epilog="Example: python scripts/generate-trend-dashboard.py --baselines-dir baselines/ --output trend-dashboard.html",
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--baselines-dir",
                       help="Directory containing baseline JSON files")
    group.add_argument("--baselines", nargs="+",
                       help="Explicit list of baseline JSON files")
    parser.add_argument("--output", default="trend-dashboard.html",
                        help="Output HTML file path (default: trend-dashboard.html)")
    args = parser.parse_args()

    # Discover baseline files
    if args.baselines_dir:
        baseline_dir = Path(args.baselines_dir)
        if not baseline_dir.is_dir():
            print(f"Error: '{args.baselines_dir}' is not a directory", file=sys.stderr)
            sys.exit(1)
        files = sorted(baseline_dir.glob("*.json"))
        files = [f for f in files if "schema" not in f.name.lower()]
    else:
        files = [Path(f) for f in args.baselines]

    if not files:
        print("Error: No baseline files found", file=sys.stderr)
        sys.exit(1)

    # Load baselines
    baselines = []
    for f in files:
        try:
            data = load_baseline(f)
            baselines.append(data)
        except Exception as e:
            print(f"Warning: Skipping {f}: {e}", file=sys.stderr)

    if not baselines:
        print("Error: No valid baseline files loaded", file=sys.stderr)
        sys.exit(1)

    # Sort by date
    baselines.sort(key=lambda b: parse_date(b["metadata"].get("date", "")))

    # Build assessment data
    assessments = []
    for b in baselines:
        findings = [f for f in b.get("findings", [])
                    if f.get("status", "finding") != "exception"]
        passed = b.get("passed", [])
        date_str = b["metadata"].get("date", "")
        assessments.append({
            "date": date_str,
            "dateLabel": format_date(date_str),
            "score": calculate_score(b),
            "findingCount": len(findings),
            "passedCount": len(passed),
            "severityCounts": severity_counts(b),
            "pillarScores": calculate_pillar_scores(b),
        })

    # Build pairwise diffs
    diffs = []
    for i in range(1, len(baselines)):
        d = diff_findings(baselines[i - 1], baselines[i])
        diffs.append({
            "fromDate": assessments[i - 1]["dateLabel"],
            "toDate": assessments[i]["dateLabel"],
            "new": [{"rule_id": f["rule_id"], "title": f.get("title", ""),
                     "severity": f.get("severity", "")} for f in d["new"]],
            "resolved": [{"rule_id": f["rule_id"], "title": f.get("title", ""),
                         "severity": f.get("severity", "")} for f in d["resolved"]],
            "escalated": d["escalated"],
            "deEscalated": d["de_escalated"],
        })

    # Find recurring findings
    recurring = find_recurring_findings(baselines)
    recurring_data = [
        {"rule_id": f["rule_id"], "title": f.get("title", ""),
         "severity": f.get("severity", ""), "pillar": f.get("pillar", "")}
        for f in recurring
    ]

    # Assemble data payload
    data = {
        "subscription": baselines[-1]["metadata"].get("subscription_name", "Unknown"),
        "profile": baselines[-1]["metadata"].get("profile", ""),
        "assessments": assessments,
        "diffs": diffs,
        "recurring": recurring_data,
    }

    # Generate and write HTML
    html = generate_html(data)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"Trend dashboard generated: {output_path}")
    print(f"   {len(assessments)} assessments, {len(diffs)} comparisons, {len(recurring_data)} recurring findings")
    sys.exit(0)


if __name__ == "__main__":
    main()
