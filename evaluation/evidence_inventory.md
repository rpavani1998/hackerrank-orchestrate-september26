# Evidence inventory and extraction readiness

Generated without model calls. This artifact inventories the supplied evidence and records the provider blocker before any AI integration.

## Inventory summary

| Dataset | Count | Links |
|---|---:|---|
| messages.csv | 215 | 128 request links; 39 event links |
| images.csv | 16 | 16 users; 16 requests; 16 events |

Message source types:

- `bank`: 18
- `employer`: 126
- `financial_service`: 23
- `merchant`: 17
- `service_provider`: 31

Keyword triage labels are overlapping inventory labels, not financial extraction results:

- `amendment`: 125
- `cancellation`: 5
- `confirmation`: 102
- `delay`: 30
- `non_cash`: 7
- `other`: 52
- `refund`: 19
- `settlement`: 59

## Model access and environment

- No `OPENAI`, `ANTHROPIC`, `GEMINI`, `GOOGLE`, `AZURE`, `OLLAMA`, model, token, or key environment variable was configured.
- No model SDK, OCR package, vision package, or document-processing library is installed.
- No dependency manifest or model configuration file is present in the project.
- Outbound HTTPS is available at the network layer, but an unauthenticated provider endpoint returned HTTP 401. No credential was available, so no model call was attempted.
- The supported implementation in this iteration is the standard-library contract in `code/evidence_extraction.py`; it fails explicitly with `ModelAccessUnavailable` rather than silently using an unknown model.

## Financial information the current engine misses

`code/main.py` currently extracts only a narrow payroll fact from messages: a salary-like amount plus an ISO date. It does not structurally extract or apply:

- transaction cancellations, reversals, disputes, or settlement status amendments;
- delayed refunds and whether a pending credit has actually reached the account;
- approved versus pending invoice or service-provider payouts;
- first salary, resumed salary, ended employment, temporary pay, unpaid-leave adjustments, and one-off payroll components as distinct facts;
- recurring rent, childcare, or other expense amendments from provider/employer messages;
- foreign-currency settlement-date conversion statements;
- investment or prize messages that explicitly distinguish realized cash from unrealized value;
- image amount roles such as subtotal, total, already-paid amount, amount due, or remaining balance.

Messages and images are untrusted evidence. Embedded instructions must never be treated as extraction or financial-policy commands.

## Complete message inventory

Each row is one supplied message. `triage` is a lexical review label only; it is not a trusted fact and is not used by the engine.

