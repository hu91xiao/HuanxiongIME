# -*- coding: utf-8 -*-
"""
幻熊输入法设置 —— 核心逻辑层（纯标准库，不联网）。

职责：读写 Rime 用户目录里的 .custom.yaml 补丁文件，调用原版
WeaselDeployer.exe /deploy 重新部署，再重启 WeaselServer 让配置立刻生效。
界面在 app.py + ui.html，这里只管配置怎么读写。
"""
import os
import re
import shutil
import subprocess
import time

HERE = os.path.dirname(os.path.abspath(__file__))


def known_folder(csidl):
    """通过 Windows API 取特殊目录，环境变量缺失时（某些启动方式下会缺）兜底"""
    try:
        import ctypes
        buf = ctypes.create_unicode_buffer(300)
        if ctypes.windll.shell32.SHGetFolderPathW(None, csidl, None, 0, buf) == 0:
            return buf.value
    except Exception:                                          # noqa: BLE001
        pass
    return ""


CSIDL_APPDATA = 0x001A
CSIDL_LOCAL_APPDATA = 0x001C
CSIDL_DESKTOP = 0x0010
CSIDL_PROGRAMS = 0x0002

APPDATA = os.environ.get("APPDATA") or known_folder(CSIDL_APPDATA)
LOCALAPPDATA = os.environ.get("LOCALAPPDATA") or known_folder(CSIDL_LOCAL_APPDATA)
DESKTOP = known_folder(CSIDL_DESKTOP)
STARTMENU_PROGRAMS = known_folder(CSIDL_PROGRAMS)

RIME = os.path.join(APPDATA or os.path.expanduser("~"), "Rime")
BACKUP_DIR = os.path.join(LOCALAPPDATA or HERE, "RimeSettings", "backup")

WEASEL_CANDIDATES = [
    r"C:\Program Files\Rime\weasel-0.17.4",
    r"C:\Program Files (x86)\Rime\weasel-0.17.4",
    r"C:\Program Files\Rime",
    r"C:\Program Files (x86)\Rime",
]


def find_weasel():
    """在各常见位置与任意 weasel-x.y.z 子目录里找 WeaselDeployer.exe"""
    cands = []
    for base in (r"C:\Program Files\Rime", r"C:\Program Files (x86)\Rime"):
        if os.path.isdir(base):
            try:
                subs = sorted((d for d in os.listdir(base) if d.lower().startswith("weasel")),
                              reverse=True)
            except OSError:
                subs = []
            cands += [os.path.join(base, d) for d in subs]
            cands.append(base)
    cands += WEASEL_CANDIDATES
    seen = set()
    for d in cands:
        if d in seen:
            continue
        seen.add(d)
        if os.path.isfile(os.path.join(d, "WeaselDeployer.exe")):
            return d
    return None


WEASEL_DIR = find_weasel()

F_MIXED = os.path.join(RIME, "wubi86_jidian_pinyin.custom.yaml")
F_DEFAULT = os.path.join(RIME, "default.custom.yaml")
F_WEASEL = os.path.join(RIME, "weasel.custom.yaml")
F_LUA = os.path.join(RIME, "rime.lua")

STATE_KEYS = [
    "mode", "iq", "return_raw", "ctrl_en", "comment_en", "commit_style",
    "fluid", "pinyin_userdict", "page_size", "font_point", "scheme",
    "horizontal", "round_corner", "candidate_spacing", "paging",
    "shift_key", "caps_lock", "num_select",
]


# ----------------------------------------------------------------- 基础读写
def read(p):
    if not os.path.isfile(p):
        return ""
    with open(p, "r", encoding="utf-8", errors="replace") as f:
        return f.read()


def write(p, s):
    with open(p, "w", encoding="utf-8", newline="\n") as f:
        f.write(s)


