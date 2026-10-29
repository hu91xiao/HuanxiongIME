; 幻熊输入法 1.0 —— Inno Setup 安装脚本
; 编译：build.py installer   （或 ISCC.exe installer\setup.iss）

#define AppName "幻熊输入法"
#define AppVer "1.0"
#define AppPub "DorpBear"
#define Exe "WeaselDeployer.exe"

[Setup]
AppId={{3C9A1E64-2B47-4F8D-9E15-A7C60B3D5F22}
AppName={#AppName}
AppVersion={#AppVer}
AppVerName={#AppName} {#AppVer}
AppPublisher={#AppPub}
AppComments=基于 Rime 小狼毫 0.17.4（GPLv3）改造的虚幻引擎/游戏开发向五笔拼音输入法
DefaultDirName={autopf}\Rime\weasel-0.17.4
DisableDirPage=yes
DisableProgramGroupPage=yes
DisableWelcomePage=no
PrivilegesRequired=admin
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
OutputDir=..\dist
OutputBaseFilename=幻熊输入法-{#AppVer}-安装程序
SetupIconFile=..\assets\huanxiong.ico
UninstallDisplayIcon={app}\{#Exe}
UninstallDisplayName={#AppName}
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
ShowLanguageDialog=no
CloseApplications=no
RestartApplications=no
AllowNoIcons=yes
VersionInfoVersion=1.0.0.0
VersionInfoDescription={#AppName} 安装程序
VersionInfoCompany={#AppPub}
VersionInfoProductName={#AppName}

[Languages]
Name: "cn"; MessagesFile: "compiler:Default.isl"

[Messages]
SetupAppTitle=安装程序
SetupWindowTitle=安装 %1
UninstallAppTitle=卸载
UninstallAppFullTitle=卸载 %1
ButtonBack=< 上一步
ButtonNext=下一步 >
ButtonInstall=安装
ButtonOK=确定
ButtonCancel=取消
ButtonYes=是(&Y)
ButtonNo=否(&N)
ButtonFinish=完成
ButtonBrowse=浏览…
WelcomeLabel1=欢迎安装 [name]
WelcomeLabel2=即将把 [name/ver] 装到你的电脑上。%n%n它会成为你的中文输入法：五笔优先 + 拼音兜底，专为虚幻引擎和游戏开发调过词库与英文直接上屏。%n%n安装过程会自动注册输入法（需要管理员权限），装完直接按 Ctrl+空格 或 Win+空格 切换即可使用。
ClickNext=点击「下一步」继续，或点「取消」退出安装。
WizardPreparing=正在准备安装
PreparingDesc=安装程序正在准备安装 [name]，请稍候。
PreparingToInstall=正在准备安装
ExtractLabel=正在解压：%1
ExtractingLabel=正在解压
InstallingLabel=正在安装
CreatingLabel=正在创建
StatusExtractFiles=正在解压文件…
StatusCreateIcons=正在创建快捷方式…
StatusCreateRegistryEntries=正在写入注册表…
StatusRunProgram=正在执行：%1
StatusRollback=正在回滚更改…
ReadyLabel1=安装程序已准备好，即将开始安装 [name]。
ReadyLabel2a=点击「安装」开始安装，或点击「上一步」检查并修改设置。
ReadyLabel2b=点击「安装」开始安装。
ReadyMemoDir=安装位置：
ReadyMemoGroup=开始菜单文件夹：
ReadyMemoTasks=附加任务：
FinishedHeadingLabel=[name] 安装完成
FinishedLabel=输入法已经装好了。%n%n首次使用请按 Win+空格（或 Ctrl+空格）切换到「幻熊输入法」，在任务栏右下角能看到小熊图标。%n%n想改配色、每页候选数、翻页键？双击桌面上的「幻熊输入法设置」。
FinishedLabelNoIcons=输入法已经装好了。
ClickFinish=点击「完成」退出安装程序。
SelectDirLabel3=安装程序将把 [name] 安装到下面的文件夹。
SelectDirBrowseLabel=点击「下一步」继续。如果想换一个文件夹，点击「浏览」。
SelectDirDesc=选择安装位置
DiskSpaceMBLabel=至少需要 [mb] MB 磁盘空间。
ConfirmUninstall=确定要卸载 %1 吗？卸载后需要重新安装才能继续输入中文（你自己的词频、短语和配置会保留）。
UninstalledAll=%1 已成功卸载。
UninstalledMost=%1 卸载完成。%n%n有些文件没能删除，你可以手动删除它们。
UninstallStatusLabel=正在卸载 %1，请稍候。
UninstallAppRunningError=%1 正在运行，请先关闭它再卸载。
SetupAppRunningError=安装程序检测到 %1 正在运行。%n%n请先关闭它，然后点击「确定」继续，或点击「取消」退出。
ErrorCopying=复制文件失败：%n%n%1%n%n点击「重试」再试一次，或点击「取消」退出。
ErrorCreatingDir=安装程序无法创建文件夹「%1」，请确认你有写入权限。
ErrorOpeningFile=无法打开文件：%1。
NoUninstall=安装程序找不到卸载记录，可能 %1 没有安装，或已经卸载过了。
ExitSetupTitle=退出安装
ExitSetupMessage=安装还没有完成，确定要退出吗？%n%n退出后输入法不会生效。
AboutSetupMenuItem=关于安装程序(&A)…
AboutSetupTitle=关于安装程序
AboutSetupMessage=%1 版本 %2%n%3%n%n%4
AboutSetupNote=安装程序由 Inno Setup 制作，详见 https://jrsoftware.org/isinfo.php
ButtonNewFolder=新建文件夹(&N)

[Tasks]
Name: "desktopicon"; Description: "在桌面创建「幻熊输入法设置」快捷方式"; GroupDescription: "附加任务："

[Files]
Source: "..\payload\program\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\payload\settings\HuanxiongSettings.exe"; DestDir: "{app}"; DestName: "{#Exe}"; Flags: ignoreversion
Source: "..\payload\settings\HuanxiongSettings_data\*"; DestDir: "{app}\HuanxiongSettings_data"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\payload\rime\*"; DestDir: "{userappdata}\Rime"; Flags: onlyifdoesntexist uninsneveruninstall
Source: "..\docs\使用说明.txt"; DestDir: "{app}"; Flags: ignoreversion

[Fonts]
Source: "..\payload\fonts\NotoSansSC-VF.ttf"; FontName: "Noto Sans SC (TrueType)"; Check: NeedFont

[Icons]
Name: "{autoprograms}\幻熊输入法设置"; Filename: "{app}\{#Exe}"; IconFilename: "{app}\{#Exe}"; Comment: "配色、候选数、翻页键都在这里改"
Name: "{autoprograms}\幻熊输入法使用说明"; Filename: "{app}\使用说明.txt"
Name: "{autodesktop}\幻熊输入法设置"; Filename: "{app}\{#Exe}"; IconFilename: "{app}\{#Exe}"; Tasks: desktopicon

[Registry]
Root: HKCU; Subkey: "Software\Rime\Weasel"; ValueType: string; ValueName: "RimeUserDir"; ValueData: "{userappdata}\Rime"
Root: HKCU; Subkey: "Software\Rime\Weasel"; ValueType: dword; ValueName: "Hant"; ValueData: "0"
Root: HKCU; Subkey: "Software\Rime\Weasel\Updates"; ValueType: string; ValueName: "CheckForUpdates"; ValueData: "0"

[Run]
Filename: "{app}\WeaselSetup.exe"; Parameters: "/s"; StatusMsg: "正在向系统注册输入法…"; Flags: runhidden waituntilterminated
Filename: "{app}\WeaselDeployer.orig.exe"; Parameters: "/deploy"; StatusMsg: "正在编译词库（首次约半分钟）…"; Flags: runhidden waituntilterminated
Filename: "{app}\{#Exe}"; Description: "打开设置面板"; Flags: nowait postinstall skipifsilent
Filename: "{app}\使用说明.txt"; Description: "查看使用说明"; Flags: shellexec nowait postinstall skipifsilent

[UninstallRun]
Filename: "{sys}\taskkill.exe"; Parameters: "/F /IM WeaselServer.exe /T"; Flags: runhidden; RunOnceId: "StopServer"
Filename: "{app}\WeaselSetup.exe"; Parameters: "/u"; Flags: runhidden waituntilterminated; RunOnceId: "UnregIME"

[Code]
const
  IME_CLSID = '{A3F4CDED-B1E9-41EE-9CA6-7B4D0DE6CB0A}';
  IME_PROFILE = '{3D02CAB6-2B8E-4781-BA20-1C9267529467}';
  IME_NAME = '幻熊输入法';

var
  InstallDone: Boolean;

{ 上游 WeaselSetup 注册输入法时用的是它内置的名字（小狼毫），
  注册完成后把语言栏里显示的名字改过来。5 个语言分支 + 32/64 位两套键。 }
procedure FixImeDisplayName();
var
  Langs: array[0..4] of String;
  I: Integer;
  Sub: String;
begin
  Langs[0] := '0x00000404';
  Langs[1] := '0x00000804';
  Langs[2] := '0x00000c04';
  Langs[3] := '0x00001004';
  Langs[4] := '0x00001404';
  for I := 0 to 4 do
  begin
    Sub := 'Software\Microsoft\CTF\TIP\' + IME_CLSID + '\LanguageProfile\' +
           Langs[I] + '\' + IME_PROFILE;
    RegWriteStringValue(HKLM, Sub, 'Description', IME_NAME);
    RegWriteStringValue(HKLM, 'Software\WOW6432Node\' + Sub, 'Description', IME_NAME);
  end;
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
    InstallDone := True;
end;

{ 部署完再拉起服务：部署过程会让旧服务退出，这里强制重启一次，
  保证装完立刻有托盘图标、配置也是刚编译好的那份。 }
procedure RestartServer();
var
  R: Integer;
  AppDir: String;
begin
  AppDir := ExpandConstant('{app}');
  Exec(ExpandConstant('{sys}\taskkill.exe'), '/F /IM WeaselServer.exe',
       '', SW_HIDE, ewWaitUntilTerminated, R);
  Sleep(700);
  Exec(ExpandConstant('{cmd}'),
       '/c start "" "' + AppDir + '\WeaselServer.exe"',
       AppDir, SW_HIDE, ewNoWait, R);
end;

procedure DeinitializeSetup();
begin
  if InstallDone then
  begin
    FixImeDisplayName();
    RestartServer();
  end;
end;

function NeedFont(): Boolean;
begin
  Result := not FileExists(ExpandConstant('{fonts}\NotoSansSC-VF.ttf'));
end;

function PrepareToInstall(var NeedsRestart: Boolean): String;
var
  R: Integer;
begin
  { 旧版本的服务会锁住 weasel.dll，装文件前先停掉 }
  Exec(ExpandConstant('{sys}\taskkill.exe'), '/F /IM WeaselServer.exe /T',
       '', SW_HIDE, ewWaitUntilTerminated, R);
  Sleep(800);
  Result := '';
end;
