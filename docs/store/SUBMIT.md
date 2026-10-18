# Submitting Photo Finder Pro

## Microsoft Store (MSIX)

The Store re-signs MSIX packages with Microsoft's certificate, so you do **not** need a code-signing certificate. You upload an unsigned `.msix`.

### Files prepared in this repo

| File | Purpose |
|---|---|
| `packaging/make_msix.ps1` | Builds `dist\PhotoFinderPro-1.0.0.msix` from `dist\PhotoFinderPro\` |
| `packaging/msix/store_identity.json` | The three Partner Center identity values (placeholders for now) |
| `packaging/msix/AppxManifest.xml` | Manifest template (full-trust desktop app, x64, Windows 10 1809+) |
| `packaging/msix/Assets/` | Generated logos (`packaging/msix/make_assets.py` regenerates them) |
| `PRIVACY.md` | Privacy policy (English and Traditional Chinese) |
| `docs/store/listing.md` | Listing text for en-US and zh-HK, keywords, age rating answers |
| `docs/store/screenshots/` | 1920x1080 screenshots (`make_screenshots.py` regenerates them) |

### Steps

1. **Register** a Microsoft Partner Center developer account (individual accounts have a one-time registration fee; check the current amount on the sign-up page): <https://partner.microsoft.com/dashboard/registration>.
2. **Reserve the name.** Apps and games > New product > MSIX or PWA app > reserve **Photo Finder Pro**. If it is taken, pick another; the in-app name does not have to match.
3. **Copy the identity.** In the product, open **Product management > Product identity**. Copy these three values into `packaging/msix/store_identity.json`:
   - `Package/Identity/Name` (looks like `12345Kylekk29.PhotoFinderPro`) into `"name"`
   - `Package/Identity/Publisher` (looks like `CN=XXXXXXXX-XXXX-...`) into `"publisher"`
   - `Package/Properties/PublisherDisplayName` into `"publisher_display_name"`
   - Keep `"version"` as `1.0.0.0`. The Store requires the last number to be 0. Raise the first three for each update.
4. **Build.** Build the app first, then the package:
   ```
   cmd /c packaging\build.bat
   powershell -ExecutionPolicy Bypass -File packaging\make_msix.ps1
   ```
   Output: `dist\PhotoFinderPro-1.0.0.msix` (about 130 MB). The script warns if the identity is still a placeholder. It uses `makeappx.exe` from the Windows SDK, or from `tools\sdk-buildtools\pkg` (NuGet package `Microsoft.Windows.SDK.BuildTools`, extracted there) if the SDK is not installed.
5. **Packages.** In the submission, open **Packages** and upload the `.msix`. It validates the identity against the reserved name. Platforms: Windows 10 Desktop. Do **not** upload the `-testsigned` file.
6. **Pricing and availability.** Free. Markets: all (or the ones you choose). Visibility: public.
7. **Properties.** Category: **Photo & video**. Privacy policy URL: `https://github.com/Kylekk29/PhotoFinderPro/blob/main/PRIVACY.md`. Support contact: `https://github.com/Kylekk29/PhotoFinderPro/issues`. System requirements from `listing.md`.
8. **Age ratings.** Fill the IARC questionnaire with the answers in `listing.md` (expected 3+).
9. **Store listings.** Add English (United States) and Chinese (Traditional, Hong Kong). Paste name, description, features, keywords, What's new and notes for certification from `listing.md`. Upload the matching screenshots from `docs/store/screenshots/` (en-* for English, zh-* for Chinese). Do not claim accuracy figures.
10. **runFullTrust justification.** Because the package declares the restricted capability `runFullTrust`, the submission asks why. Paste this into the restricted capabilities box:

    > Desktop app packaged from a Win32/PySide6 application; needs full trust to read user-selected photo folders and write copies to a user-selected output folder.

11. **Submit** for certification (usually within a few days). Fix any findings and resubmit. Do not change the package identity afterwards.

### Test the package locally (optional)

`make_msix.ps1 -TestSign` makes `dist\PhotoFinderPro-1.0.0-testsigned.msix`, signed with a self-signed certificate that lives in **your** `CurrentUser\My` store (no admin needed, private key not exportable, nothing is trusted system-wide). The public certificate is exported to `build\PhotoFinderPro-test.cer`. Windows only installs a package whose signing certificate is trusted, so to test-install it you must trust that certificate yourself, in an elevated (admin) PowerShell:

```
Import-Certificate -FilePath build\PhotoFinderPro-test.cer -CertStoreLocation Cert:\LocalMachine\TrustedPeople
Add-AppxPackage dist\PhotoFinderPro-1.0.0-testsigned.msix
```

This changes system trust, so only do it on a test machine or VM, and remove it afterwards:

```
Get-AppxPackage *PhotoFinderPro* | Remove-AppxPackage
Get-ChildItem Cert:\LocalMachine\TrustedPeople | Where-Object Subject -eq "CN=TODO" | Remove-Item
Get-ChildItem Cert:\CurrentUser\My | Where-Object FriendlyName -eq "PhotoFinderPro test signing" | Remove-Item
```

(Use your real publisher string instead of `CN=TODO` once `store_identity.json` has it. Never commit a `.pfx`; they are in `.gitignore`.)

### Regenerating screenshots

```
cd docs\store
..\..\venv\Scripts\python.exe make_screenshots.py screenshots\en-02-results-dark.png dark en grid
```

Arguments: output file, `dark|light`, `zh|en`, `empty|grid|scan|viewer`. They use generated gradient images only.

### Notes

- Inside an MSIX, writes to `%LOCALAPPDATA%` are redirected to a private per-package folder. The app only writes there (settings, index, thumbnails) and to the output folder the user picks, so this is fine. Uninstalling removes that private data.
- The app is not code-signed outside the Store. The Setup and Portable builds on GitHub are unchanged.
