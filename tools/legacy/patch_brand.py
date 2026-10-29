# -*- coding: utf-8 -*-
"""
把 Rime 小狼毫改造成「幻熊输入法」：图标 + 版本信息 + 托盘菜单 + 掐掉自动更新。

用法：
    python rebrand.py --test      只做 System32 副本，验证效果
    python rebrand.py --all       全部文件（Program Files 里能改的直接改，改不了的登记开机替换）
    python rebrand.py --restore   撤销（把 .bak_brand 还原回去）
"""
import ctypes
import ctypes.wintypes as wt
import os
import shutil
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import winres as W

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(os.path.dirname(_HERE))

ICON_DIR = os.path.join(_ROOT, "assets", "icons")
SWAP_DIR = os.path.join(os.environ.get("TEMP", "."), "_huanxiong_swapll")
WEASEL = os.environ.get("WEASEL_DIR", r"C:\Program Files\Rime\weasel-0.17.4")
SYSTEM32 = r"C:\Windows\System32"
SYSWOW64 = r"C:\Windows\SysWOW64"

BRAND_ZH = "幻熊输入法"
BRAND_TW = "幻熊輸入法"
BRAND_EN = "Huanxiong IME"
COMPANY = "DorpBear"
COPY_ZH = "DorpBear · 基于 Rime 小狼毫 0.17.4（GPLv3）"
COPY_TW = "DorpBear · 基於 Rime 小狼毫 0.17.4（GPLv3）"
COPY_EN = "DorpBear (based on Rime Weasel 0.17.4, GPLv3)"

# 托盘菜单：精简成 4 项（去掉「重新部署」）
# 注意：WeaselServer.exe 的 #105 有三个语言分支（0x409 英文 / 0x804 简体 / 0x404 繁体），
# 中文系统加载的是 0x804——只写 0x409 的话中文菜单仍是原版 15 项。
def _tray_items(lang):
    if lang == 0x0409:
        return [(40008, "Settings (&S)"), (40007, "User folder (&C)"), None,
                (40001, "Exit (&Q)")]
    if lang == 0x0404:
        return [(40008, "輸入法設定 (&S)"), (40007, "用戶文件夾 (&C)"), None,
                (40001, "退出 (&Q)")]
    return [(40008, "输入法设定 (&S)"), (40007, "用户文件夹 (&C)"), None,
            (40001, "退出 (&Q)")]


MENU_LANGS = (0x0409, 0x0804, 0x0404)
MENUS = {mid: {lang: _tray_items(lang) for lang in MENU_LANGS}
         for mid in (105, 108, 109)}

ICONS = {}


def icons(v):
    if v not in ICONS:
        ICONS[v] = W.load_icon_set(ICON_DIR, v)
    return ICONS[v]


def vtables(fd_zh, fd_tw, fd_en, tw_is_zh=False):
    def mk(brand, copy_, fd):
        d = {"ProductName": brand, "CompanyName": COMPANY, "LegalCopyright": copy_}
        d["Comments"] = "幻熊输入法 · 虚幻引擎开发者专用"
        if fd:
            d["FileDescription"] = fd
        return d
    tw = mk(BRAND_ZH, COPY_ZH, fd_zh) if tw_is_zh else mk(BRAND_TW, COPY_TW, fd_tw)
    return {
        "080404b0": mk(BRAND_ZH, COPY_ZH, fd_zh),
        "040404b0": tw,
        "040904b0": mk(BRAND_EN, COPY_EN, fd_en),
        "*": {"ProductName": BRAND_ZH, "CompanyName": COMPANY, "LegalCopyright": COPY_ZH},
    }


