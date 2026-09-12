#!/usr/bin/env python3
"""Trace one validated analysis pattern into a deterministic cash-flow event."""
from __future__ import annotations

import json
import sys
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))

from main import Agent, Data, ddate, load_evidence_facts, load_financial_analyses  # noqa: E402

OUTPUT = ROOT / "evaluation/analysis_forecast_trace.md"


def main() -> None:
    samples = json.loads((ROOT / "evaluation/financial_analysis_results.json").read_text(encoding="utf-8"))
    record = next(item for item in samples["records"] if item["request_id"] == "request_02")
    request = next(
        row for row in __import__("csv").DictReader((ROOT / "dataset/sample_requests.csv").open(newline="", encoding="utf-8"))
        if row["request_id"] == "request_02"
    )
    data = Data()
    data.evidence_facts = load_evidence_facts(ROOT / "evaluation/message_extraction_results.json", data.messages)
    data.financial_analyses = load_financial_analyses(ROOT / "evaluation/financial_analysis_results.json")
    agent = Agent(data)
    analysis = record["analysis"]
    forecast_input = next(item for item in analysis["forecast_inputs"] if item["forecastable"])
    source_ids = set(forecast_input["source_event_ids"])
    source_events = {event.event_id: event for event in data.events_by_user[request["user_id"]]}
    projected = [
        item for item in agent.projections(request)
        if source_ids.intersection(item.source_event_ids)
    ]
    if not projected:
        raise RuntimeError("validated forecast input produced no projected event in the horizon")
    first = min(projected, key=lambda item: item.when)
    profile = data.profiles[request["user_id"]]
    start = ddate(request["request_date"])
    end = start + timedelta(days=90)
    ok, lowest, balances = agent.replay(profile.balance, profile.minimum, start, end, agent.projections(request), [])
    lines = [
        "# Validated analysis → forecast trace",
        "",
        "This trace uses `request_02` in AI mode. The model proposes grouping only; "
        "deterministic validation, statistics, projection amounts, and replay calculate the financial effect.",
        "",
        "## Validated pattern",
        "",
        f"- Pattern: `{forecast_input['pattern_id']}` ({forecast_input['pattern_type']})",
        f"- Category/label: `{forecast_input['category']}` / `{forecast_input['label']}`",
        f"- Source event IDs: `{', '.join(forecast_input['source_event_ids'])}`",
        f"- Cadence: `{forecast_input['cadence_kind']}` ({forecast_input['cadence_days']} days)",
        f"- Deterministic amount policy: `{forecast_input['amount_policy']}`; recent median description `{forecast_input['recent_median']}`",
        "",
        "## Source records",
        "",
    ]
    for event_id in forecast_input["source_event_ids"]:
        event = source_events[event_id]
        lines.append(f"- `{event.event_id}`: {event.settlement_date} {event.amount} {event.currency}, {event.description}, status `{event.status}`")
    lines.extend([
        "",
        "## Projected event",
        "",
        f"- Date: `{first.when.isoformat()}`",
        f"- Direction/category: `{first.direction}` / `{first.category}`",
        f"- Amount: `{first.amount}` {profile.home_currency}",
        f"- Projection source IDs: `{', '.join(first.source_event_ids)}`",
        "",
        "## Cash-flow effect",
        "",
        f"- Starting available-balance snapshot: `{profile.balance}` {profile.home_currency}",
        f"- Balance after the first projected event: `{balances[first.when]}` {profile.home_currency}",
        f"- Baseline replay safe through horizon: `{ok}`; lowest projected balance: `{lowest}` {profile.home_currency}",
        "- Historical transactions were not replayed against the supplied starting snapshot.",
        "- No affordability, ranking, spending cut, or reserve-policy decision came from the model.",
    ])
    OUTPUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(OUTPUT)
    print(f"pattern={forecast_input['pattern_id']} projected={first.when.isoformat()} amount={first.amount} {profile.home_currency}")


if __name__ == "__main__":
    main()
