#!/usr/bin/env python3
"""
Generate a Markdown experiment report from workspace JSON files.

Usage:
    python generate_report.py <workspace_dir> [--output report.md]

Reads experiment.json, round-*/hypotheses.json, round-*/variant-*/observations.json,
round-*/comparison.json, round-*/synthesis.md, and final/learnings.json.
"""

import json
import sys
import os
from pathlib import Path
from datetime import datetime


def load_json(path):
    """Load a JSON file, return None if missing."""
    try:
        with open(path) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"  Warning: Could not load {path}: {e}", file=sys.stderr)
        return None


def generate_report(workspace_dir, output_path=None):
    ws = Path(workspace_dir)
    experiment = load_json(ws / "experiment.json")

    lines = []
    add = lines.append

    # --- Header ---
    add("---")
    add("disclaimer: >")
    add("  No information within this document should be taken for granted.")
    add("  Any statement or premise not backed by a real logical definition")
    add("  or verifiable reference may be invalid, erroneous, or a hallucination.")
    add("---")
    add("")

    exp_id = experiment.get("experiment_id", "unknown") if experiment else "unknown"
    add(f"# Experiment Report: {exp_id}")
    add("")
    add(f"**Generated**: {datetime.now().isoformat()}")
    add("")

    if experiment:
        add(f"**Objective**: {experiment.get('objective', 'N/A')}")
        add(f"**Medium**: {experiment.get('medium', 'N/A')}")
        add("")

        dims = experiment.get("evaluation_dimensions", [])
        if dims:
            add("## Evaluation Dimensions")
            add("")
            add("| Dimension | Weight | Description |")
            add("|-----------|--------|-------------|")
            for d in dims:
                add(f"| {d['label']} | {d['weight']} | {d['description']} |")
            add("")

        thresh = experiment.get("success_threshold", {})
        if thresh:
            add(f"**Success Threshold**: min {thresh.get('min_per_dimension', '?')}/dim, "
                f"avg {thresh.get('weighted_average', '?')}")
            add("")

    # --- Rounds ---
    round_dirs = sorted(ws.glob("round-*"))
    for rd in round_dirs:
        round_num = rd.name.split("-")[1]
        add(f"## Round {round_num}")
        add("")

        # Hypotheses
        hyp = load_json(rd / "hypotheses.json")
        if hyp:
            add("### Hypotheses")
            add("")
            for v in hyp.get("variants", []):
                add(f"**{v['id']}**: {v['hypothesis']}")
                if v.get("parent_variants"):
                    add(f"  *Parents*: {', '.join(v['parent_variants'])}")
                add("")

        # Variant observations
        variant_dirs = sorted(rd.glob("variant-*"))
        if variant_dirs:
            add("### Observations")
            add("")
            for vd in variant_dirs:
                obs = load_json(vd / "observations.json")
                if obs:
                    vid = obs.get("variant_id", vd.name)
                    add(f"#### {vid}")
                    va = obs.get("visual_assessment", {})
                    if va:
                        add(f"*Overall*: {va.get('overall_impression', 'N/A')}")
                        add("")
                    scores = obs.get("dimension_scores", [])
                    if scores:
                        add("| Dimension | Score | Justification |")
                        add("|-----------|-------|---------------|")
                        for s in scores:
                            add(f"| {s['dimension_id']} | {s['score']}/10 | {s['justification']} |")
                        add("")
                    metrics = obs.get("programmatic_metrics", {})
                    if metrics:
                        parts = [f"{k}: {v}" for k, v in metrics.items()]
                        add(f"*Metrics*: {', '.join(parts)}")
                        add("")

        # Comparison
        comp = load_json(rd / "comparison.json")
        if comp:
            add("### Comparison Matrix")
            add("")
            matrix = comp.get("matrix", {})
            if matrix:
                # Get variant names from first dimension
                first_dim = next(iter(matrix.values()), {})
                variants = list(first_dim.keys())
                header = "| Dimension | " + " | ".join(variants) + " |"
                sep = "|-----------|" + "|".join(["-------"] * len(variants)) + "|"
                add(header)
                add(sep)
                for dim, scores in matrix.items():
                    row = f"| {dim} | " + " | ".join(
                        str(scores.get(v, "?")) for v in variants
                    ) + " |"
                    add(row)
                add("")

            analysis = comp.get("analysis", {})
            if analysis:
                add("### Analysis")
                add("")
                if analysis.get("key_insight"):
                    add(f"**Key Insight**: {analysis['key_insight']}")
                    add("")
                carry = analysis.get("techniques_to_carry_forward", [])
                if carry:
                    add("**Carry forward**: " + "; ".join(carry))
                    add("")

        # Synthesis
        synth_path = rd / "synthesis.md"
        if synth_path.exists():
            add("### Synthesis")
            add("")
            add(synth_path.read_text())
            add("")

    # --- Final ---
    learnings = load_json(ws / "final" / "learnings.json")
    if learnings:
        add("## Final Results")
        add("")
        add(f"**Best variant**: {learnings.get('best_variant', 'N/A')}")
        add(f"**Total rounds**: {learnings.get('total_rounds', '?')}")
        add(f"**Total variants tested**: {learnings.get('total_variants_tested', '?')}")
        add("")

        final_scores = learnings.get("final_scores", {})
        if final_scores:
            add("### Final Scores")
            add("")
            add("| Dimension | Score |")
            add("|-----------|-------|")
            for k, v in final_scores.items():
                add(f"| {k} | {v}/10 |")
            add("")

        kl = learnings.get("key_learnings", [])
        if kl:
            add("## Key Learnings")
            add("")
            for i, l in enumerate(kl, 1):
                add(f"### Learning {i}: {l['insight']}")
                add(f"*Evidence*: {l['evidence']}")
                add(f"*Generalizability*: {l['generalizability']}")
                add("")

        failed = learnings.get("failed_approaches", [])
        if failed:
            add("## Failed Approaches")
            add("")
            for f_item in failed:
                add(f"**{f_item['approach']}**: {f_item['why_failed']}")
                add(f"*Lesson*: {f_item['lesson']}")
                add("")

    report = "\n".join(lines)

    if output_path:
        Path(output_path).write_text(report)
        print(f"Report written to {output_path}")
    else:
        default = ws / "final" / "experiment-report.md"
        default.parent.mkdir(parents=True, exist_ok=True)
        default.write_text(report)
        print(f"Report written to {default}")

    return report


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python generate_report.py <workspace_dir> [--output path]")
        sys.exit(1)

    workspace = sys.argv[1]
    output = None
    if "--output" in sys.argv:
        idx = sys.argv.index("--output")
        if idx + 1 < len(sys.argv):
            output = sys.argv[idx + 1]

    generate_report(workspace, output)
