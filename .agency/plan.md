# PhotoFinderPro plan (phase 1 output, DRAFT for sign-off)

Date: 2026-10-18. Status: research done; **no code written; awaiting user sign-off**. Research files: `docs/research/01_market.md`, `02_legal.md`, `03_licensing_tech_mobile.md`. Prototype `F:\Kyle\Coding\PhotoFinder` is reference only and must not be modified.

## 1. Goal
Turn the PhotoFinder prototype into a paid, local-first desktop app that finds all photos of one person from reference photos and copies matches out, never touching originals.

## 2. Hard rules (from the user)
No personal photos for dev/test (synthetic or lawfully licensed/consented data only); no commit/push/publish/deploy/paid sign-up/outbound sending without explicit approval; no secrets in files; no market/legal/price claim without a source; every phase reported honestly and signed off before the next; do not read or create anything on D:.

## 3. Honest commercial assessment
- Demand evidence is weak (one memorial forum request found; no volume data). Free tools (digiKam, Immich, PhotoPrism) group faces; none found with "give a reference photo, get everything" except possibly Events (unverified). Value is probably a niche utility, price plausibly $20-60 one-off (inference, not researched).
- Selling points:
  - *Privacy-first local*: true but table stakes (ACDSee, Excire, digiKam etc. also local). Not a moat. It IS the legal anchor: the BIPA rulings turned on the vendor having no access to the data.
  - *Non-destructive copy-only*: partly supported (tests on synthetic files; real-photo hash/mtime verification not yet done). A trust feature, easy to copy.
  - *Recall-first single-person extraction*: the real differentiator; memorial use is sensitive and probably often a one-off job.
- **Gate G0 (before heavy build):** validate demand and the gap cheaply: try Events/Tonfotos/ACDSee for reference-photo search; talk to 5-10 target users (interviews need user approval, outward-facing).

## 4. Blocking risks to resolve before charging money
1. **Model provenance**: SFace weights are Apache-2.0 but trained on CASIA-WebFace/VGGFace2/MS-Celeb-1M; taint unresolved [COUNSEL]. Fallbacks: commercial SDK/licence, own training on licensed data.
2. **HEIC**: current pillow-heif wheels bundle GPL x265. Replace with decode-only path or OS decoders; HEVC patents [COUNSEL].
3. **Legal**: GDPR Recital 18 (vendor as provider of means), HK vendor status, BIPA beyond the 7th Circuit, app-store review. Lawyer consultation needed (questions in 02_legal.md).
4. **Evaluation data**: nearly every benchmark is non-commercial/unknown. Need a consented volunteer set + synthetic degradation.
5. Accuracy limits: 33% no-face rate, small faces, cross-age; unproven on real use.

## 5. Recommended technical direction (inference from research)
- Desktop first (Windows), macOS second; phone later as a foreground companion or not at all.
- Python + PySide6 (LGPL, dynamic) + PyInstaller, reusing the prototype's logic; core separated from UI with a worker thread (fixes GUI freezing).
- Local SQLite with versioned scan status; per-user data dir instead of app folder; single-instance lock.
- Windows: Microsoft Store or Artifact Signing; macOS: Developer ID + notarization; payments via a merchant of record (Paddle/Lemon Squeezy); offline signed licence keys. No cloud features (any cloud feature = legal re-review).

## 6. Scope by stage
**G0 Validation (no code):** demand check, competitor trial, counsel questions sent (needs approval), model-licence decision. Exit: user decides go / no-go / pivot.
**MVP (Windows, free private beta, no sales):** core extracted from prototype and tested; HEIC path replaced; versioned scan status incl. re-check of no-face photos; background worker UI; single-instance lock; copy fix (naming); read-only/hash safety verified on synthetic files; evaluation harness with synthetic data. Not in MVP: video, macOS, payment, auto-update, mobile. Acceptance: all automated tests pass; originals' hash+mtime unchanged on synthetic and volunteer-consented sets; documented recall/precision per tier with per-size/age breakdowns; licence audit passed with open items listed; no network calls (verified).
**V1 (sellable Windows release):** installer, code signing, licence activation, privacy policy/ToS reviewed by counsel, multi-reference/age buckets, small-face tiling, face quality filter, memorial-sensitive wording, crash-safe reporting without images (opt-in). Acceptance: signed installer on clean Windows 11 VM, SmartScreen behaviour documented, counsel sign-off recorded, support docs.
**V2:** macOS, video (frame sampling + tracking), GPU acceleration, auto-update, optional mobile companion study.

## 7. Phase gates
Phase 1 (this): research + plan -> user sign-off. Phase 2: architecture + licence/model decision (after G0). Phase 3: MVP build. Phase 4: V1. Each: plan, approval, report (commands, results, untested, risks), sign-off.

## 8. Risk register (summary)
| Risk | Type | Severity | Mitigation |
|---|---|---|---|
| Weak demand / free competitors | market | High | G0 validation, niche positioning, low price |
| Model weights taint | legal/tech | High | counsel, commercial SDK, own model |
| GPL x265 in HEIC wheels | legal | High | pi-heif / OS decoders / own libheif build |
| HEVC patents | legal | Medium | OS decoders, counsel |
| GDPR vendor role / BIPA / HK | legal | Medium-High | counsel, no-cloud rule, no telemetry |
| Store review (Google photo permissions) | platform | Medium (phone only) | desktop first |
| Accuracy shortfall (no-face, small, cross-age) | technical | High | roadmap + measurement before claims |
| Misuse (stalking, strangers) | reputational/legal | High | own-library only, ToS, no web search |
| Memorial sensitivity / privacy backlash | reputation | Medium | careful copy, clear local-only proof |
| Support cost (AV false positives, SmartScreen, HEIC edge cases) | ops | Medium | Store distribution, docs |
| Piracy | revenue | Low-Medium | offline keys, accept leakage |
