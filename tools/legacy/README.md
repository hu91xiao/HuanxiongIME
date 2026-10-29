# legacy —— 一次性工具

这些脚本只在**把上游小狼毫改造成幻熊输入法**时跑过一遍（2026-10），
产物已经固化在 `payload/program/` 的二进制里，日常构建完全用不到它们。

留着是因为：将来如果想跟上游新版本（比如 0.18）重新对齐，
这套改法还能照着再走一遍。跑之前注意：

- 路径已改成相对/环境变量：图标读 `assets/icons/`，小狼毫目录默认
  `C:\Program Files\Rime\weasel-0.17.4`（可用环境变量 `WEASEL_DIR` 覆盖）。
- 都需要管理员权限，且会直接改 Program Files / System32 里的文件。
- 改完的二进制记得同步回 `payload/program/`，否则安装包还是旧的。

| 文件 | 做什么 |
| --- | --- |
| `patch_brand.py` + `winres.py` | 把图标、版本信息、产品名、关于框换成「幻熊输入法」，掐掉自动更新 |
| `patch_menu.py` | 重写托盘右键菜单：#105/108/109 × 三种语言全部改成「输入法设定 / 用户文件夹 / 退出」四项 |
| `unregister_legacy_ime.py` | 清掉老版"兼容输入法"（IMM 版 `weasel_legacy.ime`）的注册，只留 TSF 版 |
