#!/usr/bin/env python3
"""Materialize request-scoped deterministic financial analyses for a dataset file."""
from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import date, datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))

from financial_analysis import ANALYSIS_SCHEMA_VERSION, build_financial_analysis  # noqa: E402
from main import Data, load_evidence_facts  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Build scoped deterministic financial analysis artifact")
    parser.add_argument("--requests-file", type=Path, default=ROOT / "dataset/requests.csv")
    parser.add_argument("--output", type=Path, default=ROOT / "evaluation/financial_analysis_all_requests.json")
    args = parser.parse_args()
    data = Data()
    evidence = ROOT / "evaluation/message_extraction_results.json"
    if evidence.exists():
        data.evidence_facts = load_evidence_facts(evidence, data.messages)
    with args.requests_file.open(newline="", encoding="utf-8") as fh:
        requests = list(csv.DictReader(fh))
    records = []
    for request in requests:
        as_of = date.fromisoformat(request["request_date"])
        analysis = build_financial_analysis(
            data, request["user_id"], as_of, request["request_id"],
            model_metadata={"mode": "deterministic", "source": str(args.requests_file.relative_to(ROOT))},
        )
        records.append({
            "request_id": request["request_id"],
            "user_id": request["user_id"],
            "as_of_date": request["request_date"],
            "status": "deterministic",
            "analysis": analysis,
        })
    payload = {
        "schema_version": ANALYSIS_SCHEMA_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "scope_count": len(records),
        "records": records,
        "analyses_by_scope": {
            f"{record['user_id']}|{record['as_of_date']}": record["analysis"]
            for record in records
        },
        "source": "deterministic scoped analyses; no sample answer fields used",
    }
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    print(f"wrote {args.output} ({len(records)} scopes)")


if __name__ == "__main__":
    main()