| ID | Source | Request | Event | Sent at | Triage |
|---|---|---|---|---|---|
| `message_01` | `employer` | `` | `` | `2025-07-29T09:30:00Z` | amendment |
| `message_02` | `employer` | `request_03` | `` | `2019-08-31T09:30:00Z` | other |
| `message_03` | `employer` | `request_04` | `` | `2024-06-01T09:30:00Z` | other |
| `message_04` | `employer` | `request_06` | `` | `2025-12-28T09:30:00Z` | amendment, confirmation |
| `message_05` | `employer` | `` | `` | `2024-08-29T09:30:00Z` | amendment, confirmation |
| `message_06` | `employer` | `request_08` | `` | `2025-02-06T09:30:00Z` | amendment, settlement, confirmation |
| `message_07` | `service_provider` | `request_10` | `` | `2024-11-25T09:30:00Z` | amendment, delay, settlement |
| `message_08` | `employer` | `request_11` | `` | `2025-04-22T09:30:00Z` | other |
| `message_09` | `employer` | `` | `` | `2026-03-25T09:30:00Z` | amendment, settlement, confirmation |
| `message_10` | `employer` | `` | `` | `2025-07-27T09:30:00Z` | amendment |
| `message_11` | `employer` | `request_15` | `` | `2026-01-03T09:30:00Z` | amendment, confirmation |
| `message_12` | `service_provider` | `request_16` | `` | `2023-08-01T09:30:00Z` | amendment |
| `message_13` | `bank` | `request_18` | `` | `2026-07-01T09:30:00Z` | amendment |
| `message_14` | `merchant` | `request_20` | `event_1785` | `2026-02-06T09:30:00Z` | amendment, delay, settlement, refund |
| `message_15` | `financial_service` | `request_22` | `event_1960` | `2024-12-02T09:30:00Z` | amendment, non_cash |
| `message_16` | `financial_service` | `request_23` | `` | `2025-04-26T09:30:00Z` | settlement, confirmation |
| `message_17` | `financial_service` | `` | `event_2165` | `2025-12-29T09:30:00Z` | settlement, confirmation |
| `message_18` | `service_provider` | `` | `` | `2025-07-27T09:30:00Z` | other |
| `message_19` | `service_provider` | `request_27` | `` | `2026-06-27T09:30:00Z` | amendment, delay, settlement |
| `message_20` | `employer` | `request_28` | `` | `2024-06-04T09:30:00Z` | amendment |
| `message_21` | `employer` | `` | `` | `2025-10-27T09:30:00Z` | amendment, settlement, confirmation |
| `message_22` | `employer` | `request_32` | `` | `2025-01-24T09:30:00Z` | amendment, confirmation |
| `message_23` | `bank` | `request_33` | `` | `2026-01-03T09:30:00Z` | other |
| `message_24` | `service_provider` | `` | `` | `2024-11-23T09:30:00Z` | settlement, confirmation |
| `message_25` | `merchant` | `` | `event_3230` | `2025-10-20T09:30:00Z` | amendment, delay, settlement, refund |
| `message_26` | `employer` | `request_36` | `` | `2026-06-22T09:30:00Z` | amendment |
| `message_27` | `employer` | `` | `` | `2024-03-01T09:30:00Z` | other |
| `message_28` | `financial_service` | `` | `event_3491` | `2025-08-06T09:30:00Z` | settlement, confirmation |
| `message_29` | `employer` | `` | `` | `2024-06-03T09:30:00Z` | amendment, confirmation |
| `message_30` | `employer` | `request_42` | `` | `2025-12-31T09:30:00Z` | amendment, confirmation |
| `message_31` | `employer` | `request_43` | `` | `2024-09-05T09:30:00Z` | other |
| `message_32` | `employer` | `` | `` | `2025-01-30T09:30:00Z` | confirmation |
| `message_33` | `employer` | `request_45` | `` | `2026-07-01T09:30:00Z` | amendment |
| `message_34` | `service_provider` | `` | `` | `2025-05-04T09:30:00Z` | delay |
| `message_35` | `service_provider` | `request_48` | `event_4535` | `2026-07-24T09:30:00Z` | other |
| `message_36` | `employer` | `request_49` | `` | `2024-02-21T09:30:00Z` | other |
| `message_37` | `employer` | `` | `` | `2025-08-05T09:30:00Z` | amendment, confirmation |
| `message_38` | `employer` | `` | `` | `2024-06-04T09:30:00Z` | amendment, confirmation |
| `message_39` | `merchant` | `request_53` | `event_4994` | `2025-10-28T09:30:00Z` | amendment, delay, settlement, refund |
| `message_40` | `employer` | `request_54` | `` | `2026-07-03T09:30:00Z` | amendment |
| `message_41` | `bank` | `request_57` | `` | `2026-03-25T09:30:00Z` | amendment |
| `message_42` | `employer` | `request_58` | `` | `2024-11-29T09:30:00Z` | other |
| `message_43` | `service_provider` | `` | `` | `2025-04-22T09:30:00Z` | amendment, delay, settlement |
| `message_44` | `employer` | `request_60` | `` | `2025-12-26T09:30:00Z` | amendment, settlement, confirmation |
| `message_45` | `employer` | `request_61` | `` | `2024-02-28T09:30:00Z` | amendment, settlement, confirmation |
| `message_46` | `service_provider` | `` | `` | `2025-08-04T09:30:00Z` | settlement, confirmation |
| `message_47` | `merchant` | `request_64` | `` | `2024-05-29T09:30:00Z` | amendment, delay, refund |
| `message_48` | `employer` | `` | `` | `2025-11-02T09:30:00Z` | amendment, settlement, confirmation |
| `message_49` | `service_provider` | `request_66` | `` | `2026-03-29T09:30:00Z` | settlement, confirmation |
| `message_50` | `employer` | `` | `` | `2025-01-31T09:30:00Z` | amendment, confirmation |
| `message_51` | `service_provider` | `` | `` | `2025-12-30T09:30:00Z` | amendment |
| `message_52` | `financial_service` | `request_70` | `event_6532` | `2024-12-02T09:30:00Z` | amendment, non_cash |
| `message_53` | `employer` | `request_71` | `` | `2025-04-23T09:30:00Z` | other |
| `message_54` | `employer` | `request_72` | `` | `2026-06-24T09:30:00Z` | confirmation |
| `message_55` | `service_provider` | `` | `` | `2023-01-19T09:30:00Z` | amendment |
| `message_56` | `service_provider` | `` | `` | `2025-07-23T09:30:00Z` | amendment, settlement, confirmation |
| `message_57` | `employer` | `request_75` | `` | `2026-04-04T09:30:00Z` | amendment, confirmation |
| `message_58` | `employer` | `request_76` | `` | `2024-05-31T09:30:00Z` | delay, confirmation |
| `message_59` | `merchant` | `request_77` | `event_7186` | `2025-11-04T09:30:00Z` | amendment, delay, settlement, refund |
| `message_60` | `employer` | `request_80` | `` | `2025-01-26T09:30:00Z` | delay, confirmation |
| `message_61` | `service_provider` | `request_81` | `` | `2026-06-29T09:30:00Z` | amendment |
| `message_62` | `employer` | `request_82` | `` | `2024-11-26T09:30:00Z` | other |
| `message_63` | `employer` | `` | `` | `2025-04-27T09:30:00Z` | amendment |
| `message_64` | `merchant` | `request_84` | `event_7941` | `2026-04-03T09:30:00Z` | settlement, confirmation |
| `message_65` | `employer` | `` | `` | `2024-02-27T09:30:00Z` | other |
| `message_66` | `employer` | `request_87` | `` | `2026-01-01T09:30:00Z` | amendment |
| `message_67` | `financial_service` | `` | `` | `2024-05-31T09:30:00Z` | other |
| `message_68` | `service_provider` | `request_90` | `` | `2026-06-28T09:30:00Z` | settlement, confirmation |
| `message_69` | `bank` | `request_91` | `event_8575` | `2024-08-26T09:30:00Z` | other |
| `message_70` | `employer` | `` | `` | `2025-01-29T09:30:00Z` | amendment, delay, confirmation |
| `message_71` | `financial_service` | `request_93` | `` | `2026-03-30T09:30:00Z` | settlement, confirmation |
| `message_72` | `service_provider` | `` | `` | `2024-11-28T09:30:00Z` | settlement, confirmation |
| `message_73` | `employer` | `` | `` | `2025-04-30T09:30:00Z` | amendment, confirmation |
| `message_74` | `employer` | `request_98` | `` | `2025-08-06T09:30:00Z` | amendment, confirmation |
| `message_75` | `financial_service` | `request_101` | `event_9420` | `2025-10-23T09:30:00Z` | settlement, confirmation |
| `message_76` | `service_provider` | `` | `` | `2026-03-27T09:30:00Z` | amendment, settlement, confirmation |
| `message_77` | `employer` | `` | `` | `2024-09-05T09:30:00Z` | amendment, confirmation |
| `message_78` | `employer` | `` | `` | `2025-01-28T09:30:00Z` | amendment, delay, confirmation |
| `message_79` | `financial_service` | `request_105` | `event_9805` | `2026-05-27T09:30:00Z` | amendment, non_cash |
| `message_80` | `employer` | `` | `` | `2024-11-24T09:30:00Z` | amendment, confirmation |
| `message_81` | `employer` | `` | `` | `2025-05-01T09:30:00Z` | amendment, settlement, confirmation |
| `message_82` | `employer` | `` | `` | `2026-06-28T09:30:00Z` | amendment, delay, confirmation |
| `message_83` | `service_provider` | `` | `` | `2025-08-05T09:30:00Z` | amendment, settlement, confirmation |
| `message_84` | `employer` | `` | `` | `2026-04-01T09:30:00Z` | other |
| `message_85` | `employer` | `request_112` | `` | `2024-06-02T09:30:00Z` | confirmation |
| `message_86` | `financial_service` | `request_113` | `event_10521` | `2026-09-03T01:00:00Z` | amendment, confirmation |
| `message_87` | `employer` | `request_114` | `` | `2025-12-30T09:30:00Z` | amendment, settlement, confirmation |
| `message_88` | `financial_service` | `request_115` | `event_10699` | `2024-08-31T09:30:00Z` | amendment, settlement, confirmation |
| `message_89` | `employer` | `request_117` | `` | `2026-06-23T09:30:00Z` | amendment |
| `message_90` | `employer` | `request_118` | `` | `2024-11-28T09:30:00Z` | other |
| `message_91` | `employer` | `request_119` | `` | `2025-04-27T09:30:00Z` | amendment |
| `message_92` | `financial_service` | `request_120` | `event_11129` | `2026-03-26T09:30:00Z` | delay |
| `message_93` | `service_provider` | `request_122` | `` | `2025-07-24T09:30:00Z` | other |
| `message_94` | `service_provider` | `` | `` | `2026-01-06T09:30:00Z` | delay |
| `message_95` | `employer` | `request_125` | `` | `2025-10-26T09:30:00Z` | amendment, confirmation |
| `message_96` | `service_provider` | `request_126` | `` | `2026-06-28T09:30:00Z` | settlement, confirmation |
| `message_97` | `employer` | `request_127` | `` | `2024-08-29T09:30:00Z` | amendment |
| `message_98` | `employer` | `` | `` | `2025-01-26T09:30:00Z` | amendment, settlement, confirmation |
| `message_99` | `financial_service` | `request_129` | `event_11925` | `2026-03-29T09:30:00Z` | settlement, confirmation |
| `message_100` | `employer` | `request_130` | `` | `2024-11-26T09:30:00Z` | amendment, confirmation |
| `message_101` | `employer` | `` | `` | `2025-04-23T09:30:00Z` | amendment, confirmation |
| `message_102` | `employer` | `` | `` | `2025-12-24T09:30:00Z` | amendment, settlement, confirmation |
| `message_103` | `employer` | `` | `` | `2024-03-06T09:30:00Z` | other |
| `message_104` | `employer` | `request_135` | `` | `2026-06-25T09:30:00Z` | amendment |
| `message_105` | `service_provider` | `` | `` | `2025-10-29T09:30:00Z` | amendment |
| `message_106` | `bank` | `` | `event_12709` | `2026-04-05T09:30:00Z` | amendment, cancellation, refund |
| `message_107` | `employer` | `` | `` | `2025-01-30T09:30:00Z` | confirmation |
| `message_108` | `financial_service` | `request_141` | `event_13032` | `2025-12-29T09:30:00Z` | amendment, delay, settlement, non_cash |
| `message_109` | `service_provider` | `request_142` | `` | `2024-12-04T09:30:00Z` | settlement, confirmation |
| `message_110` | `financial_service` | `` | `event_13207` | `2025-05-04T09:30:00Z` | amendment, settlement, confirmation |
| `message_111` | `employer` | `request_144` | `` | `2026-06-22T09:30:00Z` | amendment, confirmation |
| `message_112` | `employer` | `` | `` | `2024-02-29T09:30:00Z` | other |
| `message_113` | `employer` | `request_147` | `` | `2026-04-03T09:30:00Z` | amendment |
| `message_114` | `financial_service` | `request_148` | `event_13663` | `2024-06-03T09:30:00Z` | delay, settlement, non_cash |
| `message_115` | `employer` | `request_150` | `` | `2026-01-01T09:30:00Z` | amendment, settlement, confirmation |
| `message_116` | `employer` | `request_151` | `` | `2024-08-30T09:30:00Z` | other |
| `message_117` | `employer` | `` | `event_14026` | `2025-02-01T09:30:00Z` | amendment, refund, confirmation |
| `message_118` | `merchant` | `` | `` | `2026-07-01T09:30:00Z` | amendment, confirmation |
| `message_119` | `employer` | `request_154` | `` | `2024-11-25T09:30:00Z` | amendment, confirmation |
| `message_120` | `employer` | `` | `` | `2025-04-28T09:30:00Z` | amendment |
| `message_121` | `bank` | `` | `event_14399` | `2026-04-01T09:30:00Z` | cancellation, refund |
| `message_122` | `employer` | `request_157` | `` | `2024-02-29T09:30:00Z` | other |
| `message_123` | `service_provider` | `` | `` | `2025-12-25T09:30:00Z` | amendment, delay, settlement |
| `message_124` | `employer` | `` | `` | `2024-06-01T09:30:00Z` | amendment, confirmation |
| `message_125` | `employer` | `` | `` | `2025-10-24T09:30:00Z` | other |
| `message_126` | `employer` | `` | `` | `2026-07-04T09:30:00Z` | amendment |
| `message_127` | `employer` | `` | `` | `2024-09-02T09:30:00Z` | other |
| `message_128` | `employer` | `request_164` | `` | `2025-02-01T09:30:00Z` | other |
| `message_129` | `employer` | `request_165` | `` | `2026-04-03T09:30:00Z` | amendment, confirmation |
| `message_130` | `service_provider` | `request_166` | `` | `2024-12-02T09:30:00Z` | amendment, settlement, confirmation |
| `message_131` | `employer` | `request_167` | `` | `2025-04-30T09:30:00Z` | amendment, confirmation |
| `message_132` | `employer` | `request_168` | `` | `2026-01-04T09:30:00Z` | amendment, settlement, confirmation |
| `message_133` | `merchant` | `` | `` | `2024-02-26T09:30:00Z` | amendment, delay, refund |
| `message_134` | `financial_service` | `` | `` | `2025-08-02T09:30:00Z` | other |
| `message_135` | `bank` | `request_171` | `` | `2026-07-01T09:30:00Z` | other |
| `message_136` | `bank` | `request_172` | `` | `2024-05-28T09:30:00Z` | other |
| `message_137` | `employer` | `` | `` | `2025-11-03T09:30:00Z` | confirmation |
| `message_138` | `employer` | `` | `` | `2024-09-01T09:30:00Z` | amendment, confirmation |
| `message_139` | `employer` | `request_176` | `` | `2025-01-31T09:30:00Z` | delay, confirmation |
| `message_140` | `employer` | `request_177` | `` | `2025-12-24T09:30:00Z` | amendment, settlement, confirmation |
| `message_141` | `service_provider` | `request_178` | `` | `2024-12-04T09:30:00Z` | amendment, settlement, confirmation |
| `message_142` | `financial_service` | `` | `` | `2025-04-30T09:30:00Z` | other |
| `message_143` | `employer` | `` | `` | `2026-06-29T09:30:00Z` | confirmation |
| `message_144` | `employer` | `` | `` | `2025-08-04T09:30:00Z` | amendment, settlement, confirmation |
| `message_145` | `merchant` | `request_183` | `` | `2026-04-03T09:30:00Z` | other |
| `message_146` | `merchant` | `` | `` | `2024-06-01T09:30:00Z` | amendment, delay, refund |
| `message_147` | `service_provider` | `request_185` | `` | `2025-10-30T09:30:00Z` | other |
| `message_148` | `employer` | `request_186` | `` | `2025-12-29T09:30:00Z` | amendment, settlement, confirmation |
| `message_149` | `employer` | `request_187` | `` | `2024-08-30T09:30:00Z` | confirmation |
| `message_150` | `employer` | `request_188` | `event_17401` | `2025-01-30T09:30:00Z` | amendment, refund, confirmation |
| `message_151` | `employer` | `` | `` | `2026-07-02T09:30:00Z` | amendment |
| `message_152` | `merchant` | `request_191` | `event_17662` | `2025-04-23T09:30:00Z` | amendment, delay, settlement, refund |
| `message_153` | `employer` | `request_193` | `` | `2024-03-05T09:30:00Z` | amendment, confirmation |
| `message_154` | `employer` | `request_194` | `` | `2025-07-27T09:30:00Z` | amendment, confirmation |
| `message_155` | `employer` | `request_195` | `` | `2026-01-04T09:30:00Z` | amendment, settlement, confirmation |
| `message_156` | `employer` | `` | `` | `2025-10-25T09:30:00Z` | other |
| `message_157` | `bank` | `request_198` | `event_18269` | `2026-06-28T09:30:00Z` | amendment, cancellation, refund |
| `message_158` | `service_provider` | `request_199` | `` | `2024-08-24T09:30:00Z` | delay |
| `message_159` | `employer` | `request_200` | `` | `2025-02-01T09:30:00Z` | other |
| `message_160` | `employer` | `request_201` | `` | `2026-03-26T09:30:00Z` | other |
| `message_161` | `bank` | `request_202` | `` | `2024-11-26T09:30:00Z` | other |
| `message_162` | `employer` | `` | `` | `2025-12-24T09:30:00Z` | amendment, confirmation |
| `message_163` | `financial_service` | `` | `event_19182` | `2024-06-01T09:30:00Z` | amendment |
| `message_164` | `bank` | `request_210` | `event_19334` | `2026-04-01T09:30:00Z` | cancellation, refund |
| `message_165` | `employer` | `request_212` | `` | `2025-02-04T09:30:00Z` | other |
| `message_166` | `employer` | `request_213` | `` | `2025-12-30T09:30:00Z` | amendment, settlement, confirmation |
| `message_167` | `merchant` | `request_214` | `` | `2024-11-25T09:30:00Z` | amendment, delay, refund |
| `message_168` | `service_provider` | `request_215` | `` | `2025-05-05T09:30:00Z` | amendment, delay, settlement |
| `message_169` | `employer` | `` | `` | `2026-06-28T09:30:00Z` | amendment |
| `message_170` | `employer` | `request_219` | `` | `2026-04-01T09:30:00Z` | amendment |
| `message_171` | `employer` | `` | `` | `2024-06-04T09:30:00Z` | amendment, confirmation |
| `message_172` | `merchant` | `request_221` | `event_20379` | `2025-10-29T09:30:00Z` | amendment, delay, settlement, refund |
| `message_173` | `service_provider` | `request_222` | `` | `2025-12-27T09:30:00Z` | amendment, settlement, confirmation |
| `message_174` | `employer` | `` | `event_20615` | `2025-01-23T09:30:00Z` | other |
| `message_175` | `service_provider` | `request_225` | `` | `2026-06-28T09:30:00Z` | other |
| `message_176` | `employer` | `` | `` | `2024-11-25T09:30:00Z` | amendment |
| `message_177` | `employer` | `` | `` | `2025-04-25T09:30:00Z` | amendment, settlement, confirmation |
| `message_178` | `employer` | `` | `` | `2026-04-04T09:30:00Z` | other |
| `message_179` | `bank` | `` | `event_21101` | `2024-02-25T09:30:00Z` | other |
| `message_180` | `employer` | `` | `` | `2025-08-05T09:30:00Z` | amendment, confirmation |
| `message_181` | `employer` | `` | `` | `2024-05-26T09:30:00Z` | confirmation |
| `message_182` | `employer` | `` | `` | `2025-11-03T09:30:00Z` | other |
| `message_183` | `bank` | `request_234` | `event_21582` | `2026-06-27T09:30:00Z` | cancellation, refund |
| `message_184` | `merchant` | `request_235` | `` | `2024-08-30T09:30:00Z` | amendment, delay, refund |
| `message_185` | `financial_service` | `` | `event_21785` | `2025-01-27T09:30:00Z` | amendment |
| `message_186` | `employer` | `request_237` | `` | `2026-03-26T09:30:00Z` | other |
| `message_187` | `employer` | `request_238` | `` | `2024-11-26T09:30:00Z` | amendment, confirmation |
| `message_188` | `employer` | `request_240` | `` | `2025-12-26T09:30:00Z` | amendment, confirmation |
| `message_189` | `employer` | `request_241` | `` | `2024-02-29T09:30:00Z` | other |
| `message_190` | `employer` | `` | `` | `2025-08-01T09:30:00Z` | settlement, confirmation |
| `message_191` | `employer` | `` | `` | `2025-10-28T09:30:00Z` | amendment, confirmation |
| `message_192` | `employer` | `request_246` | `` | `2026-03-24T09:30:00Z` | amendment, confirmation |
| `message_193` | `employer` | `request_247` | `` | `2024-08-30T09:30:00Z` | amendment, confirmation |
| `message_194` | `employer` | `` | `` | `2025-02-02T09:30:00Z` | amendment, delay, confirmation |
| `message_195` | `employer` | `request_249` | `` | `2025-12-27T09:30:00Z` | amendment, settlement, confirmation |
| `message_196` | `employer` | `` | `` | `2024-12-01T09:30:00Z` | confirmation |
| `message_197` | `bank` | `request_252` | `event_23203` | `2026-06-24T09:30:00Z` | other |
| `message_198` | `bank` | `request_253` | `event_23306` | `2024-03-06T09:30:00Z` | other |
| `message_199` | `employer` | `` | `` | `2025-07-29T09:30:00Z` | amendment, settlement, confirmation |
| `message_200` | `employer` | `request_256` | `` | `2024-06-01T09:30:00Z` | confirmation |
| `message_201` | `bank` | `request_259` | `event_23855` | `2024-08-29T09:30:00Z` | other |
| `message_202` | `bank` | `request_261` | `` | `2026-06-25T09:30:00Z` | other |
| `message_203` | `employer` | `request_262` | `` | `2024-11-23T09:30:00Z` | other |
| `message_204` | `employer` | `` | `` | `2025-04-28T09:30:00Z` | amendment, confirmation |
| `message_205` | `financial_service` | `request_264` | `event_24352` | `2026-04-01T09:30:00Z` | amendment, non_cash |
| `message_206` | `employer` | `` | `` | `2024-02-28T09:30:00Z` | amendment, settlement, confirmation |
| `message_207` | `financial_service` | `request_266` | `event_24534` | `2025-07-28T09:30:00Z` | amendment, non_cash |
| `message_208` | `merchant` | `request_267` | `` | `2026-01-03T09:30:00Z` | confirmation |
| `message_209` | `financial_service` | `` | `` | `2024-06-04T09:30:00Z` | settlement, confirmation |
| `message_210` | `employer` | `request_269` | `` | `2025-10-31T09:30:00Z` | amendment, settlement, confirmation |
| `message_211` | `employer` | `request_271` | `` | `2024-08-26T09:30:00Z` | other |
| `message_212` | `employer` | `request_272` | `` | `2025-02-02T09:30:00Z` | other |
| `message_213` | `bank` | `request_273` | `` | `2026-03-30T09:30:00Z` | other |
| `message_214` | `merchant` | `request_274` | `` | `2024-11-24T09:30:00Z` | amendment, delay, refund |
| `message_215` | `merchant` | `request_275` | `event_25342` | `2025-04-24T09:30:00Z` | other |

