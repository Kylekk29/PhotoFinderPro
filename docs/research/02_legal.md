# 02 Legal and compliance (draft from researcher agent, 2026-10-18)

**Research only. NOT legal advice. Consult a qualified lawyer (questions at the end).**
Status: PARTIAL, not yet spot-checked by the CEO. Many primary sources failed to load (ilga.gov, elegislation.hk, PCPD biometric guidance PDF, EDPB PDFs). Claims resting on secondary sources or the agent's background knowledge are marked "(unverified)".

## Headline
Facts (sourced):
- **G.T. v. Samsung Electronics America** (7th Cir., No. 25-1120, reported 2026-08-20): a gallery app that scanned stored photos and made on-device face templates was held NOT to "possess" or "collect" biometric data under BIPA, because that needs some control over the data. Caveats: binds only federal courts in the 7th Circuit; assumed without deciding that templates are BIPA data; rested on no allegation Samsung could access the data. Source: [Mayer Brown](https://www.mayerbrown.com/en/insights/publications/2026/08/seventh-circuit-holds-that-bipa-does-not-reach-biometric-data-that-remains-on-a-users-device). Opinion itself not obtained.
- **Barnett v. Apple** (Ill. App. Ct. 1st Dist., 2022-12-23) dismissed a BIPA claim over on-device Face ID/Touch ID. Sources: [Duane Morris](https://blogs.duanemorris.com/classactiondefense/2023/01/09/illinois-appellate-court-affirms-dismissal-of-bipa-class-action-lawsuit/); [opinion PDF](https://www.law.berkeley.edu/wp-content/uploads/2025/03/01-Barnett-v-Apple-Inc.pdf) (full text not verified).
- **GDPR Recital 18**: household exemption does not cover providers of the means for such processing. [gdpr-info.eu](https://gdpr-info.eu/recitals/no-18/). The exemption helps users, not necessarily the vendor.

Inference (agent): fully local, no-telemetry design => US BIPA exposure looks low but rests on fresh, narrow case law. EU/UK is the less clear one (vendor may be a "provider of means"). HK looks low on the statute but PCPD biometric guidance was not read.

## Per jurisdiction
| Jurisdiction | Facts and sources | Inference / uncertainty |
|---|---|---|
| Hong Kong PDPO | Personal data relates to a living individual; a deceased person is not a data subject; a data user controls collection/holding/processing/use ([PCPD slides](https://www.pcpd.org.hk/english/education_training/individuals/public_seminars/files/PDPO_eng_2026.pdf), search summary only). PCPD biometric guidance (2015, rev. 2020) lists facial images as biometric data; stresses necessity, PIA, informed consent; non-enforceable ([Baker McKenzie](https://www.bakermckenzie.com/-/media/files/insight/publications/2015/07/privacy-commissioner/al_hongkong_cautionsbiometricdata_jul15.pdf), [PCPD note](https://www.pcpd.org.hk/english/resources_centre/publications/files/GN_biometric_e.pdf) not read). s.52 domestic-purposes exemption covers data held solely for personal/family/household affairs, not collection under DPP1 ([e-lawbook](https://www.pcpd.org.hk/misc/booklets/e-lawbook/html/files/assets/basic-html/page-163.html)). | Whether a purely-local software vendor is a "data user": NOT FOUND. Plausibly not (inference). Deceased subject is outside PDPO but bystanders/living relatives in the same photo are not. |
| EU GDPR | Art 2(2)(c) household exemption ([Art 2](https://gdpr-info.eu/art-2-gdpr/)); Recital 18 (above); Art 4(14) biometric data, Art 4(7) controller ([Art 4](https://gdpr-info.eu/art-4-gdpr/)); Recital 51 photos only biometric when processed by specific technical means ([EUR-Lex](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32016R0679)); EDPB Guidelines 3/2019 and 05/2022 (PDFs not read; 05/2022 is law-enforcement-focused). | Embedding + matching to identify is very likely Art 9 biometric data (inference; Art 9 text not retrieved). Vendor role when fully local: NOT FOUND; arguments both ways. CJEU narrow reading of household exemption (Lindqvist, Ryneš, Jehovan todistajat) is background knowledge, unverified. Sharing matched photos of third parties is outside the exemption. Consumer law/VAT: not researched. |
| EU deceased | Recital 27: GDPR does not apply to deceased persons' data; member states may add rules. White & Case survey: DE/NL none; FR/IT/ES limited rights for heirs ([White & Case](https://www.whitecase.com/insight-our-thinking/gdpr-guide-national-implementation)). | National statutes not verified. Photos of the deceased nearly always contain living people. |
| Illinois BIPA | $1,000 negligent / $5,000 reckless per violation, private right of action; SB 2979 (2024-08-02) limits to one recovery per person per method ([DWT](https://dwt.com/blogs/privacy--security-law-blog/2024/08/illinois-bipa-biometrics-law-amended-for-damages), [King & Spalding](https://www.kslaw.com/insights/articles/illinois-bipa-reform-takes-effect)). Photo-derived face geometry not excluded at pleading stage in Monroy v. Shutterfly and Rivera v. Google (2017) ([Proskauer](https://newmedialaw.proskauer.com/2017/03/02/court-refuses-to-dismiss-biometric-privacy-action-over-facial-recognition-technology-used-by-google-photos/)); Rivera later dismissed for standing. Clearview settlement approved 2025-03-20 ([Bloomberg Tax](https://news.bloombergtax.com/esg/clearview-ai-gets-settlement-approved-in-face-scan-privacy-case)). | BIPA statute text NOT retrieved. s.15 duties and "photographs" exclusion from background knowledge, unverified. Samsung/Apple point towards low risk; Monroy/Rivera point the other way. One federal appellate decision only; other courts and any future cloud feature not covered. |
| Texas CUBI | Consent required before capturing biometric identifier for commercial purpose; AG enforces; Meta settled $1.4B (July 2024) ([Vinson & Elkins](https://velaw.com/insights/texas-biometrics-case-highlights-need-for-consent-meta-settles-for-1-4-billion)). | No private right of action (unverified). Meta case involved server-side photos: weak analogy for local-only. |
| Washington | RCW 19.375.020 bars enrolling a biometric identifier for a commercial purpose without notice/consent; AG-enforced ([wa-law.org](https://wa-law.org/rcw/19_business_regulations%E2%80%94miscellaneous/19.375_biometric_identifiers.html)). My Health My Data Act treats biometric data as consumer health data, opt-in consent ([Loeb](https://www.loeb.com/zh-hans/insights/publications/2024/02/washingtons-my-health-my-data-act-are-you-ready)). | Secondary sources. Whether local use is "collection" under MHMDA: NOT FOUND. MHMDA private right of action: unverified. |
| California | Biometric info used to uniquely identify is "sensitive personal information", Civ. Code 1798.140 ([SJUD analysis](https://sjud.senate.ca.gov/sites/sjud.senate.ca.gov/files/sb_1189_wieckowski_sjud_analysis.pdf)). | Business thresholds and local-vendor "collection": NOT FOUND. |
| Other US states, UK GDPR | NOT RESEARCHED | Ask counsel. |

## Deceased persons
- PDPO and GDPR do not protect the deceased (national law may differ). Not risk-free: photos include living people; FR/IT/ES give families some rights.
- Genealogy/memorial industry norms: NOT FOUND.
- Inference: same technology as for the living; legal risk comes from other faces. Careful wording, results as suggestions, gentle grief UX.

## Third parties and bystanders
The app must compute embeddings for every face in the library. HK s.52 fails beyond purely domestic use; EU exemption does not reach providers of the means. Whether scanning bystanders is biometric processing by anyone other than the user: question for counsel.

## App stores
Apple ([guidelines](https://developer.apple.com/app-store/review/guidelines/)): 5.1.1(i) privacy policy in metadata and app; 5.1.1(iii) request only relevant data, prefer picker where possible (full-library face matching needs justification); 5.1.1(ii) consent; 5.1.2(iv) no contact database from Photos data; 5.1.2(vi) facial-mapping data not for marketing/data mining; 5.1.1(ix) legal-entity rule for sensitive data may matter. No explicit ban on face recognition of a user's own library found (only first 100k characters read). Data processed only on device is not "collected" for privacy labels ([Apple](https://developer.apple.com/app-store/app-privacy-details/), search summary).
Google Play: READ_MEDIA_IMAGES only if the system picker is insufficient; broad access for apps whose core function is managing photos; Play Console declaration required, mandatory by 2025-05-28 ([policy](https://support.google.com/googleplay/android-developer/answer/14115180)). Whether a face-matching scanner counts as "gallery-like": not found, main store risk. Data safety section required ([help](https://support.google.com/googleplay/android-developer/answer/10787469)); no biometric-specific rule found (full User Data policy not read).
Desktop stores (Microsoft Store, direct): NOT RESEARCHED.

## Misuse mitigations (inference)
Own library only; no web/social scraping or "find a stranger"; local-only, no telemetry with images/embeddings; wipe control and delete on uninstall; optional DB encryption; first-run notice; no cross-person search over shared libraries; any future cloud feature = legal re-review trigger (Samsung/Apple rulings turned on no vendor access).

## Privacy policy / terms checklist
Policy: what is processed (embeddings, local DB), stays on device, vendor cannot access; legal basis/consent per region (explicit consent EU); retention and deletion; no sale/sharing; children; rights and contact; change notices; future cloud opt-in; HK DPP1 notice, EU Art 13, BIPA-style retention policy if US release, CCPA notice.
Terms: licence scope; personal/private use only; prohibit stalking, harassment, identifying strangers, covert surveillance; warranty/liability limits (check consumer law); accuracy disclaimer (probabilistic, can miss or mismatch); user responsibility for third parties and local law; indemnity; age limit; termination; governing law; export/sanctions; acknowledgement of sensitive memorial use. Keep policy, store labels and behaviour consistent.

## Export / licensing
Not researched in depth (background only, unverified): standard encryption declarations are usually simple. Check licences of face-model weights (see 03 licences report).

## Questions for a lawyer
1. HK: is a purely-local software vendor a "data user"? Does s.52 cover a user keeping bystander embeddings for personal use?
2. EU: given Recital 18, is the vendor controller/joint/processor/outside GDPR when it has no access? Does the user fall within Art 2(2)(c)?
3. Is an embedding computed to match a person Art 9 data? What DPIA/consent documents would the vendor need if in scope?
4. US: how far does G.T. v. Samsung protect a paid third-party app outside the 7th Circuit, in Illinois state courts, with TX/WA enforcement and MHMDA?
5. If cloud backup/sync/support upload is ever added, what changes? Does crash reporting with metadata matter?
6. Deceased persons: do FR/IT/ES rules or others affect the app?
7. App stores: does a face-matching scanner meet Google's READ_MEDIA_IMAGES core-functionality test? What should Apple permission strings and review notes say?
8. Terms: enforceable disclaimers and age limits per region; liability for misuse to stalk.
9. Is a legal entity required (Apple 5.1.1(ix)); EU Art 27 representative?
10. Other US states with biometric/sensitive-data rules that could apply to a local-only vendor.

## Uncertain / not found
NOT FOUND: HK PCPD statement on software vendors; EU regulator statement on local-only face-matching vendors; memorial industry norms; Google Play biometric-specific text. Could not read: PDPO text, PCPD biometric guidance, BIPA text, GDPR Art 9(1), EDPB guidelines, Samsung opinion, 7th Cir. Clearview outcome, tail of Apple guidelines. Secondary only: TX/WA/CA/HK enforcement, Barnett details, national deceased-person rules.
