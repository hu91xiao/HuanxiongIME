# -*- coding: utf-8 -*-
"""
转储/恢复「幻熊输入法」在注册表里的全部注册信息。

用途：
  1) 备份 —— 卸载输入法前先存一份，出问题能原样恢复；
  2) 核对 —— 看看到底注册了哪些键（排查「语言栏里没有它」这类问题）；
  3) 兜底 —— 万一 WeaselSetup.exe 注册失败，可以直接按转储内容补回。

用法：
  python ime_registry.py dump  ime_registry.json
  python ime_registry.py restore ime_registry.json
"""
import json
import sys
import winreg

CLSID = "{A3F4CDED-B1E9-41EE-9CA6-7B4D0DE6CB0A}"
PATH = "{3D02CAB6-2B8E-4781-BA20-1C9267529467}"

TREE = [
    (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Classes\CLSID\%s" % CLSID),
    (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\CTF\TIP\%s" % CLSID),
    (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Classes\CLSID\%s" % CLSID),
    (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\CTF\TIP\%s" % CLSID),
    (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Rime\Weasel"),
    (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Rime\Weasel"),
    (winreg.HKEY_CURRENT_USER, r"Software\Rime\Weasel"),
    (winreg.HKEY_CURRENT_USER, r"Control Panel\International\User Profile"),
    (winreg.HKEY_CURRENT_USER, r"Control Panel\International\User Profile System Backup"),
    (winreg.HKEY_LOCAL_MACHINE,
     r"SYSTEM\CurrentControlSet\Control\Keyboard Layouts\E0240804"),
    (winreg.HKEY_CURRENT_USER, r"Keyboard Layout\Preload"),
    (winreg.HKEY_CURRENT_USER, r"Keyboard Layout\Substitutes"),
    (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\CTF\Assemblies"),
    (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\CTF\SortOrder"),
]

HIVES = {winreg.HKEY_LOCAL_MACHINE: "HKLM", winreg.HKEY_CURRENT_USER: "HKCU"}


def walk(hive, path, out):
    """把一个键连同子键、值全部抓下来"""
    try:
        key = winreg.OpenKey(hive, path)
    except OSError:
        return
    node = {"values": {}, "keys": {}}
    i = 0
    while True:
        try:
            name, data, typ = winreg.EnumValue(key, i)
        except OSError:
            break
        node["values"][name or ""] = [typ, data.hex() if isinstance(data, bytes) else data]
        i += 1
    i = 0
    while True:
        try:
            sub = winreg.EnumKey(key, i)
        except OSError:
            break
        child = {}
        walk(hive, path + "\\" + sub, child)
        node["keys"][sub] = child
        i += 1
    winreg.CloseKey(key)
    out.update(node)


def write(hive, path, node):
    key = winreg.CreateKeyEx(hive, path, 0, winreg.KEY_WRITE)
    for name, (typ, data) in node.get("values", {}).items():
        val = bytes.fromhex(data) if isinstance(data, str) and typ == winreg.REG_BINARY else data
        winreg.SetValueEx(key, name, 0, typ, val)
    for sub, child in node.get("keys", {}).items():
        write(hive, path + "\\" + sub, child)
    winreg.CloseKey(key)


def remove_tree(hive, path):
    try:
        keys = []
        key = winreg.OpenKey(hive, path)
        i = 0
        while True:
            try:
                keys.append(winreg.EnumKey(key, i))
            except OSError:
                break
            i += 1
        winreg.CloseKey(key)
        for k in keys:
            remove_tree(hive, path + "\\" + k)
        winreg.DeleteKey(hive, path)
    except OSError:
        pass


def dump(dst):
    data = []
    for hive, path in TREE:
        node = {}
        walk(hive, path, node)
        if node:
            data.append({"hive": HIVES[hive], "path": path, "tree": node})
            print("+ %s\\%s" % (HIVES[hive], path))
    with open(dst, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    print("已写入 %s（%d 个键）" % (dst, len(data)))


def restore(src, clean=False):
    with open(src, encoding="utf-8") as f:
        data = json.load(f)
    rev = {v: k for k, v in HIVES.items()}
    for item in data:
        hive = rev[item["hive"]]
        if clean:
            remove_tree(hive, item["path"])
        write(hive, item["path"], item["tree"])
        print("~ %s\\%s" % (item["hive"], item["path"]))
    print("恢复完成，注销或重启后语言栏才会刷新")


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "dump"
    arg = sys.argv[2] if len(sys.argv) > 2 else "ime_registry.json"
    if mode == "dump":
        dump(arg)
    elif mode == "restore":
        restore(arg, clean="--clean" in sys.argv)
    else:
        print(__doc__)