def backup():
    if not os.path.isdir(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)
    stamp = time.strftime("%Y%m%d-%H%M%S")
    dst = os.path.join(BACKUP_DIR, stamp)
    os.makedirs(dst, exist_ok=True)
    for p in (F_MIXED, F_DEFAULT, F_WEASEL, F_LUA):
        if os.path.isfile(p):
            shutil.copy2(p, os.path.join(dst, os.path.basename(p)))
    # 只留最近 10 份
    olds = sorted(d for d in os.listdir(BACKUP_DIR)
                  if os.path.isdir(os.path.join(BACKUP_DIR, d)))
    for d in olds[:-10]:
        shutil.rmtree(os.path.join(BACKUP_DIR, d), ignore_errors=True)
    return dst


def block_lines(text, key, indent=2):
    """取出 `  key:` 下面缩进更深的子行"""
    lines = text.splitlines()
    child = " " * (indent + 2)
    out, inside = [], False
    for ln in lines:
        if not inside:
            if ln.strip() == key + ":":
                inside = True
            continue
        if ln.startswith(child):
            out.append(ln)
        elif ln.strip() == "":
            continue
        else:
            break
    return out


# ----------------------------------------------------------------- 读取状态
def read_state():
    mixed, default, weasel, lua = read(F_MIXED), read(F_DEFAULT), read(F_WEASEL), read(F_LUA)
    st = {}

    tr = "\n".join(block_lines(mixed, "engine/translators"))
    has_py = "script_translator@pinyin" in tr
    has_wb = re.search(r"(?m)^\s*-\s*table_translator\s*(#.*)?$", tr) is not None
    st["mode"] = "mixed" if (has_py and has_wb) else ("wubi" if has_wb else "pinyin")

    m = re.search(r"translator/initial_quality:\s*([0-9.]+)", mixed)
    st["iq"] = float(m.group(1)) if m else 0.0

    proc = "\n".join(block_lines(mixed, "engine/processors"))
    st["return_raw"] = "commit_raw_on_return" in proc
    st["ctrl_en"] = "commit_en_on_ctrl_num" in proc
    st["fluid"] = re.search(r"(?m)^\s*-\s*fluid_editor\s*$", proc) is not None

    filt = "\n".join(block_lines(mixed, "engine/filters"))
    st["comment_en"] = "en_comment_filter" in filt
    st["pinyin_userdict"] = re.search(r"enable_user_dict:\s*true", mixed) is not None

    m = re.search(r'EN_COMMIT_STYLE\s*=\s*"(\w+)"', lua)
    st["commit_style"] = m.group(1) if m else "pascal"

    m = re.search(r"page_size:\s*(\d+)", default)
    st["page_size"] = int(m.group(1)) if m else 9

    m = re.search(r"switch_key:\s*\{([^}]*)\}", default)
    sw = {}
    if m:
        for part in m.group(1).split(","):
            if ":" in part:
                k, v = part.split(":", 1)
                sw[k.strip()] = v.strip()
    st["shift_key"] = sw.get("Shift_L", "noop")
    st["caps_lock"] = sw.get("Caps_Lock", "commit_code")

    st["num_select"] = "accept: semicolon" in default
    st["paging"] = "minus" if re.search(r"accept:\s*minus", default) else "bracket"

    m = re.search(r'"style/color_scheme":\s*(\w+)', weasel) or re.search(r"color_scheme:\s*(\w+)", weasel)
    st["scheme"] = m.group(1) if m else "QingLan"

    m = re.search(r"(?m)^\s*font_point:\s*(\d+)", weasel)
    st["font_point"] = int(m.group(1)) if m else 16

    st["horizontal"] = not re.search(r"horizontal:\s*false", weasel)

    m = re.search(r"round_corner:\s*(\d+)", weasel)
    st["round_corner"] = int(m.group(1)) if m else 14
    m = re.search(r"candidate_spacing:\s*(\d+)", weasel)
    st["candidate_spacing"] = int(m.group(1)) if m else 20

    for k in STATE_KEYS:
        st.setdefault(k, None)
    return st


