# 01 Market and competitors (draft from researcher agent, 2026-10-18)

Status: **PARTIAL, not yet spot-checked by the CEO.** Evidence for competitors is decent; demand evidence is thin.
Legend: *fetched* = the agent read the page; *search-only* = seen only in a search summary, **verify before quoting**.
Not legal or investment advice. Anything marked NOT FOUND was not found, not "does not exist".

## Competitors

| Name | Price / licence (checked 2026-10-18) | Local/cloud | Search by reference photo? | Notes / weaknesses | Sources |
|---|---|---|---|---|---|
| digiKam | Free, open source | Local | No (tag a face, then run recognition) | Wrong confirmation causes many wrong suggestions; "search by similar face" wishlist filed 2016, closed as duplicate (2023) | [People View docs](https://docs.digikam.org/en/left_sidebar/people_view.html) fetched; [KDE bug 363724](https://bugs.kde.org/show_bug.cgi?id=363724) fetched |
| Excire Foto / Search | Perpetual. Foto 2025 cut to $129 (spring 2026); Foto 2027 planned $219-$249; Search 2026 $199 list. **Not verified on Excire's shop** | Local | NOT FOUND | - | [excire.com](https://www.excire.com/en/) fetched; [travishale.com](https://www.travishale.com/?p=33095) search-only |
| ACDSee Photo Studio Ultimate 2027 | $179.99 perpetual, 1 device; ACDSee 365 Complete $9.99/mo or $99.99/yr | Local | Not stated (labels similar faces after you name some) | Single-device licence | [ACDSee buy page](https://www.acdsee.com/en/products/photo-studio-ultimate/buy/) fetched |
| Adobe Lightroom Classic | Lightroom plan $11.99/mo; Photography plan $19.99/mo | Classic catalog local | No (People view, name faces) | Subscription only | [Adobe](https://www.adobe.com/products/photoshop-lightroom.html) fetched |
| Apple Photos | Included with device; iCloud price NOT FOUND | Not confirmed | No (name a person, search by name) | ~15 photos needed before a person auto-appears (one community reply); missed faces not rescanned | [Apple Community](https://discussions.apple.com/thread/251052014) search-only |
| Google Photos | 15 GB free; paid tiers NOT FOUND officially | Cloud | No (name group, search label) | Not available in all regions/account types | [Google help](https://support.google.com/photos/answer/6128838) fetched |
| Amazon Photos | Price NOT FOUND | Cloud | No | Recognition off by default for Illinois residents | search-only |
| PhotoPrism | Community free (AGPL); membership ~EUR 2-6/mo | Self-hosted | No (manual confirmation) | 2022 forum report of missed/wrong faces | [docs](https://docs.photoprism.app/user-guide/ai/face-recognition/) search-only |
| Immich | Free, open source (licence not verified) | Self-hosted | No evidence found (issue tracker not browsed) | - | [docs](https://immich.app/docs/features/facial-recognition) search-only |
| Mylio | Price NOT FOUND | Hybrid | NOT FOUND | Claims faces recognised "fully offline" | [pricing](https://www.mylio.com/pricing) fetched |
| Tonfotos | Free tier / $59 lifetime (own site) or $39 + $99 family (third party); conflicting | Local | NOT FOUND | Slow indexing, telemetry, no mobile app | [Tonfotos](https://tonfotos.com/articles/best-face-recognition-software/) search-only |
| Events (mher) | Price NOT FOUND (vendor 403) | Unknown | **Appears to have a "Single person" mode: closest to our idea, unverified** | - | [toolfarm](https://www.toolfarm.com/buy/mher_events) search-only |
| SnapSort | Free, open source | Local | No (scan folder, click a face) | - | [DEV post](https://dev.to/abhishek_singhkushwaha_b/snapsort-v100-cross-platform-face-sorting-app-5c50) search-only |
| Face Folder (iOS) | R19.99 (ZA storefront) | Claims on-device | Not stated | Too few ratings, no traction signal | [App Store](https://apps.apple.com/za/app/face-folder/id6758640525) fetched |
| PimEyes (web face search, separate category) | $29.99-$300/mo per aggregators, unconfirmed | Cloud | Yes, but public web only | Accused of scraping images of deceased people | search-only |
| `face_recognition` (open-source Python lib) | Free | Local | Reportedly can search a folder from a face photo | Developer tool, not a consumer product | [PyPI](https://pypi.org/project/face-recognition/0.1.3) search-only |

Not researched: Picasa (legacy), Windows Photos.

## Demand evidence (weak)
- Dropbox Community feature request "Facial recognition": a user whose father had just died needed photos of him quickly for the funeral; thread text, date and votes not read. [thread](https://www.dropboxforum.com/idea/101002013/facial-recognition/856824) search-only. Only memorial-specific item found.
- digiKam bug 363724 shows the gap exists, not its size (fetched).
- Digitisation backlog: ScanMyPhotos survey of 250 of its own clients (76% undigitised, vendor sample); Capture.HK claims 1M photos digitised in 2024 (company claim). search-only.
- IAPP: a facial recognition tool allegedly scraped images of deceased people to identify living relatives. Supports the privacy/sensitivity angle. search-only.
- NOT FOUND: Reddit threads, search-trend data, market-size figure for memorial/genealogy, user counts. Vendor CAGR figures were discarded (no named source).

## Price benchmarks
- One-off desktop: Tonfotos $39-$99; ACDSee Ultimate $179.99; Excire $129-$249.
- Subscription: Lightroom $11.99-$19.99/mo; ACDSee 365 $99.99/yr; PhotoPrism ~EUR 2-6/mo.
- Free: digiKam, Immich, PhotoPrism CE, SnapSort.
- **Inference (not researched):** a single-purpose tool would plausibly sit around $20-60 one-off.

## Mobile gap (inference mostly)
Apple Photos and Google Photos already group, name and search faces. The remaining gap is narrow: photos outside the phone gallery (old backups, other drives) and recall-oriented single-person extraction. Android file-access limits were not researched here (see tech report).

## Differentiation verdict (agent inference, to be challenged)
- Defensible: single-person extraction from a supplied reference photo with tiers (confirmed / maybe). No mainstream product found with that workflow, except possibly Events (unverified).
- Weak: local/private processing is offered by ACDSee, Excire, digiKam, PhotoPrism, Immich, Tonfotos, so it is table stakes. Copy-only is easy to copy.
- Commercial value likely small: free tools cover most needs, memorial use is often a one-off task, no volume evidence found.
- Suggested validation: try Events, Tonfotos, ACDSee to confirm they cannot do reference-photo search; ask memorial/genealogy communities.

## Uncertain
Official prices (Excire, Mylio, Google One, iCloud); whether Immich/Tonfotos support reference-photo search; Events price/quality; Reddit threads; user counts; most search-only sources were not opened.