## Complete image inventory

The current map values are manual reference fixtures, not AI extraction results. Image semantic roles must be extracted and validated before replacing them.

| Image | User | Request | Linked event | Current manual reference | File |
|---|---|---|---|---:|---|
| `image_01` | `user_03` | `request_03` | `event_253` | `4365000` | `dataset/media/images/image_01.png` |
| `image_02` | `user_16` | `request_16` | `event_1442` | `100000` | `dataset/media/images/image_02.png` |
| `image_03` | `user_17` | `request_17` | `event_1545` | `41272` | `dataset/media/images/image_03.png` |
| `image_04` | `user_19` | `request_19` | `event_1700` | `2854` | `dataset/media/images/image_04.png` |
| `image_05` | `user_20` | `request_20` | `event_1786` | `704.05` | `dataset/media/images/image_05.png` |
| `image_06` | `user_33` | `request_33` | `event_3051` | `79679.26` | `dataset/media/images/image_06.png` |
| `image_07` | `user_35` | `request_35` | `event_3231` | `8528.10` | `dataset/media/images/image_07.png` |
| `image_08` | `user_48` | `request_48` | `event_4535` | `15339` | `dataset/media/images/image_08.png` |
| `image_09` | `user_55` | `request_55` | `event_5170` | `723` | `dataset/media/images/image_09.png` |
| `image_10` | `user_64` | `request_64` | `event_6033` | `79679.26` | `dataset/media/images/image_10.png` |
| `image_11` | `user_73` | `request_73` | `event_6859` | `3650` | `dataset/media/images/image_11.png` |
| `image_12` | `user_78` | `request_78` | `event_7307` | `33.50` | `dataset/media/images/image_12.png` |
| `image_13` | `user_84` | `request_84` | `event_7941` | `2298` | `dataset/media/images/image_13.png` |
| `image_14` | `user_101` | `request_101` | `event_9421` | `4593` | `dataset/media/images/image_14.png` |
| `image_15` | `user_105` | `request_105` | `event_9806` | `9968` | `dataset/media/images/image_15.png` |
| `image_16` | `user_113` | `request_113` | `event_10521` | `393.22` | `dataset/media/images/image_16.png` |

