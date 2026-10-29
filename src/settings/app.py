# -*- coding: utf-8 -*-
"""
幻熊输入法设置 —— 桌面版（原生窗口，不是浏览器网页）

界面由 Windows 自带的 WebView2 渲染（和 VS Code / 微信 一样的做法），
但它是独立程序：有自己的窗口、任务栏图标，不需要浏览器、不需要装 Python。

打包成单文件 exe：见同目录 build.bat
"""
import os
import sys
import threading
import traceback

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)


def launch_log(txt):
    """启动诊断日志：记下被谁、用什么参数、什么工作目录拉起来的。

    托盘菜单点是黑盒，出问题只能靠这个文件判断。
    """
    try:
        import datetime
        p = os.path.join(os.environ.get("TEMP", "."), "huanxiong_launch.log")
        with open(p, "a", encoding="utf-8") as f:
            f.write("[%s] pid=%s exe=%s\n  argv=%r\n  cwd=%r\n  %s\n" % (
                datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                os.getpid(), sys.executable, sys.argv,
                os.getcwd(), txt))
    except Exception:                                           # noqa: BLE001
        pass


launch_log("module import")

import settings as CORE                                 # noqa: E402

APP_TITLE = "幻熊输入法设置"
APP_VERSION = "1.0"


def resource(name):
    """打包成 exe 后，界面文件在临时解包目录里"""
    base = getattr(sys, "_MEIPASS", HERE)
    return os.path.join(base, name)


class Api(object):
    """暴露给界面 JS 的方法：pywebview.api.xxx()"""

    # 注意：不要把 window 挂到 self 上，pywebview 会把 api 的公开属性递归序列化给 JS，
    # 挂上 window 会导致 "maximum recursion depth exceeded" 并让窗口起不来。

    # ---------------------------------------------------------- 读
    def state(self):
        try:
            st = CORE.read_state()
            st["_weasel_dir"] = CORE.WEASEL_DIR or ""
            st["_rime_dir"] = CORE.RIME
            st["_version"] = APP_VERSION
            return st
        except Exception as e:                                  # noqa: BLE001
            return {"error": str(e), "_trace": traceback.format_exc()}

    def info(self):
        return {
            "rime": CORE.RIME,
            "weasel": CORE.WEASEL_DIR or "",
            "backup": CORE.BACKUP_DIR,
            "version": APP_VERSION,
            "frozen": bool(getattr(sys, "frozen", False)),
        }

    # ---------------------------------------------------------- 写
    def apply(self, payload):
        try:
            msg = CORE.apply_settings(payload or {})
            return {"ok": True, "msg": msg}
        except Exception as e:                                  # noqa: BLE001
            return {"ok": False, "msg": "失败：%s" % e}

    def deploy(self):
        try:
            ok, msg = CORE.run_deploy()
            if ok:
                CORE.restart_server()
            return {"ok": ok, "msg": msg}
        except Exception as e:                                  # noqa: BLE001
            return {"ok": False, "msg": "失败：%s" % e}

    def open_path(self, what):
        try:
            ok, msg = CORE.open_target(what)
            return {"ok": ok, "msg": msg}
        except Exception as e:                                  # noqa: BLE001
            return {"ok": False, "msg": "打开失败：%s" % e}

    def export_config(self):
        try:
            ok, msg, path = CORE.export_bundle()
            return {"ok": ok, "msg": msg, "path": path or ""}
        except Exception as e:                                  # noqa: BLE001
            return {"ok": False, "msg": "导出失败：%s" % e}

    def import_config(self):
        """弹文件选择框，选 zip 后导入（会先备份）"""
        try:
            import webview
            wins = getattr(webview, "windows", None) or []
            if not wins:
                return {"ok": False, "msg": "窗口还没准备好"}
            picked = wins[0].create_file_dialog(
                webview.OPEN_DIALOG, allow_multiple=False,
                file_types=("配置包 (*.zip)", "所有文件 (*.*)"))
            if not picked:
                return {"ok": False, "msg": "已取消"}
            path = picked[0] if isinstance(picked, (list, tuple)) else picked
            ok, msg = CORE.import_bundle(path)
            return {"ok": ok, "msg": msg}
        except Exception as e:                                  # noqa: BLE001
            return {"ok": False, "msg": "导入失败：%s" % e}

    def quit(self):
        try:
            import webview
            for w in getattr(webview, "windows", None) or []:
                w.destroy()
        except Exception:                                       # noqa: BLE001
            pass


