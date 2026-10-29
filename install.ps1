<#
  幻熊输入法 · 一键安装脚本
  仓库：https://github.com/hu91xiao/HuanxiongIME

  用法（普通 PowerShell 窗口即可，脚本会自己请求管理员权限）：
      irm https://raw.githubusercontent.com/hu91xiao/HuanxiongIME/main/install.ps1 | iex

  如果访问 GitHub 需要代理，先执行这一行再重跑：
      $env:HUANXIONG_PROXY = 'http://127.0.0.1:7897'

  卸载走「设置 → 应用 → 幻熊输入法」，用户词频与配置会保留。
#>

$ErrorActionPreference = 'Stop'
try { [Console]::OutputEncoding = [Text.Encoding]::UTF8 } catch {}

$Repo    = 'hu91xiao/HuanxiongIME'
$Clsid   = '{A3F4CDED-B1E9-41EE-9CA6-7B4D0DE6CB0A}'
$Profile = '{3D02CAB6-2B8E-4781-BA20-1C9267529467}'
$PFDir   = if ($env:ProgramW6432) { $env:ProgramW6432 } else { $env:ProgramFiles }
$Dest    = Join-Path $PFDir 'Rime\weasel-0.17.4'

function Say  { param($m, $c = 'Gray') Write-Host "  $m" -ForegroundColor $c }
function Ok   { param($m) Say "[ OK ] $m" 'Green' }
function Warn { param($m) Say "[ !! ] $m" 'Yellow' }
function Bad  { param($m) Say "[FAIL] $m" 'Red' }

function Test-Admin {
  $id = [Security.Principal.WindowsIdentity]::GetCurrent()
  (New-Object Security.Principal.WindowsPrincipal($id)).IsInRole(
    [Security.Principal.WindowsBuiltInRole]::Administrator)
}