# 每个文件：图标组映射 + 三语 FileDescription
JOBS = [
    dict(name="weasel64.dll", src=os.path.join(SYSTEM32, "weasel.dll"),
         groups={100: "main", 101: "en", 102: "zh", 103: "busy"},
         menus=True, appcast=False, swap=True,
         fd=("幻熊输入法 文本服务", "幻熊輸入法 文字服務", "Huanxiong IME Text Service")),
    dict(name="weasel32.dll", src=os.path.join(SYSWOW64, "weasel.dll"),
         groups={100: "main", 101: "en", 102: "zh", 103: "busy"},
         menus=True, appcast=False, swap=True,
         fd=("幻熊输入法 文本服务", "幻熊輸入法 文字服務", "Huanxiong IME Text Service")),
    dict(name="pf_weaselx64.dll", src=os.path.join(WEASEL, "weaselx64.dll"),
         groups={100: "main", 101: "en", 102: "zh", 103: "busy"},
         menus=True, appcast=False, swap=False,
         fd=("幻熊输入法 文本服务", "幻熊輸入法 文字服務", "Huanxiong IME Text Service")),
    dict(name="pf_weasel.dll", src=os.path.join(WEASEL, "weasel.dll"),
         groups={100: "main", 101: "en", 102: "zh", 103: "busy"},
         menus=True, appcast=False, swap=False,
         fd=("幻熊输入法 文本服务", "幻熊輸入法 文字服務", "Huanxiong IME Text Service")),
    dict(name="WeaselServer.exe", src=os.path.join(WEASEL, "WeaselServer.exe"),
         groups={100: "main", 101: "en", 102: "zh", 103: "busy"},
         menus=True, appcast=True, swap=False,
         fd=("幻熊输入法 算法服务", "幻熊輸入法 演算法服務", "Huanxiong IME Server")),
    dict(name="weaselx64.ime", src=os.path.join(WEASEL, "weaselx64.ime"),
         groups={101: "main"}, menus=False, appcast=False, swap=False, tw_is_zh=True,
         fd=("幻熊输入法 64 位组件", "幻熊輸入法 64 位元組件", "Huanxiong IME x64")),
    dict(name="weasel.ime", src=os.path.join(WEASEL, "weasel.ime"),
         groups={101: "main"}, menus=False, appcast=False, swap=False, tw_is_zh=True,
         fd=("幻熊输入法 32 位组件", "幻熊輸入法 32 位元組件", "Huanxiong IME x86")),
    dict(name="WeaselSetup.exe", src=os.path.join(WEASEL, "WeaselSetup.exe"),
         groups={107: "main"}, menus=False, appcast=False, swap=False,
         fd=("幻熊输入法 安装程序", "幻熊輸入法 安裝程式", "Huanxiong IME Setup")),
    dict(name="WeaselDeployer.exe", src=os.path.join(WEASEL, "WeaselDeployer.orig.exe"),
         groups={131: "main"}, menus=False, appcast=False, swap=False,
         fd=("幻熊输入法 部署工具", "幻熊輸入法 部署工具", "Huanxiong IME Deployer")),
    dict(name="uninstall.exe", src=os.path.join(WEASEL, "uninstall.exe"),
         groups={103: "main"}, menus=False, appcast=False, swap=False,
         fd=("幻熊输入法 卸载程序", "幻熊輸入法 卸載程式", "Huanxiong IME Uninstaller")),
]


