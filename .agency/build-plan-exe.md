# Build plan: Windows .exe (simple version, DRAFT for approval)

Goal: a working Windows .exe of Photo Finder for private / trial use. Not sold yet (selling needs the HEIC and face-model licence items in plan.md section 4).
Stack: Python, PySide6 (UI), OpenCV YuNet + SFace (same models as the prototype), SQLite, PyInstaller. Reuse the prototype's logic; do not modify `F:\Kyle\Coding\PhotoFinder`.
Rules kept: no personal photos in tests, no commit/push/publish without approval, no secrets, nothing on D:.

## Steps (each step: I say what I will do, you approve, I report)
1. **Project setup**: new `app/` structure (core separate from UI), own venv, copy the two model files from the prototype (read-only copy), dependency list with licences.
2. **Core**: move scan / match / safe-copy logic over; fix known gaps: scan status stores detector version (so "no face" photos can be re-checked), duplicate-name copy fix, single-window lock, data folder outside the program folder.
3. **HEIC**: use a decode-only library (pi-heif) after checking the wheel does not contain GPL parts.
4. **Tests**: automated tests with synthetic images and fake face data; safety tests (originals never changed: hash and modified time). Real-face accuracy tests need consented photos, to be decided later.
5. **UI**: PySide6 window, scanning in a background thread so it never freezes; results grid with green face box; two tiers (confirmed / maybe).
6. **Package**: PyInstaller build to a folder + installer `.exe`; run on this PC; list licence notices.
7. **Report**: commands run, results, what was not tested.

Out of scope for now: video, macOS, phone, payment, licence keys, auto-update, code signing (Windows will show a SmartScreen warning for an unsigned .exe).
