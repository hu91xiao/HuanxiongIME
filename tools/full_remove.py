# -*- coding: utf-8 -*-
"""
把「幻熊输入法」从这台机器上彻底清除（需要管理员权限）。

做的事情，按顺序：
  1. 杀掉 WeaselServer / WeaselDeployer 进程
  2. 跑官方卸载程序 unins000.exe /VERYSILENT
  3. 删安装目录  C:\\Program Files\\Rime
  4. 删用户配置  %APPDATA%\\Rime（含词频、自定义短语、build 缓存）
  5. 删系统目录的 weasel.dll / weasel_legacy.ime（删不掉就登记重启后删）
  6. 删注册表：CLSID、CTF\\TIP、WOW6432Node 视图、Rime 分支、语言列表项、排序项
  7. 删快捷方式、清理 %TEMP% 日志

刻意**不删**的东西：
  · C:\\Users\\hu\\HuanxiongIME        —— 源码与安装包本体
  · 桌面上的安装程序 exe               —— 你还要用它测试
  · C:\\Windows\\Fonts\\NotoSansSC-VF.ttf —— 通用字体，别的软件可能在用（安装包会检测并跳过）

用法（管理员）：
  python tools\\full_remove.py
  python tools\\full_remove.py --dry-run     # 只列出会删什么，不动手
"""
import ctypes
import os
import shutil
import subprocess
import sys
import time
import winreg
from ctypes import wintypes as wt

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
LOG = os.path.join(ROOT, "backup", "preinstall-20261028", "remove_log.txt")

CLSID = "{A3F4CDED-B1E9-41EE-9CA6-7B4D0DE6CB0A}"
PROF = "{3D02CAB6-2B8E-4781-BA20-1C9267529467}"
KBLAYOUT_ASM = "{34745C63-B2F0-4784-8B67-5E12C8701A31}"

INSTALL_DIR = r"C:\Program Files\Rime"
USER_DIR = os.path.join(os.environ["APPDATA"], "Rime")
LOCAL_COPY = os.path.join(os.environ["LOCALAPPDATA"], "Programs", "HuanxiongSettings")

SYS_DLLS = [
    r"C:\Windows\System32\weasel.dll",
    r"C:\Windows\System32\weasel.ime",
    r"C:\Windows\System32\weasel_legacy.ime",
    r"C:\Windows\SysWOW64\weasel.dll",
]

