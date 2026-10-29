# -*- coding: utf-8 -*-
"""
把托盘右键菜单里的「重新部署 / Deploy」去掉，三个语言分支全部重写。

之前的补丁只写了 0x0409（英文）一份，而 WeaselServer.exe 的 #105 菜单里还有
0x0804（简体，原版 15 项）和 0x0404（繁体）。中文系统加载的是 0x0804，
所以「重新部署」一直在。

现在：MENU 105/108/109 × 语言 0x0409/0x0804/0x0404 全部写成同样的 4 项
      输入法设定 / 用户文件夹 / ── / 退出

用法：
  python menu4.py            改（需要管理员：Program Files + System32）
  python menu4.py --dry      只解析不改
"""
import os
import struct
import subprocess
import sys
import time

import winres as W

WEASEL = r"C:\Program Files\Rime\weasel-0.17.4"
SYSTEM32 = r"C:\Windows\System32"
SYSWOW64 = r"C:\Windows\SysWOW64"

MENU_IDS = (105, 108, 109)
LANGS = (0x0409, 0x0804, 0x0404)

# 每项：(id, 文本)  文本按语言给
TEXT = {
    0x0409: ("Settings (&S)", "User folder (&C)", "Exit (&Q)"),
    0x0804: ("输入法设定 (&S)", "用户文件夹 (&C)", "退出 (&Q)"),
    0x0404: ("輸入法設定 (&S)", "用戶文件夾 (&C)", "退出 (&Q)"),
}
ITEM_IDS = (40008, 40007, 40001)   # 设定 / 用户文件夹 / 退出


def items_for(lang):
    a, b, c = TEXT[lang]
    return [(ITEM_IDS[0], a), (ITEM_IDS[1], b), None, (ITEM_IDS[2], c)]


def parse_menu(b):
    hdrlen = struct.unpack_from("<H", b, 0)[0]
    off = hdrlen + 2
    out = []
    while off + 4 <= len(b):
        flags, mid = struct.unpack_from("<HH", b, off)
        off += 4
        txt = ""
        if not (flags & 0x0010):
            s = []
            while True:
                c = b[off:off + 2]
                off += 2
                if c == b"\x00\x00":
                    break
                s.append(c)
            txt = b"".join(s).decode("utf-16-le", "replace")
        out.append((mid, txt))
        if flags & 0x0080:
            break
    return out


LOG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "menu4.log")
LINES = []


def log(msg):
    LINES.append(str(msg))
    print(msg)


def show(path):
    data, res = W.pe_resources(path)
    for p, off, size, cp in res:
        if p[0] != W.RT_MENU:
            continue
        log("   #%s lang=%s -> %s" % (p[1], hex(p[2]),
            [t or "(分隔)" for _, t in parse_menu(data[off:off + size])]))


def patch(path, ids=MENU_IDS):
    with W.ResFile(path) as r:
        for mid in ids:
            for lang in LANGS:
                r.update(W._ptr(W.RT_MENU), W._ptr(mid), lang,
                         W.menu_blob(items_for(lang)))


def main():
    dry = "--dry" in sys.argv
    targets = [
        os.path.join(WEASEL, "WeaselServer.exe"),
        os.path.join(WEASEL, "weaselx64.dll"),
        os.path.join(WEASEL, "weasel.dll"),
        os.path.join(SYSTEM32, "weasel.dll"),
        os.path.join(SYSWOW64, "weasel.dll"),
    ]
    try:
        if dry:
            for t in targets:
                log("== " + t)
                show(t)
            return 0

        log("== 停服务")
        subprocess.run([os.path.join(WEASEL, "WeaselServer.exe"), "/q"],
                       capture_output=True, timeout=20, cwd=WEASEL)
        time.sleep(1.0)
        subprocess.run(["taskkill", "/IM", "WeaselServer.exe", "/F"],
                       capture_output=True)
        time.sleep(0.8)

        log("== 改写菜单")
        for t in targets:
            if not os.path.exists(t):
                log("  跳过（不存在） " + t)
                continue
            try:
                patch(t)
                log("  OK   %s  %s" % (os.path.basename(t), t))
            except Exception as e:
                log("  失败 %s  %s -> %r" % (os.path.basename(t), t, e))

        log("== 校验")
        for t in targets:
            if not os.path.exists(t):
                continue
            log("== " + os.path.basename(t))
            try:
                show(t)
            except Exception as e:
                log("   解析失败 %r" % (e,))

        log("== 起服务")
        subprocess.Popen([os.path.join(WEASEL, "WeaselServer.exe")], cwd=WEASEL,
                         creationflags=0x00000008 | 0x00000200, close_fds=True)
        time.sleep(2.5)
        out = subprocess.run(["tasklist", "/FI", "IMAGENAME eq WeaselServer.exe"],
                             capture_output=True, text=True, errors="replace").stdout
        log("  " + ("WeaselServer 已在运行" if "WeaselServer.exe" in out else "没起来！"))
        return 0
    finally:
        try:
            with open(LOG, "w", encoding="utf-8") as f:
                f.write("\n".join(LINES))
        except Exception:
            pass


if __name__ == "__main__":
    sys.exit(main())