def _target_size():
    """按屏幕工作区算目标窗口大小（物理像素，已含缩放）"""
    try:
        import ctypes
        import ctypes.wintypes as wt

        u = ctypes.windll.user32
        r = wt.RECT()
        u.SystemParametersInfoW(0x0030, 0, ctypes.byref(r), 0)   # SPI_GETWORKAREA
        aw, ah = r.right - r.left, r.bottom - r.top
        if aw <= 0 or ah <= 0:
            return None
        w = max(900, min(1400, int(aw * 0.56)))
        h = max(620, min(1050, int(ah * 0.80)))
        return w, h
    except Exception:                                           # noqa: BLE001
        return None


def _fit_to_screen(window):
    """按屏幕工作区摆放窗口（避开任务栏）——全用同一套坐标，缩放多少都不会错"""
    try:
        import ctypes
        import ctypes.wintypes as wt
        import time

        time.sleep(1.2)
        u = ctypes.windll.user32
        r = wt.RECT()
        u.SystemParametersInfoW(0x0030, 0, ctypes.byref(r), 0)   # SPI_GETWORKAREA
        aw, ah = r.right - r.left, r.bottom - r.top
        if aw <= 0 or ah <= 0:
            return
        size = _target_size()
        if not size:
            return
        want_w, want_h = size
        w, h = want_w, want_h
        x = r.left + (aw - want_w) // 2
        y = r.top + (ah - want_h) // 2
        SWP_NOZORDER, SWP_NOACTIVATE = 0x0004, 0x0010
        # 两个坑：pywebview 在页面加载完会再调一次窗口尺寸（会退回创建时的大小）；
        # 高分屏下窗口尺寸还会被 DPI 虚拟化缩放，传进去的值和量出来的不一致。
        # 所以用「实测反馈」校准：差多少就按比例修正下次要传的值，稳定 4 秒就收手。
        stable = 0
        t0 = time.time()
        while time.time() - t0 < 20 and stable < 8:
            hwnd = _own_hwnd()
            if hwnd:
                rr = wt.RECT()
                u.GetWindowRect(hwnd, ctypes.byref(rr))
                cw, ch = rr.right - rr.left, rr.bottom - rr.top
                if cw and ch and abs(cw - want_w) <= 10 and abs(ch - want_h) <= 10:
                    stable += 1
                else:
                    stable = 0
                    if cw and ch:
                        w = max(400, int(round(w * want_w / float(cw))))
                        h = max(300, int(round(h * want_h / float(ch))))
                    u.SetWindowPos(hwnd, 0, x, y, w, h, SWP_NOZORDER | SWP_NOACTIVATE)
            time.sleep(0.5)
        if os.environ.get("RIME_SETTINGS_DEBUG"):
            hwnd = _own_hwnd()
            if hwnd:
                rr = wt.RECT()
                u.GetWindowRect(hwnd, ctypes.byref(rr))
                _log("work=(%s,%s,%s,%s) want=%sx%s sent=%sx%s got=%sx%s"
                     % (r.left, r.top, r.right, r.bottom, want_w, want_h, w, h,
                        rr.right - rr.left, rr.bottom - rr.top))
    except Exception:                                           # noqa: BLE001
        if os.environ.get("RIME_SETTINGS_DEBUG"):
            _log("FIT-ERROR " + traceback.format_exc())


def _log(txt):
    try:
        p = os.path.join(os.environ.get("TEMP", "."), "rime_settings_fit.log")
        with open(p, "a", encoding="utf-8") as f:
            f.write(txt + "\n")
    except Exception:                                           # noqa: BLE001
        pass


def _own_hwnd():
    """按标题找自己的窗口句柄（pywebview 不暴露 HWND）"""
    try:
        import ctypes
        import ctypes.wintypes as wt

        u = ctypes.windll.user32
        r = ctypes.windll.kernel32
        pid = r.GetCurrentProcessId()
        hit = []

        @ctypes.WINFUNCTYPE(ctypes.c_bool, wt.HWND, wt.LPARAM)
        def cb(h, _l):
            n = u.GetWindowTextLengthW(h)
            if not n:
                return True
            buf = ctypes.create_unicode_buffer(n + 1)
            u.GetWindowTextW(h, buf, n + 1)
            if not buf.value.startswith(APP_TITLE):
                return True
            owner = wt.DWORD()
            u.GetWindowThreadProcessId(h, ctypes.byref(owner))
            if owner.value == pid and u.IsWindowVisible(h):
                hit.append(h)
            return True

        u.EnumWindows(cb, 0)
        return hit[0] if hit else None
    except Exception:                                           # noqa: BLE001
        return None


def _set_dpi_aware():
    """让进程按物理像素工作，高分屏下界面才不会被位图放大（也才量得准尺寸）"""
    try:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(2)          # PER_MONITOR_DPI_AWARE
        return
    except Exception:                                           # noqa: BLE001
        pass
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:                                           # noqa: BLE001
        pass


