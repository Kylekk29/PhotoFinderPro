# PhotoFinderPro task board

Updated 2026-10-18. Status: todo | doing | done | blocked. Nothing past phase 1 starts without user sign-off.

| id | task | owner | depends on | status | acceptance |
|---|---|---|---|---|---|
| P1-1 | Create project folder + .agency + docs/research | CEO | - | done | folders exist |
| P1-2 | Market + competitors research | researcher | P1-1 | done (draft, not fully spot-checked) | docs/research/01_market.md |
| P1-3 | Legal/compliance research | researcher | P1-1 | done (draft, partially spot-checked) | docs/research/02_legal.md |
| P1-4 | Licensing, tech, mobile, accuracy research | researcher | P1-1 | done (key claims verified) | docs/research/03_licensing_tech_mobile.md |
| P1-5 | Spot-check key sources | CEO | P1-2..4 | done for licences + Samsung case; market prices and most legal citations NOT re-checked | listed in report |
| P1-6 | Write plan.md + tasks.md | CEO | P1-5 | done | files exist |
| P1-7 | Phase 1 report + user sign-off | CEO | P1-6 | doing | user sign-off |
| G0-1 | Try Events, Tonfotos, ACDSee for reference-photo search (needs user OK for installs/purchases) | CEO/user | P1-7 | todo | written finding per product |
| G0-2 | 5-10 user interviews / community check (outward-facing, needs approval) | user | P1-7 | todo | notes + go/no-go |
| G0-3 | Send legal questions to counsel | user | P1-7 | todo | answers recorded |
| G0-4 | Decide face-model route (SFace as is / commercial SDK / own training) | user+CEO | G0-3 | todo | decision in decisions.md |
| P2-1 | Architecture doc (core/worker/UI split, data dir, versioned scan status) | architect | G0 go | todo | doc approved |
| P2-2 | HEIC decoder decision + licence audit | CEO | G0-3 | todo | audit table, no GPL in bundle |
| P2-3 | Evaluation plan: consented volunteer set + synthetic degradation | qa-engineer | G0 go | todo | protocol + consent form draft |
| P3-x | MVP build tasks | engineering-lead | P2 sign-off | blocked | see plan.md MVP |

## Build plan (.agency/build-plan-exe.md), approved 2026-10-18
| id | task | status | result |
|---|---|---|---|
| B1 | Project setup: folders, venv, models copied, deps | done | see report; pip check clean |
| B2 | Core (scan/match/safe-copy + fixes) | done | 19 tests pass |
| B3 | HEIC via pi-heif | done in code; HEIC decoding itself NOT tested (no sample file) | wheel has libheif + libde265 as separate DLLs, no x265; HEVC patents still [COUNSEL] |
| B4 | Tests (synthetic) | done | tests/ : safety, pipeline, engine smoke, UI smoke |
| B5 | PySide6 UI + worker thread | done (headless test + rendered screenshot; not hand-driven with real photos) | |
| B6 | PyInstaller + Setup.exe (models inside, offline installer) | deferred by user: "installer is later" | |
| B7 | Report | done 2026-10-18 | |

## Done after the MVP report (2026-10-18)
- Self-check + QA agent bug hunt: 16 bugs fixed with regression tests (tests/test_regressions.py, tests/test_qa_found.py).
- Searches (runs): own results folder, own references, history tab, filter; new search over scanned folders is filled without re-scan (tests/test_runs.py). 58 tests pass.
- UI redesign (2026-10-18): new `ui/` package (dark/light theme, step cards, accuracy presets, scan dashboard, toasts, drag and drop), Y/N review with an "excluded" tab, final export to `<search>inal\`, English UI (`i18n.EN`), thumbnail zoom. Portable zip rebuilt, selftest OK. 76 tests pass (tests/test_review.py, tests/test_i18n.py added).

## Backlog (not scheduled)
Video support; macOS; GPU; auto-update; phone companion study; bystander-face handling; localisation.
