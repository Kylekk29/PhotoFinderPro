; Inno Setup 6 script. Build: ISCC packaging\installer.iss  (after the onedir build exists in dist\PhotoFinderPro)
#define AppName "Photo Finder Pro"
#define AppVersion "1.0.0"
#define AppExe "PhotoFinderPro.exe"

[Setup]
AppId={{B7E2A5D4-3C1F-4E8A-9A62-5F0D7C41E9B3}
AppName={#AppName}
AppVersion={#AppVersion}
AppVerName={#AppName} {#AppVersion}
AppPublisher=Kylekk29
AppPublisherURL=https://github.com/Kylekk29/PhotoFinderPro
AppSupportURL=https://github.com/Kylekk29/PhotoFinderPro/issues
AppUpdatesURL=https://github.com/Kylekk29/PhotoFinderPro/releases
VersionInfoVersion={#AppVersion}
PrivilegesRequired=lowest
DefaultDirName={localappdata}\Programs\{#AppName}
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
UninstallDisplayIcon={app}\{#AppExe}
SetupIconFile=..\src\photofinder\assets\app.ico
OutputDir=..\dist
OutputBaseFilename=PhotoFinderPro-Setup-{#AppVersion}
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
Source: "..\dist\PhotoFinderPro\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs ignoreversion

[Icons]
Name: "{autoprograms}\{#AppName}"; Filename: "{app}\{#AppExe}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExe}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#AppExe}"; Description: "{cm:LaunchProgram,{#AppName}}"; Flags: nowait postinstall skipifsilent

; Uninstall removes only the program folder. User data in %LOCALAPPDATA%\PhotoFinderPro and all photos/results are never touched.
