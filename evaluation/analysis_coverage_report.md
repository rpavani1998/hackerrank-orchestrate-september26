# Financial-analysis coverage and source-quality audit

Sample artifact: `/projects/challenge/evaluation/financial_analysis_sample_scopes.json`
250-request artifact checked: `/projects/challenge/evaluation/financial_analysis_all_requests.json`

## Coverage summary

- Required sample scopes: `25`
- Missing sample scopes: `0`
- Sample scopes present in the 250-request artifact: `0/25`
- Accepted-pattern rows: `42`
- Rejected-pattern rows: `4`

The 250-request artifact is not assumed to cover samples based on file size; the intersection is checked by exact `(user_id, as_of_date)` keys.

## Per-sample exact scope and consumption

| Request | User | As of | Artifact loaded | Origin | Accepted | Rejected | Forecast patterns consumed | Fallback/reason |
|---|---|---|---|---|---:|---:|---|---|
| request_01 | user_01 | 2024-03-03 | True | cached_ai | 13 | 0 | ai_pattern_0001, ai_pattern_0002, ai_pattern_0003, ai_pattern_0004, ai_pattern_0005, ai_pattern_0006, ai_pattern_0007, ai_pattern_0008, ai_pattern_0009 | none |
| request_02 | user_02 | 2025-08-05 | True | cached_ai | 19 | 1 | ai_pattern_0001, ai_pattern_0002, ai_pattern_0003, ai_pattern_0004, ai_pattern_0005, ai_pattern_0006, ai_pattern_0007, ai_pattern_0008, ai_pattern_0009, ai_pattern_0010 | none |
| request_03 | user_03 | 2019-09-03 | True | deterministic_construction | 0 | 0 | pattern_0001, pattern_0002, pattern_0003, pattern_0004, pattern_0005, pattern_0006, pattern_0007 | no live representative AI scope |
| request_04 | user_04 | 2024-06-04 | True | deterministic_construction | 0 | 0 | pattern_0001, pattern_0002, pattern_0003, pattern_0004, pattern_0005, pattern_0006, pattern_0007, pattern_0008, pattern_0009, pattern_0010 | no live representative AI scope |
| request_05 | user_05 | 2025-11-06 | True | cached_ai | 9 | 0 | ai_pattern_0001, ai_pattern_0002, ai_pattern_0003, ai_pattern_0004, ai_pattern_0005, ai_pattern_0007, ai_pattern_0008, pattern_0008, pattern_0010 | none |
| request_06 | user_06 | 2026-01-03 | True | deterministic_construction | 0 | 0 | pattern_0001, pattern_0002, pattern_0003, pattern_0004, pattern_0005, pattern_0006, pattern_0007, pattern_0008, pattern_0009, pattern_0010, pattern_0011 | no live representative AI scope |
| request_07 | user_07 | 2024-09-05 | True | deterministic_construction | 0 | 0 | pattern_0001, pattern_0002, pattern_0003, pattern_0004, pattern_0005, pattern_0006 | no live representative AI scope |
| request_08 | user_08 | 2025-02-07 | True | deterministic_construction | 0 | 0 | pattern_0001, pattern_0002, pattern_0003, pattern_0004, pattern_0005, pattern_0006, pattern_0007, pattern_0008, pattern_0009, pattern_0010 | no live representative AI scope |
| request_09 | user_09 | 2026-07-04 | True | deterministic_construction | 0 | 0 | pattern_0001, pattern_0002, pattern_0003, pattern_0004, pattern_0005, pattern_0006 | no live representative AI scope |
| request_10 | user_10 | 2024-12-06 | True | deterministic_construction | 0 | 0 | pattern_0001, pattern_0002, pattern_0004, pattern_0005, pattern_0006, pattern_0007, pattern_0008, pattern_0009, pattern_0010 | no live representative AI scope |
| request_11 | user_11 | 2025-05-03 | True | deterministic_construction | 0 | 0 | pattern_0001, pattern_0002, pattern_0003, pattern_0004, pattern_0005, pattern_0006, pattern_0008, pattern_0009, pattern_0010, pattern_0011 | no live representative AI scope |
| request_12 | user_12 | 2026-04-05 | True | deterministic_construction | 0 | 0 | pattern_0001, pattern_0002, pattern_0003, pattern_0004, pattern_0005, pattern_0006 | no live representative AI scope |
| request_13 | user_13 | 2024-03-07 | True | deterministic_construction | 0 | 0 | pattern_0001, pattern_0002, pattern_0003, pattern_0005, pattern_0006, pattern_0007, pattern_0008, pattern_0009, pattern_0010, pattern_0011 | no live representative AI scope |
| request_14 | user_14 | 2025-08-04 | True | deterministic_construction | 0 | 0 | pattern_0001, pattern_0002, pattern_0003, pattern_0004, pattern_0005, pattern_0006, pattern_0007, pattern_0008, pattern_0009 | no live representative AI scope |
| request_15 | user_15 | 2026-01-06 | True | deterministic_construction | 0 | 0 | pattern_0001, pattern_0002, pattern_0003, pattern_0004, pattern_0005, pattern_0006, pattern_0007, pattern_0008, pattern_0009 | no live representative AI scope |
| request_16 | user_16 | 2023-08-12 | True | deterministic_construction | 0 | 0 | pattern_0001, pattern_0002, pattern_0003, pattern_0004, pattern_0005, pattern_0006, pattern_0007, pattern_0008, pattern_0009, pattern_0010 | no live representative AI scope |
| request_17 | user_17 | 2026-03-01 | True | deterministic_construction | 0 | 0 | pattern_0001, pattern_0002, pattern_0003, pattern_0004, pattern_0005, pattern_0006, pattern_0007, pattern_0008, pattern_0009, pattern_0010 | no live representative AI scope |
| request_18 | user_18 | 2026-07-07 | True | deterministic_construction | 0 | 0 | pattern_0001, pattern_0002, pattern_0003, pattern_0004, pattern_0005, pattern_0006, pattern_0007, pattern_0008, pattern_0009 | no live representative AI scope |
| request_19 | user_19 | 2024-09-04 | True | deterministic_construction | 0 | 0 | pattern_0001, pattern_0002, pattern_0003, pattern_0004, pattern_0005, pattern_0006, pattern_0007, pattern_0008, pattern_0009, pattern_0010 | no live representative AI scope |
| request_20 | user_20 | 2026-02-07 | True | cached_ai | 1 | 3 | pattern_0001, pattern_0002, pattern_0003, pattern_0004, pattern_0005, pattern_0006, pattern_0007, pattern_0008, pattern_0009, pattern_0010 | none |
| request_21 | user_21 | 2026-04-03 | True | deterministic_construction | 0 | 0 | pattern_0001, pattern_0002, pattern_0003, pattern_0004, pattern_0005, pattern_0006, pattern_0007 | no live representative AI scope |
| request_22 | user_22 | 2024-12-05 | True | deterministic_construction | 0 | 0 | pattern_0001, pattern_0002, pattern_0003, pattern_0004, pattern_0005, pattern_0006, pattern_0007, pattern_0008, pattern_0009, pattern_0010 | no live representative AI scope |
| request_23 | user_23 | 2025-05-07 | True | deterministic_construction | 0 | 0 | pattern_0001, pattern_0002, pattern_0003, pattern_0004, pattern_0005, pattern_0006, pattern_0007, pattern_0008, pattern_0009, pattern_0010 | no live representative AI scope |
| request_24 | user_24 | 2026-01-04 | True | deterministic_construction | 0 | 0 | pattern_0001, pattern_0002, pattern_0003, pattern_0004, pattern_0005, pattern_0006, pattern_0007, pattern_0008, pattern_0009, pattern_0010, pattern_0011 | no live representative AI scope |
| request_25 | user_25 | 2024-03-06 | True | deterministic_construction | 0 | 0 | pattern_0001, pattern_0002, pattern_0003, pattern_0004, pattern_0005, pattern_0006, pattern_0007, pattern_0008, pattern_0009, pattern_0010, pattern_0011 | no live representative AI scope |

