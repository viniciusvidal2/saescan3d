; installer.iss
[Setup]
AppName=SAEScan3D
AppVersion=1.0.3
DefaultDirName={pf64}\SAEScan3D
DefaultGroupName=SAEScan3D
OutputDir=.
OutputBaseFilename=SAEScan3D_installer
Compression=lzma2
SolidCompression=yes

[Files]
Source: "dist\saescan3d\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs
Source: "resources\saescan3d.ico"; DestDir: "{app}\resources"

[Icons]
Name: "{group}\SAEScan3D"; Filename: "{app}\SAEScan3D.exe"; IconFilename: "{app}\resources\saescan3d.ico"
Name: "{autodesktop}\SAEScan3D"; Filename: "{app}\SAEScan3D.exe"; Tasks: desktopicon; IconFilename: "{app}\resources\saescan3d.ico"
Name: "{group}\Uninstall SAEScan3D"; Filename: "{uninstallexe}"

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop shortcut"; GroupDescription: "Additional icons:"

[Run]
Filename: "{app}\SAEScan3D.exe"; Description: "Launch SAEScan3D"; Flags: nowait postinstall skipifsilent
