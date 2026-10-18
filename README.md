<p align="center"><img src="docs/screenshots/icon.png" width="96" alt=""></p>

<h1 align="center">Photo Finder Pro</h1>

<p align="center">
Find every photo of one person in your photo folders, using face matching that runs entirely on your own PC.<br>
Your originals are only read. Matches are <b>copied</b> to a results folder; nothing is moved, deleted or uploaded.
</p>

<p align="center"><b><a href="../../releases/latest">⬇ Download for Windows</a></b> · 繁體中文 / English · free, personal project</p>

![Photo Finder Pro, dark theme](docs/screenshots/dark.png)

## What it does

You give it a few reference photos of a person, for example Grandpa at different ages, and one or more photo folders. It goes through every photo, including sub-folders, and finds the ones where that person appears.

- **Local and private.** Face detection (YuNet) and recognition (SFace) run offline on your CPU. The app makes no network calls and sends no telemetry.
- **Safe by design.** Original photos are opened read-only. Every copy is verified with SHA-256, and existing files are never overwritten. Each search gets its own results folder.
- **Live results.** Matches appear while the scan runs. You see progress, speed and time left. You can stop at any point and resume later.
- **Fast review.** Double-click a result, then press **Y** for "it's them" or **N** for "not them", and it moves to the next photo. Marks are only labels; no file is ever deleted.
- **Final export.** One click copies the reviewed set into `final\` inside the search's results folder.
- **Better with use.** Add good results back as reference photos to improve matching. Photos with several people let you pick the right face.
- **Comfortable to use.**
  - Dark and light themes, Traditional Chinese and English.
  - Drag and drop folders and photos onto the window.
  - Zoomable, face-centred thumbnails.
  - Accuracy presets: Loose, Balanced, Strict.
  - HEIC (iPhone) photos are supported.

| Light theme | Scanning (English) |
|---|---|
| ![Light theme](docs/screenshots/light.png) | ![Scanning in English](docs/screenshots/scanning-en.png) |

*The screenshots use generated colour images, not real photos.*

## Install (Windows 10/11)

1. Download `PhotoFinderPro-<version>-win64.zip` from [Releases](../../releases/latest).
2. Unzip it anywhere and run `PhotoFinderPro.exe`. You don't need to install anything or have admin rights.
3. The app is not code-signed, so Windows SmartScreen may warn you the first time. Click **More info → Run anyway**.

Settings, the scan index and thumbnails are stored in `%LOCALAPPDATA%\PhotoFinderPro`. To uninstall, delete the unzipped folder and that folder.

## How to use

1. **Photo folders.** Add or drag in the folders to search. Sub-folders are included.
2. **Who to find.** Add a few clear reference photos. More photos from different years give better results.
3. **Accuracy.** Pick Balanced to start. Photos at or above *Confirm* (50%) are matches. Photos between *Review* (30%) and *Confirm* go to "To review".
4. **Save results to.** Choose an output folder. It must not be inside a photo folder.
5. Click **Start search**. Then review the "To review" tab with Y/N and click **Export final**.

## Run from source

Requires Python 3.12+ on Windows.

```bat
python -m venv venv
venv\Scripts\pip install -r requirements.txt
run_photofinderpro.bat
```

Run the tests. They use synthetic images and a fake face engine, with no real photos:

```bat
venv\Scripts\python -m pytest -q -p no:cacheprovider tests
```

Build the portable zip. This uses PyInstaller onedir, runs a self-test, then zips the result:

```bat
cmd /c packaging\build.bat
```

## Project layout

```
src/photofinder/      engine, scanner, index (SQLite), matcher, copier (copy-only), workers, settings, i18n, theme
src/photofinder/ui/   main window, result grid, viewer, history, dialogs, widgets, icons
models/               YuNet (MIT) and SFace (Apache-2.0) ONNX models from OpenCV Zoo
packaging/            PyInstaller spec, build script, icon generator
tests/                pytest suite
docs/                 screenshots and research notes
```

## Limits

- Accuracy has not been measured on a real-face benchmark. It drops on small faces, strong side views and large age gaps.
- Windows only for now.
- This is a personal project, not a commercial product. The SFace weights were trained on public face datasets whose terms may restrict commercial use. Please only search photo collections you own or are allowed to use.

Third-party licences are listed in [THIRD_PARTY_NOTICES.txt](THIRD_PARTY_NOTICES.txt).

---

### 中文簡介

**Photo Finder Pro**:俾幾張參考相,喺你嘅相片資料夾入面搵晒某一個人嘅所有相,並複製一份去結果資料夾。

- 全部喺本機運算,唔會上載任何嘢。
- 原相只會讀取,唔會改動、搬走或者刪除。
- 雙擊相片後用 Y / N 鍵快速確認,完成後一鍵匯出最終結果。

由 [Releases](../../releases/latest) 下載 zip,解壓後執行 `PhotoFinderPro.exe` 就用得。如果 Windows 彈出警告,撳「其他資訊 → 仍要執行」。