## Analysis-quality findings independent of acceptance

### Incorrect accepted patterns (0)
- None detected by the independent source checks.

### Correct patterns rejected by validator review (0)
- None detected by the independent source checks.

### Supported recurring commitments missed by live AI proposals (7)
- `{"label": "School fee payment", "pattern_id": "pattern_0001", "request_id": "request_20", "source_event_ids": ["event_1705", "event_1713", "event_1721", "event_1729", "event_1737"]}`
- `{"label": "Family healthcare expense", "pattern_id": "pattern_0002", "request_id": "request_20", "source_event_ids": ["event_1706", "event_1714", "event_1722", "event_1730", "event_1738"]}`
- `{"label": "Home association fee", "pattern_id": "pattern_0003", "request_id": "request_20", "source_event_ids": ["event_1702", "event_1710", "event_1718", "event_1726", "event_1734", "event_1741"]}`
- `{"label": "Household insurance", "pattern_id": "pattern_0004", "request_id": "request_20", "source_event_ids": ["event_1704", "event_1712", "event_1720", "event_1728", "event_1736", "event_1743"]}`
- `{"label": "Municipal utilities", "pattern_id": "pattern_0005", "request_id": "request_20", "source_event_ids": ["event_1703", "event_1711", "event_1719", "event_1727", "event_1735", "event_1742"]}`
- `{"label": "Payroll credit", "pattern_id": "pattern_0006", "request_id": "request_20", "source_event_ids": ["event_1701", "event_1709", "event_1717", "event_1725", "event_1733"]}`
- `{"label": "Shared storage plan", "pattern_id": "pattern_0007", "request_id": "request_20", "source_event_ids": ["event_1708", "event_1716", "event_1724", "event_1732", "event_1740"]}`