# ----------------------------------------------------------------- 写入三个补丁
def build_mixed(st):
    """整份重写 wubi86_jidian_pinyin.custom.yaml（这个文件由设置面板接管）"""
    mode = st["mode"]
    L = [
        "patch:",
        "# 本文件由「幻熊输入法设置」生成，手工改动会在下次「应用并部署」时被覆盖。",
        "# 手工修改会在下次点「应用并部署」时被覆盖；要长期保留请改设置面板。",
        "  engine/translators:",
        "    - punct_translator",
    ]
    if mode in ("mixed", "pinyin"):
        L.append("    - script_translator@pinyin   # 拼音")
    if mode in ("mixed", "wubi"):
        L.append("    - table_translator           # 五笔（主用）")
    L += [
        "    - table_translator@custom_phrase",
        "  speller:",
        "    delimiter: \"'\"              # 不含空格，否则拼音音节间会自动插空格",
        "  pinyin:",
        "    initial_quality: 0             # 拼音候选整体压后",
        "    dictionary: pinyin_simp",
        "    enable_user_dict: %s" % ("true" if st["pinyin_userdict"] else "false"),
        "    user_dict: wubi86_jidian_pinyin_pinyin",
        "    db_class: userdb",
        "    preedit_format:",
        '      - "xform/([nl])v/$1ü/"',
        '      - "xform/([nl])ue/$1üe/"',
        '      - "xform/([jqxy])v/$1u/"',
        "      - \"xform/'//\"             # 音节分隔符不显示，保持连写（虚幻里不能有空格）",
        "  custom_phrase:",
        '    dictionary: ""',
        "    user_dict: custom_phrase",
        "    db_class: stabledb",
        "    enable_completion: false",
        "    enable_sentence: false",
        "    initial_quality: -100",
        "  engine/processors:",
    ]
    if st["ctrl_en"]:
        L.append("    - lua_processor@commit_en_on_ctrl_num   # Ctrl+数字 上屏英文")
    if st["return_raw"]:
        L.append("    - lua_processor@commit_raw_on_return    # 回车直接上码")
    L += [
        "    - ascii_composer",
        "    - recognizer",
        "    - key_binder",
        "    - speller",
        "    - punctuator",
        "    - selector",
        "    - navigator",
        "    - %s" % ("fluid_editor" if st["fluid"] else "express_editor"),
    ]
    if st["comment_en"]:
        L += [
            "  engine/filters:",
            "    - lua_filter@en_comment_filter          # 候选后加英文注释",
        ]
    L += [
        "  # 五笔候选整体排在拼音前面。必须用子键路径，写成 translator: 会把 dictionary 覆盖掉",
        "  translator/initial_quality: %s" % fmt_num(st["iq"]),
        "",
    ]
    return "\n".join(L)


def fmt_num(v):
    v = float(v)
    return str(int(v)) if v == int(v) else ("%.1f" % v)


def patch_default(text, st):
    text = re.sub(r"(?m)^(\s*)page_size:\s*\d+.*$",
                  lambda m: "%spage_size: %d" % (m.group(1), st["page_size"]), text, count=1)

    sw = "{Caps_Lock: %s, Control_L: noop, Control_R: noop, Shift_L: %s, Shift_R: %s}" % (
        st["caps_lock"], st["shift_key"], st["shift_key"])
    text = re.sub(r"(?m)^(\s*)switch_key:\s*\{[^}]*\}",
                  lambda m: "%sswitch_key: %s" % (m.group(1), sw), text, count=1)

    m = re.search(r"(?m)^(\s*)bindings:\s*\[(.*)\]\s*$", text)
    if m:
        items = re.findall(r"\{[^{}]*\}", m.group(2))
        rest = []
        for it in items:
            if re.search(r"accept:\s*(minus|equal|bracketleft|bracketright)", it):
                continue                      # 翻页键固定重建
            if re.search(r"accept:\s*(semicolon|apostrophe)", it):
                continue                      # 分号引号也固定重建
            rest.append(it)
        head = []
        if st["num_select"]:
            head += ["{accept: semicolon, send: 2, when: has_menu}",
                     "{accept: apostrophe, send: 3, when: has_menu}"]
        if st["paging"] == "minus":
            head += ["{accept: minus, send: Page_Up, when: has_menu}",
                     "{accept: equal, send: Page_Down, when: has_menu}"]
        else:
            head += ["{accept: bracketleft, send: Page_Up, when: has_menu}",
                     "{accept: bracketright, send: Page_Down, when: has_menu}"]
        text = text[:m.start()] + "%sbindings: [%s]" % (m.group(1), ", ".join(head + rest)) + text[m.end():]
    return text