def apply_brand(path, job):
    log = []
    # 图标
    if job["groups"]:
        gmap = {gid: icons(var) for gid, var in job["groups"].items()}
        n = W.rebrand_icons(path, gmap)
        log.append("图标 %d 张（组 %s）" % (n, sorted(job["groups"])))
    # 版本信息
    n = W.rebrand_version(path, vtables(*job["fd"], tw_is_zh=job.get("tw_is_zh", False)))
    log.append("版本信息 %d 块" % n)
    # 菜单
    if job["menus"]:
        n = 0
        with W.ResFile(path) as r:
            for mid, langs in MENUS.items():
                for lang, items in langs.items():
                    r.update(W._ptr(W.RT_MENU), W._ptr(mid), lang, W.menu_blob(items))
                    n += 1
        log.append("菜单 %d 项 × %d 语言" % (len(MENUS), n // len(MENUS)))
    # 自动更新
    if job["appcast"]:
        data, ents = W.pe_resources(path)
        items = [(p[0], p[1], p[2]) for p, off, sz, cp in ents
                 if p[0] == "APPCAST" or (isinstance(p[0], str) and p[0].upper() == "APPCAST")]
        if not items:
            # 字符串类型资源名在 PE 里是字符串，parse 后是 str
            items = [(p[0], p[1], p[2]) for p, off, sz, cp in ents if p[0] == "APPCAST"]
        W.drop_resources(path, items)
        log.append("掐掉自动更新 %d 项" % len(items))
    return log


K32 = ctypes.WinDLL("kernel32", use_last_error=True)
K32.MoveFileExW.argtypes = [wt.LPCWSTR, wt.LPCWSTR, wt.DWORD]
K32.MoveFileExW.restype = wt.BOOL
DELAY_UNTIL_REBOOT = 0x4
REPLACE_EXISTING = 0x1


def schedule_replace(src, dst):
    ok = K32.MoveFileExW(src, dst, DELAY_UNTIL_REBOOT | REPLACE_EXISTING)
    return bool(ok), ctypes.get_last_error()


def stop_server():
    subprocess.run([os.path.join(WEASEL, "WeaselServer.exe"), "/q"], timeout=20,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def start_server():
    subprocess.Popen([os.path.join(WEASEL, "WeaselServer.exe")],
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def backup(path):
    bak = path + ".bak_brand"
    if not os.path.exists(bak):
        shutil.copy2(path, bak)
        return True
    return False


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "--test"
    os.makedirs(SWAP_DIR, exist_ok=True)

    if mode == "--restore":
        for job in JOBS:
            for cand in (job["src"], os.path.join(SWAP_DIR, job["name"])):
                bak = cand + ".bak_brand"
                if os.path.exists(bak):
                    try:
                        shutil.copy2(bak, cand)
                        print("还原 %s" % cand)
                    except OSError as e:
                        print("还原失败 %s：%s" % (cand, e))
        print("\n还原完毕。System32/SysWOW64 需要重启生效（如已登记）。")
        return 0

    jobs = [j for j in JOBS if j["swap"]] if mode == "--test" else JOBS
    if mode == "--all":
        stop_server()
        print("已停止 WeaselServer\n")

    report = []
    for job in jobs:
        print("=== %s" % job["name"])
        # 有备份就先还原，保证每次从原始状态改（幂等）
        srv_bak = job["src"] + ".bak_brand"
        if os.path.exists(srv_bak):
            try:
                shutil.copy2(srv_bak, job["src"])
                print("   （已从 .bak_brand 还原原始文件）")
            except OSError as e:
                print("   还原失败：%s" % e)
        # 工作副本
        work = os.path.join(SWAP_DIR, job["name"])
        if os.path.exists(work):
            os.remove(work)
        shutil.copy2(job["src"], work)
        if not os.path.exists(work + ".bak_brand"):
            shutil.copy2(job["src"], work + ".bak_brand")

        try:
            for line in apply_brand(work, job):
                print("   " + line)
        except Exception as e:
            print("   [失败] %r" % (e,))
            report.append((job["name"], "改失败: %s" % e))
            continue

        if job["swap"]:
            report.append((job["name"], "副本已生成，待登记开机替换"))
            print("   副本就绪 → %s" % work)
        else:
            # 尝试直接写回 Program Files
            bak_ok = backup(job["src"])
            try:
                shutil.copy2(work, job["src"])
                print("   已写回 %s%s" % (job["src"], "（已备份 .bak_brand）" if bak_ok else ""))
                report.append((job["name"], "已直接替换"))
                os.remove(work)
            except OSError as e:
                print("   直接替换失败（%s），转为开机替换" % e)
                report.append((job["name"], "被占用，已登记开机替换"))
                job["swap"] = True

    # 登记开机替换
    need_swap = [j for j in jobs if j["swap"]]
    if need_swap:
        print("\n=== 登记开机替换")
        for job in need_swap:
            work = os.path.join(SWAP_DIR, job["name"])
            dst = job["src"]
            if job["name"] == "weasel64.dll":
                dst = os.path.join(SYSTEM32, "weasel.dll")
            elif job["name"] == "weasel32.dll":
                dst = os.path.join(SYSWOW64, "weasel.dll")
            ok, err = schedule_replace(work, dst)
            print("   %s → %s : %s" % (job["name"], dst, "已登记" if ok else "失败 err=%d" % err))

    if mode == "--all":
        start_server()
        print("\nWeaselServer 已重启")

    print("\n=== 汇总")
    for n, s in report:
        print("  %-20s %s" % (n, s))
    return 0


if __name__ == "__main__":
    sys.exit(main())