### Variable-spending omissions (0)
- None detected by the independent source checks.

### Double-counted source events (0)
- None detected by the independent source checks.

### Unsupported future income (0)
- None detected by the independent source checks.

### Unresolved evidence/assumptions (9)
- `{"index": 19, "proposal": {"alternative_interpretations": ["Could be cancelled prior to final settlement."], "category": "shopping", "grouping_rationale": "Explicitly pending future commitment representing an unusual or one-time shopping debit.", "label": "Pending merchant debit", "pattern_type": "one_time", "source_event_ids": ["event_185"], "supporting_observations": [{"observation": "Pending merchant debit of 1651100.00 IDR scheduled for settlement on 2025-08-08", "source_event_id": "event_185"}], "uncertainty": "Status is pending and settlement date may shift."}, "reason": "pattern contains an unknown source event ID", "request_id": "request_02"}`
- `{"ambiguities": [], "conflicts": [], "reason": "unresolved evidence status or ambiguity", "request_id": "request_04", "source_id": "message_03", "update_status": "pending"}`
- `{"ambiguities": [], "conflicts": [], "reason": "unresolved evidence status or ambiguity", "request_id": "request_10", "source_id": "message_07", "update_status": "pending"}`
- `{"ambiguities": ["Specific numerical rent amount and effective date are not provided."], "conflicts": [], "reason": "unresolved evidence status or ambiguity", "request_id": "request_16", "source_id": "message_12", "update_status": "amended"}`
- `{"ambiguities": [], "conflicts": [], "reason": "unresolved evidence status or ambiguity", "request_id": "request_20", "source_id": "message_14", "update_status": "delayed"}`
- `{"index": 1, "proposal": {"alternative_interpretations": ["May not clear if merchant cancels."], "category": "shopping", "grouping_rationale": "Single future credit event representing a pending refund.", "label": "Pending merchant refund", "pattern_type": "one_time", "source_event_ids": ["event_1785"], "supporting_observations": [{"observation": "Pending merchant refund credit of 8640.00 INR.", "source_event_id": "event_1785"}], "uncertainty": "Settlement date is delayed."}, "reason": "pattern contains an unknown source event ID", "request_id": "request_20"}`
- `{"index": 2, "proposal": {"alternative_interpretations": ["Could become recurring if part of a regular telecom subscription plan."], "category": "utilities", "grouping_rationale": "Single pending utility expense obligation.", "label": "Outstanding telecom bill", "pattern_type": "one_time", "source_event_ids": ["event_1786"], "supporting_observations": [{"observation": "Outstanding telecom bill of 704.05 INR.", "source_event_id": "event_1786"}], "uncertainty": "Future commitment pending settlement."}, "reason": "pattern contains an unknown source event ID", "request_id": "request_20"}`
- `{"index": 3, "proposal": {"alternative_interpretations": ["Could be cancelled prior to settlement."], "category": "shopping", "grouping_rationale": "Single pending online purchase charge.", "label": "Pending online order charge", "pattern_type": "one_time", "source_event_ids": ["event_1787"], "supporting_observations": [{"observation": "Pending online order charge of 4470.00 INR.", "source_event_id": "event_1787"}], "uncertainty": "Pending transaction status."}, "reason": "pattern contains an unknown source event ID", "request_id": "request_20"}`
- `{"ambiguities": [], "conflicts": [], "reason": "unresolved evidence status or ambiguity", "request_id": "request_23", "source_id": "message_16", "update_status": "pending"}`

## Strict-mode result

- PASS
