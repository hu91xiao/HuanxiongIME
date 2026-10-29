# -*- coding: utf-8 -*-
"""
把「幻熊输入法」恢复到 full_remove.py 删除之前的样子。

做的事：
  1. 如果没装 → 跑 dist\\幻熊输入法-1.0-安装程序.exe /VERYSILENT（装程序 + 注册 + 系统 dll + 快捷方式）
  2. 停服务
  3. 把备份里的 %APPDATA%\\Rime 覆盖回去（含词频 userdb、你那 4 条个人短语、所有 yaml）
  4. 重新部署 + 起服务
  5. 校验注册表，缺了就用 ime_registry.json 补

用法（管理员）：
  python tools\\restore.py
  python tools\\restore.py --dry-run
  python tools\\restore.py --config-only    # 程序已装好，只把个人配置盖回去
"""
import ctypes
import os
import shutil
import subprocess
import sys
import time
import winreg

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
BK = os.path.join(ROOT, "backup", "preinstall-20261028")
BK_RIME = os.path.join(BK, "Rime")
BK_REG = os.path.join(BK, "registry", "ime_registry.json")
SETUP_CANDIDATES = [
    os.path.join(ROOT, "dist", "幻熊输入法-1.0-安装程序.exe"),
    os.path.join(os.environ.get("USERPROFILE", ""), "Desktop", "幻熊输入法-1.0-安装程序.exe"),
]
SETUP = next((p for p in SETUP_CANDIDATES if os.path.isfile(p)), SETUP_CANDIDATES[0])

INSTALL_DIR = r"C:\Program Files\Rime\weasel-0.17.4"
USER_DIR = os.path.join(os.environ["APPDATA"], "Rime")
CLSID = "{A3F4CDED-B1E9-41EE-9CA6-7B4D0DE6CB0A}"

DRY = "--dry-run" in sys.argv
CONFIG_ONLY = "--config-only" in sys.argv
LOG = os.path.join(BK, "restore_log.txt")


def log(msg=""):
    print(msg)
    try:
        os.makedirs(BK, exist_ok=True)
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(str(msg) + "\n")
    except Exception:                                       # noqa: BLE001
        pass


def is_admin():
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:                                       # noqa: BLE001
        return False


def elevate():
    """不是管理员就带着同样参数重新以管理员身份启动自己"""
    params = " ".join('"%s"' % a if " " in a else a for a in sys.argv)
    rc = ctypes.windll.shell32.ShellExecuteW(
        None, "runas", sys.executable, params, os.path.dirname(ROOT), 1)
    sys.exit(0 if rc > 32 else 1)


# --------------------------------------------------------------- 进程
def kill_server():
    TH32CS_SNAPPROCESS = 0x00000002
    PROCESS_TERMINATE = 0x0001

    class PE32(ctypes.Structure):
        _fields_ = [("dwSize", ctypes.c_ulong), ("cntUsage", ctypes.c_ulong),
                    ("th32ProcessID", ctypes.c_ulong), ("th32DefaultHeapID", ctypes.c_void_p),
                    ("th32ModuleID", ctypes.c_ulong), ("cntThreads", ctypes.c_ulong),
                    ("th32ParentProcessID", ctypes.c_ulong), ("pcPriClassBase", ctypes.c_long),
                    ("dwFlags", ctypes.c_ulong), ("szExeFile", ctypes.c_wchar * 260)]

    k32 = ctypes.WinDLL("kernel32", use_last_error=True)
    k32.CreateToolhelp32Snapshot.restype = ctypes.c_void_p
    snap = k32.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
    ent = PE32()
    ent.dwSize = ctypes.sizeof(PE32)
    n = 0
    ok = k32.Process32FirstW(snap, ctypes.byref(ent))
    while ok:
        if ent.szExeFile.lower() in ("weaselserver.exe", "weaseldeployer.exe"):
            h = k32.OpenProcess(PROCESS_TERMINATE, False, ent.th32ProcessID)
            if h:
                k32.TerminateProcess(h, 0)
                k32.CloseHandle(h)
                n += 1
        ok = k32.Process32NextW(snap, ctypes.byref(ent))
    k32.CloseHandle(snap)
    return n


def start_server():
    exe = os.path.join(INSTALL_DIR, "WeaselServer.exe")
    if not os.path.isfile(exe):
        log("  ！找不到 WeaselServer.exe")
        return
    # 让它脱离父进程，否则脚本退出时服务会跟着没
    subprocess.Popen('start "" "%s"' % exe, shell=True, cwd=INSTALL_DIR)
    time.sleep(3)
    out = subprocess.run(["tasklist", "/FI", "IMAGENAME eq WeaselServer.exe"],
                         capture_output=True, text=True, errors="ignore").stdout
    log("  服务: " + ("已启动 ✓" if "WeaselServer" in out else "没起来 ✗"))


