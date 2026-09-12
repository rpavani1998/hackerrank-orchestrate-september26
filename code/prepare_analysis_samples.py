#!/usr/bin/env python3
"""Merge representative AI analyses with deterministic analyses for all samples."""
from __future__ import annotations

import csv
import json
from datetime import date, datetime, timezone
from pathlib import Path

import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))

from financial_analysis import ANALYSIS_SCHEMA_VERSION, build_financial_analysis  # noqa: E402
from main import Data, load_evidence_facts  # noqa: E402

INPUT = ROOT / "evaluation/financial_analysis_results.json"
OUTPUT = ROOT / "evaluation/financial_analysis_sample_scopes.json"


def main() -> None:
    data = Data()
    evidence = ROOT / "evaluation/message_extraction_results.json"
    if evidence.exists():
        data.evidence_facts = load_evidence_facts(evidence, data.messages)
    live = json.loads(INPUT.read_text(encoding="utf-8")) if INPUT.exists() else {"records": []}
    live_by_scope = {(record["user_id"], record["request_id"], record["as_of_date"]): record for record in live.get("records", [])}
    with (ROOT / "dataset/sample_requests.csv").open(newline="", encoding="utf-8") as fh:
        samples = list(csv.DictReader(fh))
    records = []
    for request in samples:
        scope_key = (request["user_id"], request["request_id"], request["request_date"])
        if scope_key in live_by_scope:
            records.append(live_by_scope[scope_key])
            continue
        as_of = date.fromisoformat(request["request_date"])
        analysis = build_financial_analysis(
            data, request["user_id"], as_of, request["request_id"],
            model_metadata={"mode": "deterministic_fallback", "reason": "no live representative AI scope"},
        )
        records.append({
            "request_id": request["request_id"],
            "user_id": request["user_id"],
            "as_of_date": request["request_date"],
            "status": "deterministic_fallback",
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
        "source": "four live OpenRouter scopes plus deterministic analysis for remaining sample scopes",
    }
    OUTPUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    print(f"wrote {OUTPUT} ({len(records)} scopes; live_ai={sum(r['status'] == 'validated' for r in records)})")


if __name__ == "__main__":
    main()