def main():
    import webview

    _set_dpi_aware()

    api = Api()
    html = resource("ui.html")
    if not os.path.isfile(html):
        launch_log("!! 找不到界面文件 " + html)
        raise SystemExit("找不到界面文件 ui.html：%s" % html)

    win_w, win_h = _target_size() or (1120, 840)
    window = webview.create_window(
        "%s %s" % (APP_TITLE, APP_VERSION),
        url="file:///" + html.replace("\\", "/"),
        js_api=api,
        width=win_w, height=win_h,
        min_size=(900, 620),
        background_color="#F4F5F7",
        text_select=False,
    )
    webview.start(_fit_to_screen, window, debug=False)
    return 0


def selftest():
    """命令行自检：不弹窗，验证读配置、导出配置包是否正常（打包后排查用）"""
    lines = []
    lines.append("frozen=%s" % bool(getattr(sys, "frozen", False)))
    lines.append("exe=%s" % sys.executable)
    lines.append("rime=%s" % CORE.RIME)
    lines.append("weasel=%s" % (CORE.WEASEL_DIR or "未找到"))
    try:
        st = CORE.read_state()
        lines.append("state: mode=%s iq=%s page_size=%s font_point=%s scheme=%s style=%s"
                     % (st.get("mode"), st.get("iq"), st.get("page_size"),
                        st.get("font_point"), st.get("scheme"), st.get("commit_style")))
    except Exception as e:                                      # noqa: BLE001
        lines.append("state FAIL: %r" % (e,))
    try:
        tmp = os.path.join(os.environ.get("TEMP", HERE), "rime_selftest.zip")
        ok, msg, path = CORE.export_bundle(tmp)
        lines.append("export: ok=%s %s" % (ok, msg))
        if ok and path:
            import zipfile
            with zipfile.ZipFile(path) as z:
                names = z.namelist()
            lines.append("zip entries=%d" % len(names))
            lines.append("names=%s" % ", ".join(names))
            os.remove(path)
    except Exception as e:                                      # noqa: BLE001
        lines.append("export FAIL: %r" % (e,))
    txt = "\n".join(lines)
    try:
        with open(os.path.join(os.environ.get("TEMP", HERE), "rime_settings_selftest.txt"),
                  "w", encoding="utf-8") as f:
            f.write(txt)
    except Exception:                                           # noqa: BLE001
        pass
    print(txt)
    return 0


def delegate(args):
    """把不认识的命令行参数转给原版 WeaselDeployer（本程序可能被改名顶替它）"""
    import subprocess
    orig = os.path.join(os.path.dirname(sys.executable), "WeaselDeployer.orig.exe")
    if os.path.isfile(orig):
        flags = 0x00000008 | 0x00000200
        subprocess.Popen([orig] + args, cwd=os.path.dirname(orig),
                         creationflags=flags, close_fds=True)
        return True
    return False


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        raise SystemExit(selftest())
    if "--export" in sys.argv:
        ok, msg, path = CORE.export_bundle()
        print("%s %s" % (ok, msg))
        raise SystemExit(0 if ok else 1)
    # 被 Weasel 菜单调用时（顶替 WeaselDeployer.exe）：
    #   /deploy → 执行部署；其它参数（/dict 等）→ 转给原版
    argv = [a.lower() for a in sys.argv[1:]]
    if any(a in ("/deploy", "-deploy", "--deploy", "deploy") for a in argv):
        launch_log("=> 走 deploy 分支，不显示界面")
        ok, msg = CORE.run_deploy()
        if ok:
            CORE.restart_server()
            msg += "，服务已重启"
        print(msg)
        raise SystemExit(0 if ok else 1)
    if argv and not argv[0].startswith("--") and delegate(sys.argv[1:]):
        launch_log("=> 转交给 WeaselDeployer.orig.exe，不显示界面")
        raise SystemExit(0)
    launch_log("=> 进入 main()，准备创建窗口")
    try:
        rc = main()
        launch_log("== 窗口已关闭，main 返回 %r" % (rc,))
        sys.exit(rc)
    except SystemExit as e:
        launch_log("!! 提前退出: %r" % (e,))
        raise
    except BaseException:                                       # noqa: BLE001
        # 没有 WebView2 运行时时给个能看懂的提示
        detail = traceback.format_exc()
        launch_log("!! 启动失败\n" + detail)
        try:
            import tkinter as tk
            from tkinter import messagebox
            r = tk.Tk()
            r.withdraw()
            messagebox.showerror(
                APP_TITLE,
                "启动失败：\n\n%s\n\n如果提示缺少 Microsoft Edge WebView2 运行时，"
                "去微软官网装一下（Win11 和较新的 Win10 一般自带）。" % detail[-600:])
        except Exception:                                       # noqa: BLE001
            print(detail)
        raise SystemExit(1)