def patch_weasel(text, st):
    fp = int(st["font_point"])
    text = re.sub(r"(?m)^(\s*)font_point:\s*\d+",
                  lambda m: "%sfont_point: %d" % (m.group(1), fp), text)
    text = re.sub(r"(?m)^(\s*)comment_font_point:\s*\d+",
                  lambda m: "%scomment_font_point: %d" % (m.group(1), max(11, fp - 3)), text)
    text = re.sub(r'("style/color_scheme":\s*)\w+', lambda m: m.group(1) + st["scheme"], text)
    text = re.sub(r"(?m)^(\s*)color_scheme:\s*\w+", lambda m: "%scolor_scheme: %s" % (m.group(1), st["scheme"]),
                  text, count=1)
    text = re.sub(r"horizontal:\s*(true|false)", "horizontal: %s" % ("true" if st["horizontal"] else "false"), text)
    text = re.sub(r"round_corner:\s*\d+", "round_corner: %d" % int(st["round_corner"]), text)
    text = re.sub(r"candidate_spacing:\s*\d+", "candidate_spacing: %d" % int(st["candidate_spacing"]), text)
    return text


def patch_lua(text, st):
    text = re.sub(r'(?m)^local EN_COMMIT_STYLE\s*=\s*"\w+"',
                  'local EN_COMMIT_STYLE = "%s"' % st["commit_style"], text, count=1)
    return text


# ----------------------------------------------------------------- 部署
def run_deploy():
    if not WEASEL_DIR:
        return False, "找不到 WeaselDeployer.exe，请确认幻熊输入法安装目录"
    # 注意：本程序可能被改名成 WeaselDeployer.exe 顶替官方那个（菜单「输入法设定」指向它），
    # 所以真正执行部署时要优先用原版 WeaselDeployer.orig.exe，否则会自己调自己
    exe = os.path.join(WEASEL_DIR, "WeaselDeployer.orig.exe")
    if not os.path.isfile(exe):
        exe = os.path.join(WEASEL_DIR, "WeaselDeployer.exe")
    try:
        p = subprocess.run([exe, "/deploy"], cwd=WEASEL_DIR,
                           capture_output=True, timeout=300)
    except Exception as e:                                    # noqa: BLE001
        return False, "部署失败：%s" % e
    if p.returncode != 0:
        return False, "部署返回码 %d" % p.returncode
    return True, "部署完成"


def restart_server():
    if not WEASEL_DIR:
        return False, "找不到 WeaselServer.exe"
    subprocess.run(["taskkill", "/IM", "WeaselServer.exe", "/F"], capture_output=True)
    time.sleep(1.2)
    exe = os.path.join(WEASEL_DIR, "WeaselServer.exe")
    flags = 0x00000008 | 0x00000200          # DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP
    try:
        subprocess.Popen([exe], cwd=WEASEL_DIR, creationflags=flags, close_fds=True)
    except Exception as e:                                    # noqa: BLE001
        return False, "重启服务失败：%s" % e
    return True, "服务已重启"


# ----------------------------------------------------------------- 配置包（给别的电脑用）
EXPORT_SKIP = {"installation.yaml", "user.yaml"}       # 记录机器状态的，不带走


def bundle_files():
    out = []
    if not os.path.isdir(RIME):
        return out
    for name in sorted(os.listdir(RIME)):
        low = name.lower()
        if not low.endswith((".yaml", ".txt", ".lua")):
            continue
        if low in EXPORT_SKIP:
            continue
        p = os.path.join(RIME, name)
        if os.path.isfile(p):
            out.append(p)
    return out


