; Inno Setup 6 script. Build: ISCC packaging\installer.iss  (after the onedir build exists in dist\PhotoFinderPro)
#define AppName "Photo Finder Pro"
#define AppVersion "1.0.1"
#define AppExe "PhotoFinderPro.exe"

[Setup]
AppId={{B7E2A5D4-3C1F-4E8A-9A62-5F0D7C41E9B3}
AppName={#AppName}
AppVersion={#AppVersion}
AppVerName={#AppName} {#AppVersion}
AppPublisher=Kylekk29
AppCopyright=Copyright (C) 2026 Kylekk29. MIT License.
AppPublisherURL=https://github.com/Kylekk29/PhotoFinderPro
AppSupportURL=https://github.com/Kylekk29/PhotoFinderPro/issues
AppUpdatesURL=https://github.com/Kylekk29/PhotoFinderPro/releases
VersionInfoVersion={#AppVersion}
VersionInfoDescription={#AppName} Setup
VersionInfoProductName={#AppName}
ShowLanguageDialog=auto
UsePreviousLanguage=no
PrivilegesRequired=lowest
DefaultDirName={localappdata}\Programs\{#AppName}
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
UninstallDisplayIcon={app}\{#AppExe}
UninstallDisplayName={#AppName}
LicenseFile=..\LICENSE
CloseApplications=yes
RestartApplications=no
SetupIconFile=..\src\photofinder\assets\app.ico
OutputDir=..\dist
OutputBaseFilename=PhotoFinderPro-{#AppVersion}-x64-Setup
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "chinesesimplified"; MessagesFile: "lang\ChineseSimplified.isl"

[CustomMessages]
english.UninstallAskData=Also delete Photo Finder Pro settings, scan index and thumbnails?%n%n%1%n%nYour photos and saved results are NOT affected. Choose No to keep them (for a later reinstall).
chinesesimplified.UninstallAskData=是否同时删除 Photo Finder Pro 的设置、扫描索引和缩略图?%n%n%1%n%n您的照片和已保存的结果不受影响。选择“否”可保留这些数据,以便日后重新安装。

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
Source: "..\dist\PhotoFinderPro\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs ignoreversion

[Icons]
Name: "{autoprograms}\{#AppName}"; Filename: "{app}\{#AppExe}"
Name: "{autoprograms}\{cm:UninstallProgram,{#AppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExe}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#AppExe}"; Description: "{cm:LaunchProgram,{#AppName}}"; Flags: nowait postinstall skipifsilent

; Uninstall removes the program folder. It asks whether to also delete settings/index/thumbnails in
; %LOCALAPPDATA%\PhotoFinderPro (default: keep). Original photos and exported results are never touched.
[Code]
procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  DataDir: String;
begin
  if (CurUninstallStep = usPostUninstall) and not UninstallSilent then
  begin
    DataDir := ExpandConstant('{localappdata}\PhotoFinderPro');
    if DirExists(DataDir) then
      if MsgBox(FmtMessage(CustomMessage('UninstallAskData'), [DataDir]),
                mbConfirmation, MB_YESNO or MB_DEFBUTTON2) = IDYES then
        DelTree(DataDir, True, True, True);
  end;
end;
