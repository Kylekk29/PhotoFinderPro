# 03 Licensing, tech route, accuracy, mobile (researcher agent report, 2026-10-18)

Not legal advice. [COUNSEL] = needs a qualified lawyer. "Verified" = CEO re-fetched the source on 2026-10-18. Everything else is the agent's claim with its URL; "NOT FOUND" = not retrieved.

## Headline findings
1. **pillow-heif binary wheels are not closed-source distributable as-is. VERIFIED.** [LICENSES_bundled.txt](https://raw.githubusercontent.com/bigcat88/pillow_heif/master/LICENSES_bundled.txt) lists x265 as GPLv2 and libheif/libde265 as LGPLv3; wheels as a whole GPLv2. Options: `pi-heif` decode-only (PyPI says BSD-3 licence but LGPLv3 classifier; bundled contents NOT verified), self-built decode-only libheif+libde265 as plugins/DLLs, or OS decoders (WIC+HEVC extension, macOS ImageIO). HEVC patent exposure: [COUNSEL].
2. **insightface pretrained models are non-commercial. VERIFIED** ("ALL models are available for non-commercial research purposes only", [model_zoo](https://github.com/deepinsight/insightface/tree/master/model_zoo)). Agent: README (2025-11-24) points commercial users of buffalo_l to a contact email; price NOT FOUND. Do not use buffalo_l / SCRFD / antelopev2 / ArcFace zoo models.
3. EdgeFace weights CC BY-NC-SA 4.0 ([HF](https://huggingface.co/Idiap/EdgeFace-Base)); yolov5-face GPL-3.0; dlib 68-landmark model non-commercial; FFHQ non-commercial and not for face-recognition development.
4. **Current stack licences are clean on paper. VERIFIED for two:** SFace ONNX files Apache-2.0 ([LICENSE](https://raw.githubusercontent.com/opencv/opencv_zoo/main/models/face_recognition_sface/LICENSE)); YuNet MIT, (c) 2020 Shiqi Yu ([LICENSE](https://raw.githubusercontent.com/opencv/opencv_zoo/main/models/face_detection_yunet/LICENSE)). OpenCV Apache-2.0 (agent).
5. **Unresolved core risk: SFace training-data provenance.** Paper says CASIA-WebFace, VGGFace2, MS-Celeb-1M ([arXiv 2205.12010](https://arxiv.org/abs/2205.12010)); original repo states no licence. Whether weights inherit dataset restrictions: no source either way. [COUNSEL]. Same for AdaFace/MagFace weights.
6. **No benchmark dataset checked is clearly commercially usable** (details below).

## Licence table (agent; ! = verified by CEO)
| Component | Licence | Closed-source commercial? | Obligations |
|---|---|---|---|
| OpenCV 4.x | Apache-2.0 | Yes | licence + NOTICE |
| YuNet ! | MIT | Yes | keep notice |
| libfacedetection | 3-clause BSD | Yes | keep notice |
| SFace files ! | Apache-2.0 | Files yes; data provenance [COUNSEL] | notice |
| numpy | BSD-3 (wheels carry extra third-party licences, not read) | Yes | notice |
| Pillow | MIT-CMU | Yes | notice |
| pillow-heif wheels ! | BSD-3 own code; wheels bundle x265 GPLv2, libheif/libde265 LGPLv3 | **No as shipped** | see headline 1 |
| pi-heif 1.4.0 | licence field BSD-3, classifier LGPLv3 (conflict) | Probably; verify wheel contents | verify no x265 |
| libheif / libde265 | LGPL | Yes if dynamically linked / plugin | relink ability, licence text |
| HEVC patents | Access Advance pool etc. | Unknown [COUNSEL] | OS decoder or licence |
| SQLite | public domain | Yes | none |
| PySide6 6.12.0 | LGPL-3.0 OR GPL | Yes under LGPL | dynamic link, relink, notice ([Qt](https://www.qt.io/development/open-source-lgpl-obligations)) |
| PyQt6 | not verified (commonly GPL/commercial) | commercial licence likely needed | - |
| PyInstaller | GPL-2.0+ with bootloader exception | Yes for bundled apps | do not modify PyInstaller |
| Nuitka | AGPL-3.0 + runtime exception | Likely; exception text not read [COUNSEL] | verify |
| Tauri | MIT/CC-BY | Yes | - |
| ONNX Runtime | MIT | Yes | notice |
| MediaPipe | Apache-2.0 | Yes (BlazeFace is short-range, weak for small faces) | - |
| NCNN | BSD-3 | Yes | - |
| Apple Vision | OS API | detection/quality only; **no face embedding API** | - |
| Google ML Kit face | detects only, "does not recognize people" | detection only | terms not read |
| Luxand FaceSDK | proprietary, quote only | by purchase | price NOT FOUND |

## Models (agent-sourced)
- Candidates with commercial-OK code and weights stated: YuNet (WIDER FACE AP E/M/H 0.887/0.871/0.768), SFace (opencv_zoo eval 0.9940, dataset unnamed). Weights licence not stated: AdaFace (IJB-C TAR@FAR1e-4 up to 97.66; trained on MS1MV2/WebFace etc.), MagFace, RetinaFace. dlib ResNet face model CC0 but trained on scraped data [COUNSEL].
- Not usable commercially: insightface zoo, EdgeFace weights, yolov5-face (GPL-3.0).
- No sourced per-face-size, profile, or YuNet/SFace cross-age numbers. Embedding models drop on CPLFW/CALFW vs LFW (EdgeFace-base 99.83 -> 93.75/96.07).
- Lower-risk paths: buy a commercial SDK or the insightface commercial licence, or train an embedding on licensed/consented data (expensive).

## Desktop routes
| Route | Pros | Cons |
|---|---|---|
| **Python + PySide6 + PyInstaller (recommended)** | reuses prototype; fastest; LGPL workable | large bundle, AV false positives, weak anti-reverse-engineering |
| Python + Nuitka | harder to extract | AGPL tool + exception [COUNSEL], paid tier |
| Electron | mature update ecosystem | big bundle (not verified) |
| Tauri + sidecar | small shell | two runtimes |
| Qt C++ | performance, licensing control | slow dev; commercial Qt price NOT FOUND |
| .NET / Flutter desktop | not researched | - |

Distribution: Windows EV certificates no longer bypass SmartScreen (Microsoft docs 2026); Microsoft recommends Artifact Signing ("starts at $9.99/month", needs Azure subscription) and the Store avoids SmartScreen warnings ([MS](https://learn.microsoft.com/en-us/windows/apps/package-and-deploy/smartscreen-reputation)). Microsoft Store fees second-hand only. macOS: Apple Developer Program $99/yr incl. Developer ID + notarization. Payments: Paddle 5%+$0.50 (merchant of record), Lemon Squeezy 5%+$0.50 with licence keys, Stripe 2.9%+$0.30 not MoR (secondary). Auto-update, offline activation, Gumroad: NOT RESEARCHED. Offline signed keys are standard; determined piracy not preventable (inference).

## Mobile feasibility (agent; verdict = inference)
- iOS: `BGProcessingTask` runs minutes with limits; iOS 26 adds `BGContinuedProcessingTask` (foreground start, Live Activity, can be terminated). iCloud-only assets need network download (`isNetworkAccessAllowed`). Vision has no embedding API, so a model must be shipped (ncnn/ONNX/Core ML conversion not verified).
- Android: Android 14 partial photo access + photo picker; Play allows `READ_MEDIA_IMAGES` only when the picker cannot deliver the core function (declaration required). From Android 15 `dataSync`/`mediaProcessing` foreground services capped at 6 h/24 h.
- Fees: Apple Small Business 15% (<$1M), Google 15% first $1M then 30%.
- NOT FOUND: battery/speed benchmarks for 10k-100k photos; copy-out semantics, Live Photos/RAW/video, store face-data policy review.
- **Verdict: desktop first, mobile companion later** (few clean models; background caps hurt large-library scans; Google permission review risk). A phone version works best as a foreground scan of selected albums.

## Accuracy roadmap (agent proposal, inference)
Versioned scan status (detector id/version/scale, re-run "no face" when a new detector ships); multi-scale + overlapped tiling; crop/upscale small faces; second detector for profiles + quality/pose rejection; video frame sampling + tracking; multi-reference, age-bucket centroids, per-person thresholds, review tier; metrics TAR@FAR 1e-3/1e-4, recall at fixed precision per tier, per-age-gap and per-face-size breakdown, no-face rate, latency. GPU: ONNX Runtime DirectML is in maintenance mode, WinML recommended; CUDA/CoreML EPs not checked.

## Dataset terms
| Dataset | Terms | Commercial |
|---|---|---|
| LFW, CALFW/CPLFW, WIDER FACE | NOT FOUND | unknown |
| AgeDB | non-commercial research only | no |
| IJB-C | NIST, CC variants, exact variant NOT FOUND; MagFace says apply to NIST | unknown |
| FFHQ | CC BY-NC-SA; not for FR development | no |
| UTKFace, CelebA | non-commercial research only | no |
| FairFace | CC BY 4.0 per page; image provenance unchecked | likely for labels |
| VGGFace2 | no licence on repo, scraped images | unknown |
| MS-Celeb-1M | withdrawn by Microsoft | do not use |
| WebFace260M, Glint360K, CASIA-WebFace | NOT FOUND | unknown |
Measurement plan (inference): consented in-house/volunteer set (written consent; NOT the owner's personal photos) + synthetic degradation (downscale tiers, blur, JPEG, crop, rotate, pose). Counsel should review any internal evaluation use of non-commercial datasets.

## Uncertain
pi-heif bundled contents; which pillow-heif wheels include x265 per platform; HEVC patent exposure; SFace/AdaFace/MagFace weight taint; Nuitka exception; Apple `.limited` behaviour page (empty); Qt commercial, Luxand, Gumroad, auto-update, offline activation prices/designs; per-size/profile numbers for YuNet/SFace; Microsoft Store fees; dataset terms listed NOT FOUND.