# --------------------------------------------------------------- 注册表
def registry_ok():
    try:
        winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                       r"SOFTWARE\Classes\CLSID\%s\InprocServer32" % CLSID).Close()
        return True
    except OSError:
        return False


def main():
    try:
        os.remove(LOG)
    except OSError:
        pass
    log("=" * 60)
    log("幻熊输入法 —— 还原到删除前状态" + ("（演练模式）" if DRY else ""))
    log("=" * 60)

    log("\n[0/6] 检查必要的材料")
    ok = True
    for p, what in [(BK_RIME, "配置备份"), (SETUP, "安装包")]:
        e = os.path.exists(p)
        log("  %-10s %s  %s" % (what, "✓" if e else "✗ 缺失", p))
        if not e:
            ok = False
    if not ok:
        log("\n材料不全，终止。")
        return 1

    installed = os.path.isdir(INSTALL_DIR)

    if not CONFIG_ONLY:
        log("\n[1/6] 安装程序（如果已装会跳过）")
        if installed:
            log("  已经装好了: " + INSTALL_DIR)
        elif DRY:
            log("  [dry] 会运行安装包 /VERYSILENT")
        else:
            t0 = time.time()
            p = subprocess.run([SETUP, "/VERYSILENT", "/SUPPRESSMSGBOXES", "/NORESTART"],
                               timeout=1200)
            log("  安装包返回 %s，用时 %d 秒" % (p.returncode, int(time.time() - t0)))
            for _ in range(20):
                if os.path.isdir(INSTALL_DIR):
                    break
                time.sleep(2)
            log("  安装目录: " + ("✓" if os.path.isdir(INSTALL_DIR) else "✗ 不存在"))

        log("\n[2/6] 检查注册表")
        if DRY:
            log("  [dry] 跳过")
        elif registry_ok():
            log("  注册表正常 ✓")
        else:
            log("  注册表缺失，用备份补…")
            r = subprocess.run([sys.executable, os.path.join(HERE, "ime_registry.py"),
                                "restore", BK_REG], timeout=120)
            log("  ime_registry restore 返回 %s" % r.returncode)

    log("\n[3/6] 停服务")
    if DRY:
        log("  [dry] 会停 WeaselServer")
    else:
        log("  结束了 %d 个进程" % kill_server())
        time.sleep(1)

    log("\n[4/6] 把个人配置盖回去（词频 / 自定义短语 / 全部 yaml）")
    if DRY:
        log("  [dry] 会复制 %s → %s" % (BK_RIME, USER_DIR))
    else:
        os.makedirs(USER_DIR, exist_ok=True)
        n = 0
        for dirpath, _dirs, files in os.walk(BK_RIME):
            rel = os.path.relpath(dirpath, BK_RIME)
            dst_dir = USER_DIR if rel == "." else os.path.join(USER_DIR, rel)
            os.makedirs(dst_dir, exist_ok=True)
            for f in files:
                src = os.path.join(dirpath, f)
                # LOCK / 日志这类文件不覆盖，避免数据库句柄冲突
                if f in ("LOCK", "LOG", "LOG.old"):
                    continue
                shutil.copy2(src, os.path.join(dst_dir, f))
                n += 1
        log("  已复制 %d 个文件" % n)

    log("\n[5/6] 重新部署")
    deployer = os.path.join(INSTALL_DIR, "WeaselDeployer.orig.exe")
    if not os.path.isfile(deployer):
        deployer = os.path.join(INSTALL_DIR, "WeaselDeployer.exe")
    if DRY:
        log("  [dry] 会运行 %s /deploy" % os.path.basename(deployer))
    elif not os.path.isfile(deployer):
        log("  ！找不到部署器")
    else:
        p = subprocess.run([deployer, "/deploy"], timeout=1200)
        log("  /deploy 返回 %s" % p.returncode)

    log("\n[6/6] 启动服务")
    if DRY:
        log("  [dry] 会启动 WeaselServer")
    else:
        start_server()

    log("\n完成。按 Win+空格 切到「幻熊输入法」即可。")
    log("（语言栏偶有缓存，没看到就注销一次或重启）")
    return 0


if __name__ == "__main__":
    if not is_admin() and not DRY:
        elevate()
    sys.exit(main())