# ---------- 提权 ----------
if (-not (Test-Admin)) {
  if ($env:HUANXIONG_PROXY) {
    try { [Net.WebRequest]::DefaultWebProxy = New-Object Net.WebProxy($env:HUANXIONG_PROXY) } catch {}
  }
  $self = $PSCommandPath
  if (-not $self -or -not (Test-Path -LiteralPath $self)) {
    $self = Join-Path $env:TEMP 'huanxiong-install.ps1'
    try {
      Invoke-WebRequest -Uri "https://raw.githubusercontent.com/$Repo/main/install.ps1" `
                        -OutFile $self -UseBasicParsing -TimeoutSec 120
    } catch {
      Bad '下载安装脚本失败，请检查网络或代理。'
      Read-Host '按回车退出'
      exit 1
    }
  }
  Warn '需要管理员权限，正在打开新的管理员窗口…'
  $argLine = '-NoProfile -NoExit -ExecutionPolicy Bypass -File "{0}"' -f $self
  try {
    Start-Process -FilePath 'powershell.exe' -Verb RunAs -ArgumentList $argLine
  } catch {
    Bad '提权被取消，安装中止。'
    exit 1
  }
  exit 0
}

# ---------- 代理 ----------
if ($env:HUANXIONG_PROXY) {
  try {
    [Net.WebRequest]::DefaultWebProxy = New-Object Net.WebProxy($env:HUANXIONG_PROXY)
    Say "使用代理 $env:HUANXIONG_PROXY"
  } catch { Warn "代理设置失败：$($_.Exception.Message)" }
}
try { [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12 } catch {}

Write-Host ''
Say '幻熊输入法 · 安装程序' 'Cyan'
Say '虚幻引擎 / 游戏开发向的五笔 + 拼音输入法' 'DarkGray'
Write-Host ''

# ---------- 已安装？ ----------
if (Test-Path (Join-Path $Dest 'WeaselServer.exe')) {
  Warn "检测到已安装，将覆盖安装（你的词频和自定义短语会保留）"
  Get-Process WeaselServer -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
  Start-Sleep -Milliseconds 800
}

# ---------- 找最新版 ----------
Say '查询最新版本…'
$url = $null; $name = $null
try {
  $rel = Invoke-RestMethod -Uri "https://api.github.com/repos/$Repo/releases/latest" `
                           -Headers @{ 'User-Agent' = 'HuanxiongIME-Installer' } -TimeoutSec 45
  $asset = @($rel.assets | Where-Object { $_.name -like '*.exe' }) | Select-Object -First 1
  if ($asset) { $url = $asset.browser_download_url; $name = $asset.name }
} catch {
  Warn "GitHub API 不可用：$($_.Exception.Message)"
}
if (-not $url) {
  $name = 'HuanxiongIME-1.0-Setup.exe'
  $url  = "https://github.com/$Repo/releases/latest/download/$name"
  Warn '改用直连最新安装包。'
}
Ok "目标版本：$name"

# ---------- 下载 ----------
$tmp = Join-Path $env:TEMP $name
Say '下载安装包（约 24 MB）…'
$sw = [Diagnostics.Stopwatch]::StartNew()
try {
  $wc = New-Object Net.WebClient
  $wc.Headers.Add('User-Agent', 'HuanxiongIME-Installer')
  $wc.DownloadFile($url, $tmp)
} catch {
  Bad "下载失败：$($_.Exception.Message)"
  Write-Host ''
  Say '如果这台电脑访问 GitHub 需要代理，先执行下面这行再重试：' 'White'
  Say "  `$env:HUANXIONG_PROXY = 'http://127.0.0.1:7897'" 'White'
  exit 1
}
$sw.Stop()
Ok ("下载完成，{0:N1} 秒 / {1:N1} MB" -f $sw.Elapsed.TotalSeconds, ((Get-Item $tmp).Length / 1MB))
try { Unblock-File -LiteralPath $tmp } catch {}

# ---------- 安装 ----------
Say '开始安装（注册输入法 + 编译词库，1~3 分钟，不要关闭这个窗口）…'
$p = Start-Process -FilePath $tmp -PassThru -Wait -ArgumentList `
     '/VERYSILENT', '/SUPPRESSMSGBOXES', '/NORESTART', '/SP-'
if ($p.ExitCode -ne 0) {
  Bad "安装程序退出码 $($p.ExitCode)（0 才是成功）"
  Say '可能是杀软拦截，或安装包被杀软删掉了。'
  exit 1
}
Ok '安装程序已结束'

# ---------- 验证 ----------
Start-Sleep -Seconds 2
$fail = 0

if (Test-Path (Join-Path $Dest 'WeaselServer.exe')) {
  Ok "程序目录：$Dest"
} else { Bad "程序目录不存在：$Dest"; $fail++ }

$descKey = "HKLM:\SOFTWARE\Microsoft\CTF\TIP\$Clsid\LanguageProfile\0x00000804\$Profile"
$desc = $null
try { $desc = (Get-ItemProperty -Path $descKey -Name Description -ErrorAction Stop).Description } catch {}
if ($desc) { Ok "语言栏名称：$desc" } else { Bad '输入法未注册到系统（语言栏里找不到它）'; $fail++ }

if (Test-Path "HKLM:\SOFTWARE\Classes\CLSID\$Clsid") {
  Ok 'COM 组件注册正常'
} else { Bad 'COM 组件未注册'; $fail++ }

if (Get-Process WeaselServer -ErrorAction SilentlyContinue) {
  Ok '后台服务已运行'
} else {
  Warn '后台服务没在跑，尝试手动启动…'
  $exe = Join-Path $Dest 'WeaselServer.exe'
  if (Test-Path $exe) {
    Start-Process -FilePath $exe -WorkingDirectory $Dest
    Start-Sleep -Seconds 3
  }
  if (Get-Process WeaselServer -ErrorAction SilentlyContinue) { Ok '已启动' }
  else { Bad '后台服务启动失败'; $fail++ }
}

$rimeDir = Join-Path $env:APPDATA 'Rime'
if (Test-Path (Join-Path $rimeDir 'default.custom.yaml')) {
  Ok "用户配置：$rimeDir"
} else { Bad "用户配置缺失：$rimeDir"; $fail++ }

Remove-Item -LiteralPath $tmp -Force -ErrorAction SilentlyContinue

# ---------- 收尾 ----------
Write-Host ''
if ($fail -eq 0) {
  Say '装好了。' 'Green'
  Write-Host ''
  Say '· 按 Win+空格（或 Ctrl+空格）切到「幻熊输入法」' 'White'
  Say '· 右下角出现小熊图标就是成功；个别机器要注销一次才刷新语言栏' 'White'
  Say '· 改配色 / 每页候选数：开始菜单 →「幻熊输入法设置」' 'White'
  Say '· 使用说明：开始菜单 →「幻熊输入法使用说明」' 'White'
} else {
  Say "有 $fail 项检查没通过。把上面的红字整段发给作者即可。" 'Red'
}
Write-Host ''
