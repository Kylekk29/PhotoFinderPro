<p align="center"><img src="docs/screenshots/icon.png" width="96" alt=""></p>

<h1 align="center">Photo Finder Pro</h1>

<p align="center">
Find every photo of one person in your photo folders, using face matching that runs entirely on your own PC.<br>
Your originals are only read. Matches are <b>copied</b> to a results folder; nothing is moved, deleted or uploaded.
</p>

<p align="center"><b><a href="../../releases/latest">⬇ Download for Windows</a></b> · 简体中文 / English · free and open source (MIT)</p>

![Photo Finder Pro, dark theme](docs/screenshots/dark.png)

## What it does

You give it a few reference photos of a person, for example Grandpa at different ages, and one or more photo folders. It goes through every photo, including sub-folders, and finds the ones where that person appears.

- **Local and private.** Face detection (YuNet) and recognition (SFace) run offline on your CPU. The app makes no network calls and sends no telemetry.
- **Safe by design.** Original photos are opened read-only. Every copy is verified with SHA-256, and existing files are never overwritten. Each search gets its own results folder.
- **Live and fast.** Photos are analysed on several CPU threads at once. Matches appear while the scan runs. You see progress, speed and time left. You can stop at any point and resume later.
- **Fast review.** Double-click a result (or press **Enter**), then press **Y** for "it's them" or **N** for "not them", and it moves to the next photo. In the grid, **Ctrl+A** selects the page and **Y / N / U** mark or clear the selection. Marks are only labels; no file is ever deleted.
- **Sort by similarity or date taken.** Date comes from the photo's EXIF data, or the file date if there is none, and is cached in the app's own index.
- **Final export.** One click copies the reviewed set into `final\` inside the search's results folder.
- **Better with use.** Add good results back as reference photos to improve matching. Photos with several people let you pick the right face.
- **Comfortable to use.**
  - Dark and light themes. The interface is in Simplified Chinese or English, and the installer asks in your system language.
  - Drag and drop folders and photos onto the window.
  - Zoomable, face-centred thumbnails.
  - Accuracy presets: Loose, Balanced, Strict.
  - HEIC (iPhone) photos are supported.
  - Remembers the window size and position. An **About** box and a "Check for updates" link (it only opens the GitHub releases page in your browser) are in the ⋯ menu.

| Light theme | Scanning (English) |
|---|---|
| ![Light theme](docs/screenshots/light.png) | ![Scanning in English](docs/screenshots/scanning-en.png) |

*The screenshots use generated colour images, not real photos.*

## Install (Windows 10/11)

[**Download for Windows**](../../releases/latest). All files are 64-bit (x64). The release has three, so pick one:

- **Setup (recommended):** `PhotoFinderPro-<version>-x64-Setup.exe`. Double-click it and follow the wizard. It installs for your user only, so it needs no admin rights. You get a Start menu entry (and an optional desktop shortcut), and you can remove it in Windows **Settings → Apps**.
- **Portable:** `PhotoFinderPro-<version>-x64-Portable.exe`. A single file. Put it anywhere and double-click it. Nothing is installed. The first start takes a few seconds while it unpacks itself.
- **Zip:** `PhotoFinderPro-<version>-x64.zip`. Unzip it anywhere and run `PhotoFinderPro.exe`. Nothing is installed, and it starts faster than the single-file version.

`SHA256SUMS.txt` lists the SHA-256 of each file if you want to check your download.

### How to be sure your download is genuine

1. Download only from this repository's **Releases** page (`github.com/Kylekk29/PhotoFinderPro/releases`), never from a mirror or a link someone sends you.
2. Download `SHA256SUMS.txt` from the same release, next to the file you picked.
3. Open PowerShell in your Downloads folder and run (use the name of the file you downloaded):

   ```powershell
   Get-FileHash .\PhotoFinderPro-1.0.1-x64-Setup.exe -Algorithm SHA256
   ```

4. Compare the `Hash` value with the line for that file in `SHA256SUMS.txt`. If they are identical (letters are not case-sensitive), the file is intact and is the one published here. If they differ, delete the file and download it again.

The source code in this repository is the complete source of the app, and the app makes no network calls, so you can read it yourself.

The app is not code-signed, so Windows SmartScreen may warn you the first time. Click **More info → Run anyway**.

Settings, the scan index and thumbnails are stored in `%LOCALAPPDATA%\PhotoFinderPro` in both cases. Uninstalling the Setup version keeps this folder (and, of course, your photos and results). Delete it by hand if you want everything gone.

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

Build the release files (onedir build, self-test, zip, onefile build, self-test, installer, checksums). The installer step needs [Inno Setup 6](https://jrsoftware.org/isinfo.php) (`winget install --id JRSoftware.InnoSetup -e`):

```bat
cmd /c packaging\build.bat
```

Outputs: `dist\PhotoFinderPro-1.0.1-x64-Setup.exe`, `dist\PhotoFinderPro-1.0.1-x64-Portable.exe`, `dist\PhotoFinderPro-1.0.1-x64.zip` and `dist\SHA256SUMS.txt`.

## Microsoft Store package (MSIX)

After `packaging\build.bat`, build the Store package with `powershell -ExecutionPolicy Bypass -File packaging\make_msix.ps1`. It writes `dist\PhotoFinderPro-1.0.1.msix` (unsigned; the Store signs it). The package identity comes from `packaging\msix\store_identity.json`, which holds placeholders until the values from Partner Center are pasted in. It needs `makeappx.exe` from the Windows SDK, or from the NuGet package `Microsoft.Windows.SDK.BuildTools` extracted to `tools\sdk-buildtools\pkg`. Add `-TestSign` to also make a self-signed copy for local testing; to install that copy you must trust its certificate yourself, as described in [docs/store/SUBMIT.md](docs/store/SUBMIT.md). See that file for the full submission steps and [PRIVACY.md](PRIVACY.md) for the privacy policy.

## Project layout

```
src/photofinder/      engine, scanner (parallel), index (SQLite), dates, matcher, copier (copy-only), workers, settings, i18n, theme
src/photofinder/ui/   main window, result grid, viewer, history, dialogs, widgets, icons
models/               YuNet (MIT) and SFace (Apache-2.0) ONNX models from OpenCV Zoo
packaging/            PyInstaller specs (onedir + onefile), Inno Setup script, build script, icon generator
tests/                pytest suite
docs/                 screenshots and research notes
```

## Limits

- Accuracy has not been measured on a real-face benchmark. It drops on small faces, strong side views and large age gaps.
- Windows only for now.
- This is a personal project, not a commercial product. The SFace weights were trained on public face datasets whose terms may restrict commercial use. Please only search photo collections you own or are allowed to use.

Licensed under the [MIT License](LICENSE). Third-party licences are listed in [THIRD_PARTY_NOTICES.txt](THIRD_PARTY_NOTICES.txt).

---

### 中文简介

**Photo Finder Pro** 是一款在本机运行的人脸查找工具:提供几张参考照片,它会在您的照片文件夹中找出某个人的全部照片,并复制一份到结果文件夹。

- **完全离线**:所有运算都在本机完成,程序不联网、不追踪、不上传任何内容。
- **保护原片**:原始照片只会被读取,不会被修改、移动或删除;复制的文件会用 SHA-256 校验,且不会覆盖已有文件。
- **快速确认**:双击照片后按 Y / N 键即可确认,完成后一键导出最终结果。
- **支持 HEIC**:可直接处理 iPhone 拍摄的照片。

#### 下载与安装(Windows 10/11)

请到 [Releases](../../releases/latest) 页面下载。所有文件均为 64 位(x64),三选一即可:

- **安装版(推荐)**:`PhotoFinderPro-<版本>-x64-Setup.exe`。双击后按向导操作,无需管理员权限,会创建开始菜单快捷方式(可选桌面快捷方式)。卸载请在 Windows“设置 → 应用”中进行,或使用开始菜单里的卸载快捷方式。
- **便携版**:`PhotoFinderPro-<版本>-x64-Portable.exe`。单个文件,放在任意位置双击即可使用,不会安装任何内容。首次启动需要几秒钟解压。
- **压缩包**:`PhotoFinderPro-<版本>-x64.zip`。解压后运行 `PhotoFinderPro.exe`,不会安装任何内容,启动速度比单文件便携版更快。

由于程序没有代码签名,首次运行时 Windows SmartScreen 可能会弹出警告,请点击“更多信息 → 仍要运行”。

#### 如何确认下载的文件可信

1. 只从本仓库的 **Releases** 页面下载,不要使用镜像站或他人发来的链接。
2. 同时下载同一个发布页中的 `SHA256SUMS.txt`。
3. 在下载目录中打开 PowerShell,运行下面的命令(文件名换成您实际下载的文件):

   ```powershell
   Get-FileHash .\PhotoFinderPro-1.0.1-x64-Setup.exe -Algorithm SHA256
   ```

4. 将输出的 `Hash` 与 `SHA256SUMS.txt` 中对应文件的那一行比较(不区分大小写)。完全一致,说明文件完整且就是这里发布的版本;不一致,请删除后重新下载。

#### 数据与卸载

设置、扫描索引和缩略图保存在 `%LOCALAPPDATA%\PhotoFinderPro`。卸载时程序会询问是否一并删除这些数据,默认保留;无论如何选择,您的照片和导出的结果都不会受到影响。
