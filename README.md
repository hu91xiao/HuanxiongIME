# 幻熊输入法

面向 **虚幻引擎 / 游戏开发** 的中文输入法，基于 [Rime 小狼毫 0.17.4](https://github.com/rime/weasel)（GPLv3）深度定制。

五笔优先、拼音兜底；英文回车直上屏；候选词后面带英文注释，`Ctrl+数字` 直接上屏按命名风格转换过的英文；
词库内置 500+ 条 UE / 游戏开发术语。

**只想用，不想看代码** → 到 [Releases](../../releases) 下载 `幻熊输入法-1.0-安装程序.exe`，双击，一路下一步。

---

## 它解决什么

用 Rime 打 UE 项目时，下面这些事每次都要手动折腾。这个项目把它们固化成默认行为：

| 痛点 | 这里的做法 |
| --- | --- |
| 打 `blueprint` 想直接出 `Blueprint` | 有英文注释的候选，`Ctrl+数字` 直接上屏，命名风格可选 `PascalCase` / `原样` / `snake_case` / `lowercase` |
| 想说「层次实例化静态网格」，五笔要一个字一个字敲 | 内置 UE 官方中文术语表，常用术语直接出词，权重 9999 |
| 打一半想切英文 | 回车直接把已敲的编码原样上屏（`commit_raw_on_return`） |
| 五笔打不出某个字，切输入法 | 五笔拼音混输，打不出直接敲拼音 |
| 输入法吃掉 `Shift` | 左右 Shift 全部 `noop`，Shift+方向键选字、Shift+符号全不受影响 |
| 翻页要按 `PageDown` | `-` / `=` 翻页，`;` `'` 选第 2、3 个候选 |
| 候选框丑、字重飘 | Noto Sans SC + 真阴影 + 分层圆角，4 套配色（晴蓝 / 素白 / 夜墨 / 云青） |
| 进编辑器就被输入法缠住 | `UnrealEditor.exe` / `Blender` / `cmd` / `VSCode` 等自动进英文模式（`app_options`） |

## 配置与界面

`src/settings/` 是一个独立设置面板（Python + pywebview，单文件 HTML 界面，无外部依赖、不联网）。
可以改：配色主题、字号、每页候选数（3/5/7/9/10）、候选窗宽度、简繁、标点、中英上屏风格、UE 词表开关，
以及一键「应用并部署」。

Rime 配置全在 `payload/rime/` 下，都是标准的 `.custom.yaml` 补丁 + Lua 过滤器，不魔改内核，可以单独摘出来用。

## 目录结构

```
HuanxiongIME/
├── build.py                   一键构建（payload / settings / installer）
├── HuanxiongSettings.spec     PyInstaller 打包描述（设置面板）
├── src/settings/              设置面板源码
│   ├── app.py                 pywebview 原生窗口 + 对外 API
│   ├── settings.py            读写 Rime 补丁 / 部署 / 导入导出（纯标准库）
│   └── ui.html                界面（单文件）
├── payload/                   构建输入（安装包素材）
│   ├── rime/                  随包分发的 Rime 用户配置
│   │   ├── default.custom.yaml    方案列表、中英切换键、应用白名单、翻页快捷键
│   │   ├── weasel.custom.yaml     候选窗皮肤（字体 / 阴影 / 圆角 / 4 套配色）
│   │   ├── *.schema.yaml          五笔86 极点、五笔拼音混输、简体拼音、大写数字
│   │   ├── *.dict.yaml            码表
│   │   ├── rime.lua               自写过滤器：英文注释、Ctrl+数字上屏、回车上原文、日期、计算器
│   │   ├── ue_terms.lua           手写 UE / 游戏开发术语中英对照（优先级最高）
│   │   ├── zh_en_dict.lua         73,613 条自动生成中英对照（CC-CEDICT）
│   │   └── custom_phrase.txt      自定义短语（UE 缩写 → 全称）
│   ├── program/               小狼毫 0.17.4 运行时（已品牌化）— 不进版本库
│   ├── fonts/                 Noto Sans SC — 不进版本库
│   └── settings/              PyInstaller 产物 — 不进版本库
├── installer/setup.iss        Inno Setup 脚本（注册输入法 / 装字体 / 卸载）
├── docs/使用说明.txt          随安装包一起装给用户
└── tools/                     维护与改造工具
```

## 从源码构建

需要 **Windows x64**、**Python 3.10+**、[Inno Setup 6](https://jrsoftware.org/isdl.php)。

```
python -m venv .venv
.venv\Scripts\pip install pyinstaller pywebview pyyaml
```

前置素材（因为许可与体积原因不进 Git）：

```
1. 装上游 Weasel 0.17.4 安装包      → 提供 payload/program 的来源
2. 下载 Noto Sans SC 可变字体        → 放进 payload/fonts/NotoSansSC-VF.ttf
3. python build.py payload           → 从本机安装目录快照运行时与配置
```

出包：

```
python build.py all
```

| 命令 | 作用 |
| --- | --- |
| `python build.py payload` | 从本机 `C:\Program Files\Rime\weasel-0.17.4`、`%APPDATA%\Rime` 快照素材 |
| `python build.py settings` | PyInstaller 打包设置面板 → `payload/settings` |
| `python build.py installer` | Inno Setup 编译 → `dist/幻熊输入法-1.0-安装程序.exe` |

**注意**：`payload` 是「快照你当前这一套」的意思，不是从 `payload/rime/` 拷贝。所以改完配置要先在本机部署生效，
再跑 `build.py payload`，产出的安装包才会带上你的改动。

## tools

| 脚本 | 用途 |
| --- | --- |
| `gen_ue_dict.py` | 把 UE / 游戏开发术语补进五笔 + 拼音码表（幂等，重复跑不会重复插） |
| `ime_registry.py dump/restore` | 转储 / 恢复输入法在注册表里的全部注册信息（排查「语言栏没有它」、卸载前备份） |
| `ime_registry_baseline.json` | 一份正常状态的注册表快照，出问题可 `restore` 回滚（各机器路径不同，仅供参考） |
| `full_remove.py` | 彻底清除：卸载 + 删目录 + 系统 dll + 注册表 + 快捷方式，用于模拟「新电脑」（需管理员，`--dry-run` 演练） |
| `restore.py` | 一键还原：重装 + 覆盖备份配置 + 部署 + 起服务（需管理员，`--config-only` 只恢复词频短语） |
| `caretfix.py` | 候选框跟随鼠标的进程外兜底（见「已知问题」） |
| `legacy/` | 上游二进制的品牌化 / 托盘菜单裁剪等一次性改造脚本，只有换上游版本时才需要重跑 |

## 安装包做了什么

1. 解压运行时到 `C:\Program Files\Rime\weasel-0.17.4`
2. 装 `Noto Sans SC` 字体（已有则跳过）
3. 首次安装时把配置铺到 `%APPDATA%\Rime`（**已有配置不覆盖**，且 `uninsneveruninstall`）
4. 调 `WeaselSetup.exe /s` 注册 TSF 输入法（写 CLSID / CTF TIP / 语言列表，复制 dll 到 System32 & SysWOW64）
5. 调部署器 `/deploy` 编译词库，启动 `WeaselServer.exe`
6. 桌面 / 开始菜单快捷方式，卸载项写进「设置 → 应用」

卸载会清掉注册表和系统目录 DLL，**用户词频与配置保留**。

## 已知问题

- **在 UE 编辑器里，候选框不跟随光标**，会停在上一处位置。
  根因在 UE 侧：`FTextStoreACP::GetTextExt` 返回 `(0,0)`，而 Weasel 的
  `CGetTextExtentEditSession` 见到 `(0,0)` 就直接丢弃坐标更新（上游 [rime/weasel#1023](https://github.com/rime/weasel/issues/1023)）。
  Slate 自绘光标不走 `SetCaretPos`，所以 IMM 兼容模式也救不了。
  `tools/caretfix.py` 是进程外兜底方案（让候选框跟鼠标），不随安装包分发，想用自己起。
- **输入到一半按 `Ctrl+空格` 会清空未上屏的编码**，上不了屏。这是 Windows 的系统热键
  （`IME_CHOTKEY_IME_NONIME_TOGGLE`），在 TSF 层就被截走，输入法收不到事件，配置层面无解。
  `ascii_composer.switch_key` 只接受**不带修饰键的单键**，组合键进不去。
- **安装包没有代码签名**，首次运行会弹 SmartScreen「Windows 已保护你的电脑」，
  走「更多信息 → 仍要运行」。杀软也可能拦，加白名单即可。
- 装完需要 `Win+空格` 切一次；个别机器要注销一次才刷新语言栏。

## 许可

**GPL-3.0**，见 [`LICENSE`](LICENSE)。因为安装包捆绑了 GPLv3 的 Weasel 内核，整个分发物都在 GPLv3 之下。

第三方组件、以及本项目对上游二进制所做的修改（GPLv3 §5 要求的修改声明），见 [`THIRD_PARTY.md`](THIRD_PARTY.md)。

上游：[Rime 小狼毫 / Weasel](https://github.com/rime/weasel) · [librime](https://github.com/rime/librime) ·
词库：[极点五笔86](https://github.com/KyleBing/rime-wubi86-jidian)、CC-CEDICT ·
字体：[Noto Sans SC](https://fonts.google.com/noto/specimen/Noto+Sans+SC) (OFL 1.1)

作者：DorpBear
