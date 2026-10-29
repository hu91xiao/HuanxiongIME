# 第三方组件与许可

本项目是 **Rime 小狼毫 0.17.4 的改造工程**，不包含也不重新实现输入法内核。
分发形式（安装包）捆绑了上游二进制，因此整体分发受 **GPLv3** 约束，见 `LICENSE`。

| 组件 | 用途 | 许可 | 来源 |
| --- | --- | --- | --- |
| [Rime 小狼毫 / Weasel](https://github.com/rime/weasel) 0.17.4 | Windows 输入法前端（TSF 服务、候选窗、部署器） | **GPL-3.0** | `payload/program/`（不随仓库分发，见下） |
| [librime](https://github.com/rime/librime) 1.13.1 | 输入法核心（含 `rime.dll`） | **GPL-3.0** | 随 Weasel 安装包提供 |
| [极点五笔86 词库](https://github.com/KyleBing/rime-wubi86-jidian) | `wubi86_jidian*.dict.yaml` 五笔码表 | 上游未标注许可；原作者 王永民（五笔字型） | 上游仓库，按原样分发 |
| 简体拼音词库 | `pinyin_simp.dict.yaml` 拼音码表 | 源自 Android PinyinIME（Apache-2.0） | Rime 官方 `rime-dictionary` |
| [CC-CEDICT](https://cc-cedict.org/) | `zh_en_dict.lua`（73,613 条中英对照，自动生成） | **CC BY-SA 4.0** | 由 CC-CEDICT 与青简术语表生成 |
| [Noto Sans SC](https://fonts.google.com/noto/specimen/Noto+Sans+SC) | 候选窗字形 | **SIL OFL 1.1** | 不随仓库分发，见下 |
| [pywebview](https://github.com/r0x0r/pywebview) | 设置面板原生窗口 | MIT | PyPI |
| [PyInstaller](https://pyinstaller.org/) | 打包设置面板 | GPL-2.0 + bootloader 例外 | PyPI |
| [Inno Setup](https://jrsoftware.org/isinfo.php) | 生成安装程序 | 修改版 MPL（允许自由分发产物） | 构建工具 |

## 仓库内不含、需要单独获取的素材

`payload/program/`（约 31MB）和 `payload/fonts/`（约 17MB）**不在版本库中**：

- **`payload/program/`** —— Weasel 0.17.4 的运行副本，经二进制资源改造（品牌字符串、托盘菜单裁剪）。
  GPLv3 要求分发二进制时提供对应源码，因此不把它塞进 Git 历史。要构建自己的版本：
  先安装 [上游 0.17.4 安装包](https://github.com/rime/weasel/releases/tag/0.17.4)，
  再跑 `python build.py payload` 从本机安装目录快照；改造脚本在 `tools/legacy/`。
- **`payload/fonts/`** —— Noto Sans SC，SIL OFL 1.1 允许再分发，但同样不进 Git 历史以控制体积。

## 改造说明（GPLv3 §5 要求的修改声明）

本项目对上游 Weasel 0.17.4 二进制所做的修改，全部由 `tools/legacy/` 下的脚本完成，可复现：

| 脚本 | 修改内容 |
| --- | --- |
| `patch_brand.py` + `winres.py` | 替换 PE 资源中的产品名、公司名、字符串表、图标（「小狼毫」→「幻熊输入法」） |
| `patch_menu.py` | 重写托盘右键菜单（`RT_MENU` 105/108/109 × 三种语言），移除「重新部署」等项 |
| `unregister_legacy_ime.py` | 清理早期实验遗留的 IMM 兼容版输入法注册项 |

未修改任何 C++ 源码，也未重新编译内核；所有改动均为 PE 资源层面的替换。因此上游源码即对应源码，
改造差异由上述脚本完整描述。

## 本项目原创部分

以下内容为本项目原创，按 GPLv3 发布：

- `src/settings/` —— 设置面板（Python + HTML/CSS/JS）
- `payload/rime/rime.lua` —— Rime Lua 过滤器（英文注释、Ctrl+数字上屏、回车上原文、日期、计算器）
- `payload/rime/ue_terms.lua` —— 虚幻引擎 / 游戏开发术语中英对照表（手写，优先级最高）
- `tools/gen_ue_dict.py` —— UE 术语写入五笔/拼音码表的生成器
- `installer/setup.iss`、`build.py` —— 打包与安装逻辑
