; Inno Setup script — packages dist\GOATconvert\ into GOATconvert-Setup.exe.
; Build with: ISCC.exe /DMyAppVersion=1.2.3 installer.iss
#ifndef MyAppVersion
  #define MyAppVersion "0.1.0"
#endif

[Setup]
AppId={{9E6C6E6A-5C7D-4B6C-9A1D-3D6B9F6B3A21}
AppName=GOATconvert
AppVersion={#MyAppVersion}
AppPublisher=GOATconvert
DefaultDirName={autopf}\GOATconvert
DefaultGroupName=GOATconvert
DisableProgramGroupPage=yes
OutputDir=installer_output
OutputBaseFilename=GOATconvert-Setup
Compression=lzma2
SolidCompression=yes
ArchitecturesInstallIn64BitMode=x64compatible
SetupIconFile=goatconvert\assets\goat_icon.ico

[Files]
Source: "dist\GOATconvert\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs

[Icons]
Name: "{group}\GOATconvert"; Filename: "{app}\GOATconvert.exe"
Name: "{commondesktop}\GOATconvert"; Filename: "{app}\GOATconvert.exe"

[Run]
Filename: "{app}\GOATconvert.exe"; Description: "Launch GOATconvert"; Flags: nowait postinstall skipifsilent
