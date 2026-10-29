# -*- coding: utf-8 -*-
"""
幻熊输入法 · 虚幻引擎候选框跟随修正  (HuanxiongCaretFix)

为什么需要它
------------
虚幻引擎走 TSF 输入，但它回报给输入法的插入符位置恒为 (0,0)（上游 issue
rime/weasel#1023）。weasel 前端拿到 (0,0) 时会直接放弃设置候选窗位置，
于是候选窗停留在上一次的位置或屏幕左上角，就是不跟光标。

本工具在进程外接管：当前台是虚幻编辑器、幻熊候选窗出现时，把候选窗移到
鼠标附近（点击输入框后鼠标通常就停在那儿）。不改虚幻，不改输入法。
"""
import ctypes
import os
import sys
import time
from ctypes import wintypes

try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

u32 = ctypes.windll.user32
k32 = ctypes.windll.kernel32

BASE = os.path.join(os.environ.get('LOCALAPPDATA', os.path.expanduser('~')),
                    'HuanxiongCaretFix')
try:
    os.makedirs(BASE, exist_ok=True)
except Exception:
    BASE = os.path.dirname(os.path.abspath(__file__))
LOG = os.path.join(BASE, 'caretfix.log')

# WeaselServer 里与候选窗无关的窗口，跳过
SKIP_CLASSES = {
    'TrayIconClass',
    'WeaselIPCWindow_1.0',
    'GDI+ Hook Window Class',
    'IME',
    'MSCTFIME UI',
}
UE_PROCS = ('unrealeditor', 'ue4editor', 'ue5editor', 'unrealpak')
POLL = 0.04
NEAR = 60          # 已经在鼠标附近就不动，避免抖动
OFFSET_X = -2      # 候选窗左上角相对鼠标的偏移
OFFSET_Y = 26


def log(msg):
    try:
        if os.path.exists(LOG) and os.path.getsize(LOG) > 1024 * 512:
            os.replace(LOG, LOG + '.old')
        with open(LOG, 'a', encoding='utf-8') as f:
            f.write('%s  %s\n' % (time.strftime('%m-%d %H:%M:%S'), msg))
    except Exception:
        pass


def proc_name(pid):
    h = k32.OpenProcess(0x1000, False, pid)
    if not h:
        return ''
    buf = ctypes.create_unicode_buffer(1024)
    size = ctypes.c_ulong(1024)
    ok = k32.QueryFullProcessImageNameW(h, 0, buf, ctypes.byref(size))
    k32.CloseHandle(h)
    return os.path.basename(buf.value) if ok else ''


def find_panels():
    """返回 WeaselServer 进程下可见的候选窗 [(hwnd, x, y, w, h), ...]

    weasel 的候选窗用 ATL 自动类名（ATL:xxxx），无法按类名匹配，
    改用窗口样式特征：分层窗口 + 工具窗 + 不抢焦点（顶部对齐）。
    """
    out = []

    @ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    def cb(hwnd, lparam):
        if not u32.IsWindowVisible(hwnd):
            return True
        ex = u32.GetWindowLongW(hwnd, -20) & 0xFFFFFFFF
        WS_EX_LAYERED = 0x00080000
        WS_EX_TOOLWINDOW = 0x00000080
        WS_EX_NOACTIVATE = 0x08000000
        if not (ex & WS_EX_LAYERED) or not (ex & WS_EX_TOOLWINDOW):
            return True
        if not (ex & WS_EX_NOACTIVATE):
            return True
        pid = wintypes.DWORD()
        u32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        if 'weaselserver' not in proc_name(pid.value).lower():
            return True
        r = wintypes.RECT()
        u32.GetWindowRect(hwnd, ctypes.byref(r))
        w, h = r.right - r.left, r.bottom - r.top
        if w <= 0 or h <= 0:
            return True
        out.append((hwnd, r.left, r.top, w, h))
        return True

    u32.EnumWindows(cb, 0)
    return out


def foreground():
    h = u32.GetForegroundWindow()
    pid = wintypes.DWORD()
    u32.GetWindowThreadProcessId(h, ctypes.byref(pid))
    return h, proc_name(pid.value)


def cursor():
    p = wintypes.POINT()
    u32.GetCursorPos(ctypes.byref(p))
    return p.x, p.y


def place(hwnd, x, y, w, h):
    """把候选窗放到 (x,y)，并确保不超出屏幕"""
    m = u32.MonitorFromPoint(wintypes.POINT(x, y), 2)  # MONITOR_DEFAULTTONEAREST
    if m:
        class MI(ctypes.Structure):
            _fields_ = [('cbSize', wintypes.DWORD), ('rcMonitor', wintypes.RECT),
                        ('rcWork', wintypes.RECT), ('dwFlags', wintypes.DWORD)]
        mi = MI()
        mi.cbSize = ctypes.sizeof(MI)
        if u32.GetMonitorInfoW(m, ctypes.byref(mi)):
            x = max(mi.rcWork.left, min(x, mi.rcWork.right - w))
            y = max(mi.rcWork.top, min(y, mi.rcWork.bottom - h))
    u32.SetWindowPos(hwnd, 0, x, y, 0, 0, 0x0001 | 0x0004 | 0x0010)


def main():
    log('--- HuanxiongCaretFix 启动 pid=%d ---' % os.getpid())
    sessions = {}   # hwnd -> 已处理标记
    quiet_until = 0.0
    while True:
        try:
            panels = find_panels()
            alive = set(p[0] for p in panels)
            for h in list(sessions):
                if h not in alive:
                    del sessions[h]

            if panels:
                _, pname = foreground()
                pl = pname.lower()
                is_ue = any(pl.startswith(p) for p in UE_PROCS)
                for hwnd, x, y, w, h in panels:
                    if hwnd in sessions:
                        continue
                    sessions[hwnd] = True
                    if not is_ue:
                        continue
                    mx, my = cursor()
                    if abs(x - mx) < NEAR and abs(y - my) < NEAR:
                        log('候选窗 hwnd=%s 已在鼠标附近 (%d,%d)，不干预' % (hwnd, x, y))
                        continue
                    if time.time() < quiet_until:
                        continue
                    tx, ty = mx + OFFSET_X, my + OFFSET_Y
                    place(hwnd, tx, ty, w, h)
                    log('候选窗 hwnd=%s (%d,%d,%dx%d) -> 鼠标 (%d,%d)'
                        % (hwnd, x, y, w, h, tx, ty))
            time.sleep(POLL)
        except KeyboardInterrupt:
            break
        except Exception as e:
            log('ERR %r' % (e,))
            quiet_until = time.time() + 3
            time.sleep(0.3)
    log('--- 退出 ---')


if __name__ == '__main__':
    main()
