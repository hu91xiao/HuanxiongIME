# 清理安装目录里改造期间留下的备份 / 一次性文件（不属于安装包内容）
$dir = 'C:\Program Files\Rime\weasel-0.17.4'
$kill = @(
  'rime-install.bat', 'rime-install-config.bat', 'uninstall.exe',
  'WeaselSetup.orig.exe', 'WeaselDeployer.onefile.bak.exe'
)
foreach ($f in $kill) {
  $p = Join-Path $dir $f
  if (Test-Path $p) { Remove-Item $p -Force -Confirm:$false }
}
Get-ChildItem $dir -File |
  Where-Object { $_.Name -match '\.(bak_brand|bak_menu)$' } |
  ForEach-Object { Remove-Item $_.FullName -Force -Confirm:$false }
Write-Output ("剩余 " + (Get-ChildItem $dir).Count + " 项")
Get-ChildItem $dir | Select-Object -ExpandProperty Name