def export_bundle(dst_zip=None):
    """把 Rime 目录里的方案/词库/lua/补丁打包成一个 zip，方便换电脑用"""
    import zipfile
    files = bundle_files()
    if not files:
        return False, "Rime 目录里没找到可导出的配置：%s" % RIME, None
    if not dst_zip:
        desk = DESKTOP or os.path.join(os.path.expanduser("~"), "Desktop")
        if not os.path.isdir(desk):
            desk = os.path.expanduser("~")
        dst_zip = os.path.join(desk, "Rime配置-%s.zip" % time.strftime("%Y%m%d-%H%M"))
    os.makedirs(os.path.dirname(dst_zip) or ".", exist_ok=True)
    with zipfile.ZipFile(dst_zip, "w", zipfile.ZIP_DEFLATED) as z:
        for p in files:
            z.write(p, os.path.basename(p))
        z.writestr("导出说明.txt",
                   "幻熊输入法配置包\r\n导出时间：%s\r\n来源目录：%s\r\n\r\n"
                   "用法：在目标电脑上打开「幻熊输入法设置」→ 短语与维护 → 导入配置包，"
                   "选这个 zip，程序会自动备份并部署。\r\n"
                   % (time.strftime("%Y-%m-%d %H:%M:%S"), RIME))
    size = os.path.getsize(dst_zip) / 1024.0 / 1024.0
    return True, "已导出 %d 个文件到 %s（%.1f MB）" % (len(files), dst_zip, size), dst_zip


def import_bundle(src_zip):
    """把配置包解回 Rime 目录（先自动备份），然后部署"""
    import zipfile
    if not src_zip or not os.path.isfile(src_zip):
        return False, "找不到配置包：%s" % src_zip
    try:
        z = zipfile.ZipFile(src_zip)
    except Exception as e:                                     # noqa: BLE001
        return False, "压缩包打不开：%s" % e
    os.makedirs(RIME, exist_ok=True)
    backup()
    n = 0
    with z:
        for info in z.infolist():
            name = os.path.basename(info.filename)
            if not name or info.is_dir() or name.lower() in EXPORT_SKIP:
                continue
            if not name.lower().endswith((".yaml", ".txt", ".lua")):
                continue
            with z.open(info) as src, open(os.path.join(RIME, name), "wb") as dst:
                dst.write(src.read())
            n += 1
    if n == 0:
        return False, "配置包里没有可用的配置文件"
    ok, msg = run_deploy()
    if ok:
        restart_server()
    return True, "已导入 %d 个文件%s" % (n, "，部署完成，服务已重启" if ok else "，但部署失败：" + msg)


def open_target(what):
    target = {
        "phrase": os.path.join(RIME, "custom_phrase.txt"),
        "rime": RIME,
        "backup": BACKUP_DIR,
        "lua": F_LUA,
    }.get(what)
    if target and os.path.exists(target):
        os.startfile(target)                                   # noqa: S606
        return True, "已打开"
    return False, "路径不存在：%s" % (target or what)


def apply_settings(payload):
    st = {k: payload.get(k) for k in STATE_KEYS}
    # 归一化
    st["mode"] = st.get("mode") or "mixed"
    st["iq"] = float(st.get("iq") or 0)
    st["page_size"] = int(st.get("page_size") or 9)
    st["font_point"] = int(st.get("font_point") or 16)
    st["round_corner"] = int(st.get("round_corner") if st.get("round_corner") is not None else 14)
    st["candidate_spacing"] = int(st.get("candidate_spacing") if st.get("candidate_spacing") is not None else 20)
    st["scheme"] = st.get("scheme") or "QingLan"
    st["paging"] = st.get("paging") or "minus"
    st["shift_key"] = st.get("shift_key") or "noop"
    st["caps_lock"] = st.get("caps_lock") or "commit_code"
    st["commit_style"] = st.get("commit_style") or "pascal"
    for k in ("return_raw", "ctrl_en", "comment_en", "fluid", "pinyin_userdict", "horizontal", "num_select"):
        st[k] = bool(st.get(k))

    backup()
    write(F_MIXED, build_mixed(st))
    write(F_DEFAULT, patch_default(read(F_DEFAULT), st))
    write(F_WEASEL, patch_weasel(read(F_WEASEL), st))
    write(F_LUA, patch_lua(read(F_LUA), st))

    ok, msg = run_deploy()
    if not ok:
        return msg + "（配置已写入，但部署没成功，请再点一次「应用并部署」）"
    restart_server()
    return "已保存并部署，服务已重启。打个字就能看到效果。"