## First message fixture

The first supported category is explicit transaction-status evidence, beginning with delayed refunds. `message_14` is linked to `request_20` and `event_1785`; it says the refund was initiated but has not reached the account. It supplies no amount or settlement date. The deterministic engine already excludes the pending credit, but the current message parser ignores this supporting evidence entirely.

Expected validated shape for a future provider response:

```json
{
  "source_id": "message_14",
  "source_kind": "message",
  "supplied_user_id": "user_20",
  "supplied_request_id": "request_20",
  "supplied_event_id": "event_1785",
  "action": "delay",
  "amount": null,
  "currency": null,
  "dates": [],
  "recurrence_scope": "once",
  "supporting_text": "The refund has been initiated but has not reached the account yet.",
  "missing_fields": ["amount", "settlement_date"],
  "ambiguities": ["The message does not state when the refund will settle."],
  "conflicts": []
}
```

No financial application is performed for this fixture until a model response is available and passes deterministic validation, request-date visibility, conflict precedence, and duplicate-source checks.

## Extraction interface

`code/evidence_extraction.py` provides:

- strict `EvidenceFact` validation for source IDs, supplied user/request/event references, actions, non-negative amounts, ISO dates, currencies, recurrence scope, supporting text, and explicit missing/ambiguous/conflicting fields;
- `EvidenceSource` content hashing and an untrusted-evidence prompt wrapper;
- cache keys incorporating source content, model name, prompt version, and schema version;
- `JsonExtractionCache` and `ExtractionOutcome` fields for cache reuse, model name, token counts, retries, and estimated cost;
- `UnavailableModelProvider` as an explicit blocker;
- `EvidenceLedger` to reject duplicate application if deterministic and model paths converge on the same source fact.

The existing deterministic payroll parser remains in `code/main.py` for comparison. It is not invoked by this interface, and no model facts are applied to `Agent` in this iteration.

## Next integration gate

Configure a supported model credential and SDK through environment variables, then add one provider adapter for `message_14`-style delayed refunds. The adapter must return the schema above, be cached, validate against supplied links, and be measured separately from downstream affordability results before any financial application is enabled.