REG_TREES = [
    (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Classes\CLSID\%s" % CLSID),
    (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\CTF\TIP\%s" % CLSID),
    (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Classes\CLSID\%s" % CLSID),
    (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\CTF\TIP\%s" % CLSID),
    (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Rime"),
    (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Rime"),
    (winreg.HKEY_CURRENT_USER, r"Software\Rime"),
]

DRY = "--dry-run" in sys.argv
_lines = []


def log(msg=""):
    print(msg)
    _lines.append(str(msg))
    try:
        os.makedirs(os.path.dirname(LOG), exist_ok=True)
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(str(msg) + "\n")
    except Exception:                                       # noqa: BLE001
        pass


def flush_log():
    pass


# --------------------------------------------------------------- 进程
def kill_processes(names):
    """按进程名强杀，不依赖 taskkill"""
    TH32CS_SNAPPROCESS = 0x00000002
    PROCESS_TERMINATE = 0x0001

    class PE32(ctypes.Structure):
        _fields_ = [("dwSize", wt.DWORD), ("cntUsage", wt.DWORD),
                    ("th32ProcessID", wt.DWORD), ("th32DefaultHeapID", ctypes.c_void_p),
                    ("th32ModuleID", wt.DWORD), ("cntThreads", wt.DWORD),
                    ("th32ParentProcessID", wt.DWORD), ("pcPriClassBase", ctypes.c_long),
                    ("dwFlags", wt.DWORD), ("szExeFile", wt.WCHAR * 260)]

    k32 = ctypes.WinDLL("kernel32", use_last_error=True)
    k32.CreateToolhelp32Snapshot.restype = wt.HANDLE
    k32.CreateToolhelp32Snapshot.argtypes = [wt.DWORD, wt.DWORD]
    snap = k32.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
    if snap in (None, wt.HANDLE(-1).value):
        return 0
    ent = PE32()
    ent.dwSize = ctypes.sizeof(PE32)
    lowered = [n.lower() for n in names]
    killed = 0
    ok = k32.Process32FirstW(snap, ctypes.byref(ent))
    while ok:
        if ent.szExeFile.lower() in lowered:
            h = k32.OpenProcess(PROCESS_TERMINATE, False, ent.th32ProcessID)
            if h:
                if k32.TerminateProcess(h, 0):
                    killed += 1
                    log("   已结束 %s (pid=%d)" % (ent.szExeFile, ent.th32ProcessID))
                k32.CloseHandle(h)
        ok = k32.Process32NextW(snap, ctypes.byref(ent))
    k32.CloseHandle(snap)
    return killed


# --------------------------------------------------------------- 文件
def remove_dir(path):
    if not os.path.isdir(path):
        log("  跳过（不存在）%s" % path)
        return True
    if DRY:
        log("  [dry] 删除目录 %s" % path)
        return True
    try:
        shutil.rmtree(path)
        log("  已删目录 %s" % path)
        return True
    except Exception as e:                                  # noqa: BLE001
        log("  ！删目录失败 %s -> %s" % (path, e))
        return False


def remove_file(path, schedule_reboot=False):
    if not os.path.exists(path):
        return True
    if DRY:
        log("  [dry] 删除文件 %s" % path)
        return True
    try:
        os.remove(path)
        log("  已删文件 %s" % path)
        return True
    except Exception as e:                                  # noqa: BLE001
        log("  ！删不掉 %s -> %s" % (path, e))
        if schedule_reboot and schedule_delete_on_reboot(path):
            log("    → 已登记重启后删除")
        return False


def schedule_delete_on_reboot(path):
    """MoveFileExW(path, NULL, MOVEFILE_DELAY_UNTIL_REBOOT)"""
    try:
        k32 = ctypes.WinDLL("kernel32", use_last_error=True)
        k32.MoveFileExW.argtypes = [wt.LPCWSTR, wt.LPCWSTR, wt.DWORD]
        return bool(k32.MoveFileExW(path, None, 0x4))
    except Exception:                                       # noqa: BLE001
        return False


# --------------------------------------------------------------- 注册表
def remove_reg_tree(hive, path):
    if DRY:
        log("  [dry] 删除注册表 %s\\%s" % (hive_name(hive), path))
        return
    try:
        winreg.OpenKey(hive, path).Close()
    except OSError:
        log("  跳过（不存在）%s\\%s" % (hive_name(hive), path))
        return
    try:
        _del_tree(hive, path)
        log("  已删注册表 %s\\%s" % (hive_name(hive), path))
    except Exception as e:                                  # noqa: BLE001
        log("  ！删注册表失败 %s\\%s -> %s" % (hive_name(hive), path, e))


def _del_tree(hive, path):
    with winreg.OpenKey(hive, path, 0, winreg.KEY_ALL_ACCESS) as key:
        subs = []
        i = 0
        while True:
            try:
                subs.append(winreg.EnumKey(key, i))
            except OSError:
                break
            i += 1
    for s in subs:
        _del_tree(hive, path + "\\" + s)
    # 需要重新拿 ALL_ACCESS 才能删
    winreg.DeleteKey(hive, path)


def hive_name(h):
    return {winreg.HKEY_LOCAL_MACHINE: "HKLM", winreg.HKEY_CURRENT_USER: "HKCU"}.get(h, "?")


def clean_user_profile():
    """从「语言列表」里摘掉幻熊这一项"""
    for base in (r"Control Panel\International\User Profile",
                 r"Control Panel\International\User Profile System Backup"):
        try:
            root = winreg.OpenKey(winreg.HKEY_CURRENT_USER, base)
        except OSError:
            continue
        try:
            langs = []
            i = 0
            while True:
                try:
                    langs.append(winreg.EnumKey(root, i))
                except OSError:
                    break
                i += 1
        finally:
            root.Close()
        for lang in langs:
            p = base + "\\" + lang
            try:
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, p, 0, winreg.KEY_ALL_ACCESS)
            except OSError:
                continue
            try:
                vals = []
                i = 0
                while True:
                    try:
                        n, d, _t = winreg.EnumValue(key, i)
                    except OSError:
                        break
                    if CLSID in str(n) or CLSID in str(d):
                        vals.append(n)
                    i += 1
                for v in vals:
                    if DRY:
                        log("  [dry] 删值 %s\\%s :: %s" % (base, lang, v))
                    else:
                        winreg.DeleteValue(key, v)
                        log("  已删值 %s\\%s :: %s" % (base, lang, v))
            finally:
                key.Close()


def clean_ctf_assemblies():
    """HKCU\\Software\\Microsoft\\CTF\\Assemblies 下指向幻熊的值"""
    base = r"Software\Microsoft\CTF\Assemblies"
    try:
        root = winreg.OpenKey(winreg.HKEY_CURRENT_USER, base)
    except OSError:
        return
    try:
        langs = []
        i = 0
        while True:
            try:
                langs.append(winreg.EnumKey(root, i))
            except OSError:
                break
            i += 1
    finally:
        root.Close()
    for lang in langs:
        p = "%s\\%s\\%s" % (base, lang, KBLAYOUT_ASM)
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, p, 0, winreg.KEY_ALL_ACCESS)
        except OSError:
            continue
        try:
            hit = False
            for name in ("Default", "Profile"):
                try:
                    if CLSID in str(winreg.QueryValueEx(key, name)[0]) or \
                       PROF in str(winreg.QueryValueEx(key, name)[0]):
                        hit = True
                except OSError:
                    pass
            if hit:
                if DRY:
                    log("  [dry] 删注册表 HKCU\\%s" % p)
                else:
                    key.Close()
                    _del_tree(winreg.HKEY_CURRENT_USER, p)
                    log("  已删注册表 HKCU\\%s" % p)
                    continue
        finally:
            try:
                key.Close()
            except Exception:                               # noqa: BLE001
                pass


def clean_sort_order():
    """HKCU\\Software\\Microsoft\\CTF\\SortOrder\\AssemblyItem 下指向幻熊的排序项"""
    base = r"Software\Microsoft\CTF\SortOrder\AssemblyItem"
    try:
        root = winreg.OpenKey(winreg.HKEY_CURRENT_USER, base)
    except OSError:
        return
    try:
        langs = []
        i = 0
        while True:
            try:
                langs.append(winreg.EnumKey(root, i))
            except OSError:
                break
            i += 1
    finally:
        root.Close()
    for lang in langs:
        try:
            lk = winreg.OpenKey(winreg.HKEY_CURRENT_USER, "%s\\%s" % (base, lang))
        except OSError:
            continue
        try:
            asms = []
            i = 0
            while True:
                try:
                    asms.append(winreg.EnumKey(lk, i))
                except OSError:
                    break
                i += 1
        finally:
            lk.Close()
        if KBLAYOUT_ASM not in asms:
            continue
        p = "%s\\%s\\%s" % (base, lang, KBLAYOUT_ASM)
        try:
            ak = winreg.OpenKey(winreg.HKEY_CURRENT_USER, p)
        except OSError:
            continue
        try:
            items = []
            i = 0
            while True:
                try:
                    items.append(winreg.EnumKey(ak, i))
                except OSError:
                    break
                i += 1
        finally:
            ak.Close()
        for it in items:
            sub = "%s\\%s" % (p, it)
            try:
                sk = winreg.OpenKey(winreg.HKEY_CURRENT_USER, sub)
            except OSError:
                continue
            hit = False
            try:
                for name in ("CLSID", "Profile"):
                    try:
                        if CLSID in str(winreg.QueryValueEx(sk, name)[0]) or \
                           PROF in str(winreg.QueryValueEx(sk, name)[0]):
                            hit = True
                    except OSError:
                        pass
            finally:
                sk.Close()
            if hit:
                if DRY:
                    log("  [dry] 删注册表 HKCU\\%s" % sub)
                else:
                    try:
                        _del_tree(winreg.HKEY_CURRENT_USER, sub)
                        log("  已删注册表 HKCU\\%s" % sub)
                    except Exception as e:                  # noqa: BLE001
                        log("  ！删排序项失败 %s -> %s" % (sub, e))


def clean_uninstall_entries():
    """Inno 安装项（正常卸载会删，这里兜底）"""
    for hive, base in [
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"),
    ]:
        try:
            root = winreg.OpenKey(hive, base)
        except OSError:
            continue
        try:
            subs = []
            i = 0
            while True:
                try:
                    subs.append(winreg.EnumKey(root, i))
                except OSError:
                    break
                i += 1
        finally:
            root.Close()
        for s in subs:
            p = base + "\\" + s
            try:
                k = winreg.OpenKey(hive, p)
            except OSError:
                continue
            try:
                try:
                    name = str(winreg.QueryValueEx(k, "DisplayName")[0])
                except OSError:
                    name = ""
                try:
                    loc = str(winreg.QueryValueEx(k, "InstallLocation")[0])
                except OSError:
                    loc = ""
            finally:
                k.Close()
            if "幻熊" in name or "weasel" in loc.lower() or "幻熊" in loc:
                log("  卸载项: %s\\%s  (%s)" % (hive_name(hive), p, name))
                remove_reg_tree(hive, p)


# --------------------------------------------------------------- 主流程
def main():
    try:
        os.remove(LOG)
    except OSError:
        pass
    log("=" * 60)
    log("幻熊输入法 —— 完全清除" + ("（演练模式，不会真删）" if DRY else ""))
    log("=" * 60)

    log("\n[1/8] 结束进程")
    if DRY:
        log("  [dry] 会结束 WeaselServer / WeaselDeployer")
        n = 0
    else:
        n = kill_processes(["WeaselServer.exe", "WeaselDeployer.exe", "HuanxiongSettings.exe"])
    if not n:
        log("  没有正在运行的进程")

    log("\n[2/8] 运行官方卸载程序")
    unins = os.path.join(INSTALL_DIR, "weasel-0.17.4", "unins000.exe")
    if os.path.isfile(unins) and not DRY:
        try:
            p = subprocess.run([unins, "/VERYSILENT", "/SUPPRESSMSGBOXES", "/NORESTART"],
                               timeout=600)
            log("  卸载程序返回 %s" % p.returncode)
        except Exception as e:                              # noqa: BLE001
            log("  卸载程序出错: %r" % (e,))
        # 等它把目录清完（Inno 会把自己复制到 temp 再执行）
        for _ in range(30):
            if not os.path.isdir(INSTALL_DIR):
                break
            time.sleep(2)
    elif DRY:
        log("  [dry] 会运行 %s /VERYSILENT" % unins)
    else:
        log("  没有卸载程序，直接删目录")

    log("\n[3/8] 删除安装目录")
    remove_dir(INSTALL_DIR)

    log("\n[4/8] 删除用户配置（词频 / 自定义短语 / 方案）")
    remove_dir(USER_DIR)

    log("\n[5/8] 删除系统目录的 dll / ime")
    for f in SYS_DLLS:
        remove_file(f, schedule_reboot=True)
    # 历史备份文件（.bak_menu / .old.N）
    for d in (r"C:\Windows\SysWOW64", r"C:\Windows\System32"):
        if DRY or not os.path.isdir(d):
            continue
        for name in os.listdir(d):
            if name.lower().startswith("weasel") and (
                    ".bak" in name.lower() or ".old" in name.lower()):
                remove_file(os.path.join(d, name), schedule_reboot=True)

    log("\n[6/8] 删除注册表")
    for hive, path in REG_TREES:
        remove_reg_tree(hive, path)
    clean_user_profile()
    clean_ctf_assemblies()
    clean_sort_order()
    clean_uninstall_entries()

    log("\n[7/8] 删除快捷方式 / 旧副本 / 临时文件")
    for lnk in [
        os.path.join(os.environ["USERPROFILE"], "Desktop", "幻熊输入法设置.lnk"),
        os.path.join(os.environ["APPDATA"], "Microsoft", "Windows", "Start Menu",
                     "Programs", "幻熊输入法设置.lnk"),
    ]:
        remove_file(lnk)
    remove_dir(LOCAL_COPY)
    tmp = os.environ.get("TEMP", "")
    for item in [os.path.join(tmp, "rime.weasel"),
                 os.path.join(tmp, "huanxiong_launch.log"),
                 os.path.join(tmp, "rime_settings_selftest.txt")]:
        if os.path.isdir(item):
            remove_dir(item)
        else:
            remove_file(item)

    log("\n[8/8] 残留复查")
    left = []
    if os.path.isdir(INSTALL_DIR):
        left.append(INSTALL_DIR)
    if os.path.isdir(USER_DIR):
        left.append(USER_DIR)
    for f in SYS_DLLS:
        if os.path.exists(f):
            left.append(f)
    for hive, path in REG_TREES:
        try:
            winreg.OpenKey(hive, path).Close()
            left.append("%s\\%s" % (hive_name(hive), path))
        except OSError:
            pass
    if left:
        log("  以下仍在（多为被占用，重启后消失）：")
        for x in left:
            log("    · " + x)
    else:
        log("  干净，没有残留")

    log("\n完成。")
    flush_log()
    return 0


if __name__ == "__main__":
    sys.exit(main())
