# -*- coding: utf-8 -*-
"""
幻熊输入法 —— 一键构建

    python build.py payload     # 从本机现行安装 / 用户配置里重新快照打包素材
    python build.py settings    # PyInstaller 打包设置面板 → payload/settings
    python build.py installer   # Inno Setup 编译安装包 → dist/
    python build.py all         # 上面三步全做
"""
import os
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
PAYLOAD = os.path.join(ROOT, "payload")
PROG_SRC = r"C:\Program Files\Rime\weasel-0.17.4"
RIME_SRC = os.path.join(os.environ.get("APPDATA", ""), "Rime")
FONT_SRC = os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Fonts", "NotoSansSC-VF.ttf")
PY = sys.executable
_venv_py = os.path.join(ROOT, ".venv", "Scripts", "python.exe")
if os.path.isfile(_venv_py):
    PY = _venv_py

# 程序目录里不带走的东西：备份、旧版、以及会被我们替换掉的部署器
PROG_SKIP_PREFIX = ("WeaselDeployer.onefile", "uninstall.exe")
PROG_SKIP_SUFFIX = (".bak_brand", ".bak_menu", ".bak")
# Rime 用户目录里不带走的东西：机器状态与个人词频
RIME_SKIP = {"installation.yaml", "user.yaml", "user.txt"}


def log(msg):
    print("  " + msg)


def rm(path):
    if os.path.isdir(path):
        shutil.rmtree(path, ignore_errors=True)
    elif os.path.exists(path):
        os.remove(path)


def collect_payload():
    """把当前这台机器上的成品状态快照成安装包素材（程序 + 配置 + 字体）"""
    prog_dst = os.path.join(PAYLOAD, "program")
    rime_dst = os.path.join(PAYLOAD, "rime")
    font_dst = os.path.join(PAYLOAD, "fonts")

    print("[1/3] 程序文件 ← " + PROG_SRC)
    rm(prog_dst)
    os.makedirs(prog_dst)
    n = 0
    for name in os.listdir(PROG_SRC):
        if name.startswith(PROG_SKIP_PREFIX) or name.endswith(PROG_SKIP_SUFFIX):
            continue
        if name in ("WeaselDeployer.exe", "data", "uninstall.exe"):
            continue                       # 部署器由设置面板顶替；data 单独拷
        src = os.path.join(PROG_SRC, name)
        if os.path.isfile(src):
            shutil.copy2(src, os.path.join(prog_dst, name))
            n += 1
    shutil.copytree(os.path.join(PROG_SRC, "data"), os.path.join(prog_dst, "data"))
    # 原版部署器留着，设置面板遇到不认识的参数会转交给它
    orig = os.path.join(PROG_SRC, "WeaselDeployer.orig.exe")
    if os.path.isfile(orig):
        shutil.copy2(orig, os.path.join(prog_dst, "WeaselDeployer.orig.exe"))
    log("%d 个文件 + data 目录" % n)

    print("[2/3] Rime 配置 ← " + RIME_SRC)
    rm(rime_dst)
    os.makedirs(rime_dst)
    n = 0
    for name in sorted(os.listdir(RIME_SRC)):
        low = name.lower()
        if not low.endswith((".yaml", ".txt", ".lua")) or low in RIME_SKIP:
            continue
        if ".bak" in low:
            continue
        src = os.path.join(RIME_SRC, name)
        if os.path.isfile(src):
            shutil.copy2(src, os.path.join(rime_dst, name))
            n += 1
    log("%d 个配置文件" % n)

    print("[3/3] 候选窗字体 ← " + FONT_SRC)
    os.makedirs(font_dst, exist_ok=True)
    if os.path.isfile(FONT_SRC):
        shutil.copy2(FONT_SRC, os.path.join(font_dst, "NotoSansSC-VF.ttf"))
        log("NotoSansSC-VF.ttf  %.1f MB" % (os.path.getsize(FONT_SRC) / 1048576.0))
    else:
        log("!! 本机没有 NotoSansSC-VF.ttf，候选窗字体会退回宋体")


def build_settings():
    """PyInstaller：设置面板（onedir）→ payload/settings"""
    print("[设置面板] PyInstaller onedir 打包")
    out = os.path.join(ROOT, "build", "out")
    work = os.path.join(ROOT, "build", "work")
    rm(out)
    rm(work)
    cmd = [PY, "-m", "PyInstaller", "--noconfirm", "--clean",
           "--distpath", out, "--workpath", work,
           os.path.join(ROOT, "HuanxiongSettings.spec")]
    r = subprocess.run(cmd, cwd=ROOT)
    if r.returncode != 0:
        raise SystemExit("PyInstaller 失败，退出码 %d" % r.returncode)

    dst = os.path.join(PAYLOAD, "settings")
    rm(dst)
    shutil.copytree(os.path.join(out, "HuanxiongSettings"), dst)
    size = sum(os.path.getsize(os.path.join(dp, f))
               for dp, _dn, fn in os.walk(dst) for f in fn)
    log("→ payload/settings（%.1f MB）" % (size / 1048576.0))


def find_iscc():
    cands = [
        r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
        r"C:\Program Files\Inno Setup 6\ISCC.exe",
        os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs", "Inno Setup 6", "ISCC.exe"),
        os.path.join(os.environ.get("USERPROFILE", ""), "InnoSetup6", "ISCC.exe"),
    ]
    for p in cands:
        if p and os.path.isfile(p):
            return p
    raise SystemExit("找不到 Inno Setup 的 ISCC.exe，请先安装 Inno Setup 6")


def build_installer():
    print("[安装包] Inno Setup 编译")
    os.makedirs(os.path.join(ROOT, "dist"), exist_ok=True)
    r = subprocess.run([find_iscc(), "/Qp", os.path.join(ROOT, "installer", "setup.iss")], cwd=ROOT)
    if r.returncode != 0:
        raise SystemExit("ISCC 失败，退出码 %d" % r.returncode)
    for f in sorted(os.listdir(os.path.join(ROOT, "dist"))):
        if f.lower().endswith(".exe"):
            p = os.path.join(ROOT, "dist", f)
            log("→ dist/%s  %.1f MB" % (f, os.path.getsize(p) / 1048576.0))


def main():
    what = (sys.argv[1] if len(sys.argv) > 1 else "all").lower()
    if what in ("payload", "all"):
        collect_payload()
    if what in ("settings", "all"):
        build_settings()
    if what in ("installer", "all"):
        build_installer()
    if what not in ("payload", "settings", "installer", "all"):
        print(__doc__)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
