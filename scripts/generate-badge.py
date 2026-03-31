#!/usr/bin/env python3
"""Generate shields.io endpoint-badge JSON from governance baseline results.

Reads baseline JSON files produced by azure-environment-advisor and outputs
shields.io endpoint JSON (https://shields.io/badges/endpoint-badge) showing
the governance score as a colour-coded percentage badge.

Score = passed / (passed + findings) * 100

Colour thresholds:
    >=80  green
    >=60  yellow
    >=40  orange
    <40   red

Usage:
    # Single baseline file
    python scripts/generate-badge.py --baseline baselines/baseline-latest.json --output badge/score.json

    # Pick the latest baseline from a directory (by metadata.date)
    python scripts/generate-badge.py --baselines-dir baselines/ --output badge/score.json

    # Multi-subscription mode: one badge per subscription + overall average
    python scripts/generate-badge.py --baselines-dir baselines/ --output badge/score.json --multi
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path


def load_baseline(path: Path) -> dict:
    """Load and minimally validate a baseline JSON file."""
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    for key in ("metadata", "findings", "passed"):
        if key not in data:
            raise ValueError(f"{path}: missing required key '{key}'")
    return data


def calculate_score(baseline: dict) -> int:
    """Return governance score as an integer percentage (0-100)."""
    passed = len(baseline["passed"])
    findings = len(baseline["findings"])
    total = passed + findings
    if total == 0:
        return 100  # no rules evaluated → perfect by default
    return round(passed / total * 100)


def score_color(score: int) -> str:
    """Map a score to a shields.io colour name."""
    if score >= 80:
        return "green"
    if score >= 60:
        return "yellow"
    if score >= 40:
        return "orange"
    return "red"


def make_badge(label: str, score: int) -> dict:
    """Build a shields.io endpoint-badge JSON object."""
    return {
        "schemaVersion": 1,
        "label": label,
        "message": f"{score}%",
        "color": score_color(score),
    }


def write_badge(badge: dict, path: Path) -> None:
    """Write badge JSON to *path*, creating parent directories as needed."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(badge, f, indent=2)
        f.write("\n")


def find_baselines(directory: Path) -> list[Path]:
    """Return all *.json files in *directory* that look like baselines."""
    candidates: list[Path] = []
    for entry in sorted(directory.iterdir()):
        if entry.suffix == ".json" and entry.name != "baseline-schema.json":
            try:
                load_baseline(entry)
                candidates.append(entry)
            except (json.JSONDecodeError, ValueError, KeyError):
                continue
    return candidates


def pick_latest(baselines: list[Path]) -> Path:
    """Return the baseline with the latest metadata.date."""
    if not baselines:
        raise SystemExit("No valid baseline files found in the directory.")

    def date_key(p: Path) -> str:
        with open(p, encoding="utf-8") as f:
            return json.load(f).get("metadata", {}).get("date", "")

    return max(baselines, key=date_key)


def run_single(baseline_path: Path, output: Path) -> None:
    """Generate a single overall governance-score badge."""
    baseline = load_baseline(baseline_path)
    score = calculate_score(baseline)
    badge = make_badge("governance score", score)
    write_badge(badge, output)
    print(f"Badge written to {output}  (score: {score}%, color: {badge['color']})")


def run_multi(baselines_dir: Path, output: Path) -> None:
    """Generate per-subscription badges and an overall average badge."""
    baselines = find_baselines(baselines_dir)
    if not baselines:
        raise SystemExit(f"No valid baseline files found in {baselines_dir}")

    output_dir = output.parent
    scores: list[int] = []

    for path in baselines:
        baseline = load_baseline(path)
        sub_name = baseline["metadata"].get("subscription_name", path.stem)
        score = calculate_score(baseline)
        scores.append(score)

        sub_badge = make_badge(f"governance · {sub_name}", score)
        sub_path = output_dir / f"{sub_name}.json"
        write_badge(sub_badge, sub_path)
        print(f"  {sub_path}  ({score}%)")

    overall = round(sum(scores) / len(scores))
    overall_badge = make_badge("governance score", overall)
    write_badge(overall_badge, output)
    print(f"Overall badge: {output}  (avg: {overall}%, color: {overall_badge['color']})")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate shields.io endpoint-badge JSON from governance baselines.",
    )

    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument(
        "--baseline",
        type=Path,
        help="Path to a single baseline JSON file.",
    )
    source.add_argument(
        "--baselines-dir",
        type=Path,
        help="Directory containing baseline JSON files (picks latest by date).",
    )

    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="Output path for the badge JSON (e.g. badge/score.json).",
    )
    parser.add_argument(
        "--multi",
        action="store_true",
        help="Generate one badge per subscription plus an overall average badge.",
    )

    args = parser.parse_args(argv)

    if args.multi and not args.baselines_dir:
        parser.error("--multi requires --baselines-dir")

    return args


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)

    if args.multi:
        run_multi(args.baselines_dir, args.output)
    elif args.baselines_dir:
        latest = pick_latest(find_baselines(args.baselines_dir))
        print(f"Using latest baseline: {latest}")
        run_single(latest, args.output)
    else:
        if not args.baseline.exists():
            raise SystemExit(f"File not found: {args.baseline}")
        run_single(args.baseline, args.output)


if __name__ == "__main__":
    main()
