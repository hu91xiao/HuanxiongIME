# -*- coding: utf-8 -*-
"""撤销 reg_imm.py 做的全部改动"""
import ctypes
import os
import sys
import winreg

_LOG = open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         "unreg_imm.log"), "w", encoding="utf-8")


class _Tee(object):
    def write(self, s):
        sys.__stdout__.write(s)
        _LOG.write(s)

    def flush(self):
        sys.__stdout__.flush()
        _LOG.flush()


sys.stdout = _Tee()

KLID = "e0240804"
KLID_KEY = r"SYSTEM\CurrentControlSet\Control\Keyboard Layouts\E0240804"
IME_NAME = "weasel_legacy.ime"
SYS64 = os.path.join(os.environ["SystemRoot"], "System32")
SYS32 = os.path.join(os.environ["SystemRoot"], "SysWOW64")

ILOT_UNINSTALL = 0x00000001

dll = ctypes.WinDLL("input.dll")
dll.InstallLayoutOrTip.argtypes = [ctypes.c_wchar_p, ctypes.c_ulong]
dll.InstallLayoutOrTip.restype = ctypes.c_long
dll.InstallLayoutOrTipUserReg.argtypes = [ctypes.c_wchar_p, ctypes.c_wchar_p,
                                          ctypes.c_wchar_p, ctypes.c_ulong]
dll.InstallLayoutOrTipUserReg.restype = ctypes.c_long

spec = "0804:%s" % KLID
print("InstallLayoutOrTip 卸载 -> 0x%08X" % (dll.InstallLayoutOrTip(spec, ILOT_UNINSTALL) & 0xFFFFFFFF))
print("InstallLayoutOrTipUserReg 卸载 -> 0x%08X" % (dll.InstallLayoutOrTipUserReg(None, None, spec, ILOT_UNINSTALL) & 0xFFFFFFFF))

try:
    winreg.DeleteKey(winreg.HKEY_LOCAL_MACHINE, KLID_KEY)
    print("已删除注册项", KLID_KEY)
except OSError as e:
    print("删除注册项失败：", e)

for d in (SYS64, SYS32):
    p = os.path.join(d, IME_NAME)
    if os.path.isfile(p):
        try:
            os.remove(p)
            print("已删除", p)
        except OSError as e:
            print("删除失败（可能被占用，重启后消失）：", p, e)
print("撤销完成，重新登录后语言栏里的「兼容」项会消失。")
