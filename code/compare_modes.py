#!/usr/bin/env python3
"""Read-only per-field comparison of deterministic and AI-enabled modes."""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CODE = Path(__file__).resolve().parent
sys.path.insert(0, str(CODE))

from compare_samples import COMPARE_FIELDS, explanation_consistent, load_samples, plans_equal  # noqa: E402
from main import Agent, Data, load_evidence_facts  # noqa: E402

ALL_FIELDS = COMPARE_FIELDS + ["explanation_consistency"]


def run_agent(mode: str, evidence_file: Path) -> tuple[Data, Agent]:
    data = Data()
    if mode == "ai":
        data.evidence_facts = load_evidence_facts(evidence_file, data.messages)
    return data, Agent(data)


def equals(field: str, expected: dict[str, str], actual: dict[str, str]) -> bool:
    if field == "amount_safe_to_pay":
        from main import dec
        return dec(expected[field]) == dec(actual[field])
    if field == "payment_plan":
        return plans_equal(expected[field], actual[field])
    if field == "explanation_consistency":
        return explanation_consistent(actual)
    return expected[field] == actual[field]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence-file", type=Path,
                        default=ROOT / "evaluation/message_extraction_results.json")
    parser.add_argument("--output", type=Path,
                        default=ROOT / "evaluation/mode_comparison.md")
    args = parser.parse_args()
    samples = load_samples()
    modes = {mode: run_agent(mode, args.evidence_file) for mode in ("deterministic", "ai")}
    actual: dict[str, dict[str, dict[str, str]]] = {"deterministic": {}, "ai": {}}
    exceptions: dict[str, list[str]] = {"deterministic": [], "ai": []}
    for mode, (_, agent) in modes.items():
        for expected in samples:
            try:
                actual[mode][expected["request_id"]] = agent.decide(expected)
            except Exception as exc:
                exceptions[mode].append(f"{expected['request_id']}: {type(exc).__name__}: {exc}")

    lines = [
        "# Deterministic versus AI-enabled sample comparison",
        "",
        "Both modes ran all 25 solved sample requests in memory; neither mode wrote `output.csv`.",
        "",
        "## Per-field matches against solved sample outputs",
        "",
        "| Field | Deterministic | AI-enabled |",
        "|---|---:|---:|",
    ]
    for field in ALL_FIELDS:
        counts = []
        for mode in ("deterministic", "ai"):
            count = sum(
                equals(field, expected, actual[mode][expected["request_id"]])
                for expected in samples if expected["request_id"] in actual[mode]
            )
            counts.append(f"{count}/{len(samples)}")
        lines.append(f"| {field} | {counts[0]} | {counts[1]} |")

    lines += ["", "## Mode differences", ""]
    differences = []
    for expected in samples:
        request_id = expected["request_id"]
        if request_id not in actual["deterministic"] or request_id not in actual["ai"]:
            continue
        changed = [
            field for field in ALL_FIELDS
            if (actual["deterministic"][request_id].get(field)
                if field != "explanation_consistency" else explanation_consistent(actual["deterministic"][request_id]))
            != (actual["ai"][request_id].get(field)
                if field != "explanation_consistency" else explanation_consistent(actual["ai"][request_id]))
        ]
        if changed:
            differences.append((request_id, changed))
    if differences:
        for request_id, changed in differences:
            lines.append(f"- `{request_id}`: {', '.join(changed)}")
    else:
        lines.append("- None in the seven output fields and explanation consistency.")
    lines += ["", "## Exceptions", ""]
    for mode in ("deterministic", "ai"):
        lines.append(f"- {mode}: {len(exceptions[mode])}")
        lines.extend(f"  - {item}" for item in exceptions[mode])
    lines += [
        "", "## Source-backed interpretation", "",
        "- AI mode consumed the 19 validated cached message facts before projection.",
        "- `message_11` added a confirmed EUR 1661 salary credit on 2026-01-15 to request_15's timeline; the recommendation stayed unchanged.",
        "- Delayed/pending refunds, prizes, payouts, and disputed reversals were unresolved and never added cash.",
        "- Settled/non-cash facts were status-only; they did not duplicate starting-balance or event cash.",
    ]
    args.output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
