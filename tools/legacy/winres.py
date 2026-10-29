# -*- coding: utf-8 -*-
"""Windows 资源读写工具：PE 资源解析 / UpdateResource 封装 / VERSIONINFO 重建 / 图标替换"""
import ctypes
import ctypes.wintypes as wt
import os
import struct

RT_ICON = 3
RT_MENU = 4
RT_STRING = 6
RT_GROUP_ICON = 14
RT_VERSION = 16
LANG_EN_US = 0x0409


# ---------------------------------------------------------------- PE 解析
def pe_resources(path):
    """返回 [(path_tuple, file_offset, size, codepage)]"""
    data = open(path, "rb").read()
    e = struct.unpack_from("<I", data, 0x3C)[0]
    if data[e:e + 4] != b"PE\0\0":
        raise ValueError("not a PE file: %s" % path)
    coff = e + 4
    nsec = struct.unpack_from("<H", data, coff + 2)[0]
    opt_size = struct.unpack_from("<H", data, coff + 16)[0]
    opt = coff + 20
    magic = struct.unpack_from("<H", data, opt)[0]
    dd = opt + (112 if magic == 0x20B else 96)
    rsrc_rva = struct.unpack_from("<I", data, dd + 16)[0]
    if not rsrc_rva:
        return data, []
    rsrc_off = sec_raw = sec_va = None
    for i in range(nsec):
        s = opt + opt_size + i * 40
        if data[s:s + 8].rstrip(b"\0") == b".rsrc":
            vsize, vaddr, rawsize, rawptr = struct.unpack_from("<IIII", data, s + 8)
            rsrc_off = rawptr - vaddr + rsrc_rva
            sec_raw, sec_va = rawptr, vaddr
            break
    if rsrc_off is None:
        return data, []
    out = []

    def walk(off, acc):
        n_named, n_id = struct.unpack_from("<HH", data, off + 12)
        for i in range(n_named + n_id):
            e2 = off + 16 + i * 8
            nm, tgt = struct.unpack_from("<II", data, e2)
            if nm & 0x80000000:
                noff = rsrc_off + (nm & 0x7FFFFFFF)
                ln = struct.unpack_from("<H", data, noff)[0]
                label = data[noff + 2:noff + 2 + ln * 2].decode("utf-16-le", "replace")
            else:
                label = nm
            if tgt & 0x80000000:
                walk(rsrc_off + (tgt & 0x7FFFFFFF), acc + [label])
            else:
                doff, dsize, cp, _ = struct.unpack_from("<IIII", data, rsrc_off + tgt)
                out.append((tuple(acc + [label]), sec_raw + (doff - sec_va), dsize, cp))
    walk(rsrc_off, [])
    return data, out


class ResFile(object):
    """BeginUpdateResource 包装，with 语句用"""

    def __init__(self, path, delete=False):
        self.path = path
        self.h = K.BeginUpdateResourceW(path, delete)
        if not self.h:
            raise OSError("BeginUpdateResource 失败 err=%d（文件被占用或无权限）" % ctypes.get_last_error())

    def update(self, rtype, rname, lang, data):
        buf = ctypes.create_string_buffer(data, len(data)) if data else None
        ok = K.UpdateResourceW(self.h, rtype, rname, lang, buf, len(data) if data else 0)
        if not ok:
            raise OSError("UpdateResource 失败 type=%r name=%r err=%d" % (rtype, rname, ctypes.get_last_error()))

    def __enter__(self):
        return self

    def __exit__(self, *a):
        if not K.EndUpdateResourceW(self.h, False):
            raise OSError("EndUpdateResource 失败 err=%d" % ctypes.get_last_error())
        return False


K = ctypes.WinDLL("kernel32", use_last_error=True)
K.BeginUpdateResourceW.argtypes = [wt.LPCWSTR, wt.BOOL]
K.BeginUpdateResourceW.restype = wt.HANDLE
K.UpdateResourceW.argtypes = [wt.HANDLE, wt.LPCWSTR, wt.LPCWSTR, wt.WORD,
                              ctypes.c_void_p, wt.DWORD]
K.UpdateResourceW.restype = wt.BOOL
K.EndUpdateResourceW.argtypes = [wt.HANDLE, wt.BOOL]
K.EndUpdateResourceW.restype = wt.BOOL


def _ptr(v):
    """数字资源名 → LPCWSTR 低位整数形式；字符串资源名 → 原样"""
    if isinstance(v, int):
        return ctypes.cast(ctypes.c_void_p(v), wt.LPCWSTR)
    return v


def update_res(path, rtype, rname, lang, data):
    with ResFile(path) as r:
        r.update(_ptr(rtype), _ptr(rname), lang, data)


# ------------------------------------------------------- VERSIONINFO
def _align4(n):
    return (n + 3) & ~3


def _read_wstr(data, off):
    end = off
    n = len(data)
    while end + 1 < n:
        if data[end] == 0 and data[end + 1] == 0:
            break
        end += 2
    return data[off:end].decode("utf-16-le", "replace"), end + 2


def parse_version(blob):
    """→ dict(fixed=bytes52, tables={tableKey: {k: v}}, varinfo=bytes|None, topkey=str)"""
    w_len, w_val, w_type = struct.unpack_from("<HHH", blob, 0)
    key, p = _read_wstr(blob, 6)
    p = _align4(p)
    fixed = blob[p:p + w_val]
    p = _align4(p + w_val)
    tables = {}
    varinfo = None
    while p + 6 <= min(w_len, len(blob)):
        clen, cval, ctype = struct.unpack_from("<HHH", blob, p)
        if clen == 0:
            break
        ckey, cp = _read_wstr(blob, p + 6)
        if ckey == "StringFileInfo":
            cp = _align4(cp)
            end = p + clen
            while cp + 6 <= end:
                tlen, tval, ttype = struct.unpack_from("<HHH", blob, cp)
                if tlen == 0:
                    break
                tkey, tp = _read_wstr(blob, cp + 6)
                tp = _align4(tp)
                d = {}
                while tp + 6 <= cp + tlen:
                    slen, sval, stype = struct.unpack_from("<HHH", blob, tp)
                    if slen == 0:
                        break
                    skey, sp = _read_wstr(blob, tp + 6)
                    sp = _align4(sp)
                    raw = blob[sp:sp + sval * 2]
                    d[skey] = raw.decode("utf-16-le", "replace").rstrip("\0")
                    tp = _align4(tp + slen)
                tables[tkey] = d
                cp = _align4(cp + tlen)
        elif ckey == "VarFileInfo":
            varinfo = blob[p:p + clen]
        p = _align4(p + clen)
    return {"key": key, "fixed": fixed, "tables": tables, "varinfo": varinfo}


def _node(key, value_len, type_, value_bytes, children):
    """wLength 按 Windows 实际读法：不含末尾对齐用的填充"""
    hdr = 6 + (len(key) + 1) * 2
    pad = _align4(hdr) - hdr
    body = value_bytes + children
    real = hdr + pad + len(body)
    total = _align4(real)
    tail = total - real
    return (struct.pack("<HHH", real, value_len, type_)
            + key.encode("utf-16-le") + b"\0\0" + b"\0" * pad
            + body + b"\0" * tail)


def _string_node(key, val):
    data = val.encode("utf-16-le") + b"\0\0"
    return _node(key, len(val) + 1, 1, data, b"")


def build_version(fixed, tables, varinfo=None):
    sfi_children = b""
    for tkey, d in tables.items():
        kids = b"".join(_string_node(k, v) for k, v in d.items())
        sfi_children += _node(tkey, 0, 1, b"", kids)
    sfi = _node("StringFileInfo", 0, 1, b"", sfi_children)
    body = fixed + sfi + (varinfo or b"")
    return _node("VS_VERSION_INFO", len(fixed), 0, fixed, sfi + (varinfo or b""))


def rewrite_version(path, lang, changes, drop_keys=()):
    """只改指定语言的 VERSION 资源里 StringFileInfo 的若干键"""
    if isinstance(lang, str):
        lang = int(lang, 16)
    data, ents = pe_resources(path)
    for p, off, size, cp in ents:
        if p[0] == RT_VERSION and p[2] == lang:
            v = parse_version(data[off:off + size])
            for tkey in list(v["tables"]):
                for k, val in changes.items():
                    if k in v["tables"][tkey]:
                        v["tables"][tkey][k] = val
                for k in drop_keys:
                    v["tables"][tkey].pop(k, None)
            blob = build_version(v["fixed"], v["tables"], v["varinfo"])
            update_res(path, RT_VERSION, p[1], lang, blob)
            return True, v["tables"]
    return False, None


def version_langs(path):
    data, ents = pe_resources(path)
    return sorted({p[2] for p, off, s, c in ents if p[0] == RT_VERSION})


# ------------------------------------------------------- 图标
def icons_from_ico(ico_path, want_sizes=(256, 64, 48, 32, 24, 16)):
    """把 .ico 拆成 [(size, png_or_dib_bytes, bpp, planes)]"""
    from PIL import Image
    import io as _io
    out = []
    for s in want_sizes:
        bio = _io.BytesIO()
        im = Image.open(ico_path).convert("RGBA")
        im.save(bio, format="ICO", sizes=[(s, s)])
        blob = bio.getvalue()
        # 解析单尺寸 ICO，取出图像数据
        cnt = struct.unpack_from("<H", blob, 4)[0]
        for i in range(cnt):
            b = 6 + i * 16
            w, h, ncol, rsv, planes, bpp, dsize, doff = struct.unpack_from("<BBBBHHII", blob, b)
            if (w or 256) == s:
                out.append((s, blob[doff:doff + dsize], bpp or 32, planes or 1))
                break
    return out


def group_icon_blob(items):
    """items: [(size, bpp, planes, bytes_len, icon_id)] → GRPICONDIR"""
    blob = struct.pack("<HHH", 0, 1, len(items))
    for (size, bpp, planes, blen, iid) in items:
        v = 0 if size >= 256 else size
        blob += struct.pack("<BBBBHHIH", v, v, 0, 0, planes, bpp, blen, iid)
    return blob


def replace_icon_group(path, group_id, png_by_size, lang=1033):
    """把 group_id 这一组图标换成 png_by_size[(size)] = icon_bytes"""
    data, ents = pe_resources(path)
    # 找出该 group 原来的 ICON id 列表，逐个覆盖（数量一致时不新增资源）
    old = None
    for p, off, size, cp in ents:
        if p[0] == RT_GROUP_ICON and p[1] == group_id:
            old = parse_group_icon(data[off:off + size])
            break
    if old is None:
        raise ValueError("找不到 group %s" % group_id)
    entries = []
    for idx, (w, h, ncol, rsv, planes, bpp, blen, iid) in enumerate(old):
        key = 256 if w == 0 else w
        blob = png_by_size.get(key)
        if blob is None:
            entries.append((w, bpp, planes, blen, iid))
            continue
        update_res(path, RT_ICON, iid, lang, blob)
        entries.append((key, bpp or 32, planes or 1, len(blob), iid))
    return entries


def parse_group_icon(blob):
    rsv, typ, cnt = struct.unpack_from("<HHH", blob, 0)
    out = []
    for i in range(cnt):
        b = 6 + i * 14
        w, h, ncol, rsv2, planes, bpp, blen, iid = struct.unpack_from("<BBBBHHIH", blob, b)
        out.append((w, h, ncol, rsv2, planes, bpp, blen, iid))
    return out


def write_group_icon(path, group_id, entries, lang=1033):
    blob = group_icon_blob([(e[0], e[1], e[2], e[3], e[4]) for e in entries])
    update_res(path, RT_GROUP_ICON, group_id, lang, blob)


# ------------------------------------------------------- PNG → DIB
def png_to_dib(png_path):
    """把 PNG 转成图标用的 DIB（BITMAPINFOHEADER + 自下而上 BGRA + AND mask）"""
    from PIL import Image
    im = Image.open(png_path).convert("RGBA")
    w, h = im.size
    px = im.load()
    rows = []
    for y in range(h - 1, -1, -1):
        row = bytearray()
        for x in range(w):
            r, g, b, a = px[x, y]
            row += bytes((b, g, r, a))
        rows.append(bytes(row))
    xor = b"".join(rows)
    stride = ((w + 31) // 32) * 4
    and_mask = b"\x00" * (stride * h)
    hdr = struct.pack("<IiiHHIIiiII", 40, w, h * 2, 1, 32, 0,
                      len(xor) + len(and_mask), 0, 0, 0, 0)
    return hdr + xor + and_mask


def load_icon_set(icon_dir, variant, sizes=(256, 64, 48, 32, 24, 16)):
    """{size: bytes}；256 用 PNG（Vista+ 支持），其余转 DIB 保证兼容"""
    out = {}
    for s in sizes:
        p = os.path.join(icon_dir, "%s_%d.png" % (variant, s))
        if s == 256:
            out[s] = open(p, "rb").read()
        else:
            out[s] = png_to_dib(p)
    return out


# ------------------------------------------------------- 批量改
def rebrand_version(path, per_table):
    """per_table: {table_key: {k: v}}，table_key 小写；'*' 表示所有 table 兜底"""
    data, ents = pe_resources(path)
    jobs = []
    for p, off, size, cp in ents:
        if p[0] != RT_VERSION:
            continue
        v = parse_version(data[off:off + size])
        changed = False
        for tkey, d in v["tables"].items():
            rule = per_table.get(tkey.lower()) or per_table.get("*") or {}
            for k, val in rule.items():
                if k in d:
                    d[k] = val
                    changed = True
        if changed:
            jobs.append((p[1], p[2], build_version(v["fixed"], v["tables"], v["varinfo"])))
    if not jobs:
        return 0
    with ResFile(path) as r:
        for name, lang, blob in jobs:
            r.update(_ptr(RT_VERSION), _ptr(name), lang, blob)
    return len(jobs)


def rebrand_icons(path, group_map):
    """group_map: {group_id: {size: bytes}}，按原尺寸覆盖对应 ICON 资源"""
    data, ents = pe_resources(path)
    icon_jobs = []
    group_jobs = []
    for gid, by_size in group_map.items():
        for p, off, size, cp in ents:
            if p[0] == RT_GROUP_ICON and p[1] == gid:
                old = parse_group_icon(data[off:off + size])
                entries = []
                for (w, h, ncol, rsv, planes, bpp, blen, iid) in old:
                    key = 256 if w == 0 else w
                    blob = by_size.get(key)
                    if blob:
                        icon_jobs.append((iid, p[2], blob))
                        entries.append((key, 32, planes or 1, len(blob), iid))
                    else:
                        entries.append((key, bpp or 32, planes or 1, blen, iid))
                group_jobs.append((gid, p[2], entries))
                break
    if not icon_jobs:
        return 0
    with ResFile(path) as r:
        for iid, lang, blob in icon_jobs:
            r.update(_ptr(RT_ICON), _ptr(iid), lang, blob)
        for gid, lang, entries in group_jobs:
            r.update(_ptr(RT_GROUP_ICON), _ptr(gid), lang, group_icon_blob(entries))
    return len(icon_jobs)


def drop_resources(path, items):
    """items: [(type, name, lang)] —— 删除资源"""
    with ResFile(path) as r:
        for t, n, l in items:
            r.update(_ptr(t), _ptr(n), l, None)


def menu_blob(items, popup_text="WeaselTray"):
    """items: [(id, text)] 或 None（分隔线）"""
    out = struct.pack("<HH", 0, 0)
    out += struct.pack("<H", 0x0010 | 0x0080)
    out += popup_text.encode("utf-16-le") + b"\x00\x00"
    for i, it in enumerate(items):
        last = (i == len(items) - 1)
        flags, mid, text = (0, 0, "") if it is None else (0, it[0], it[1])
        if last:
            flags |= 0x0080
        out += struct.pack("<HH", flags, mid) + text.encode("utf-16-le") + b"\x00\x00"
    return out


# ------------------------------------------------------- 字符串表（RT_STRING）
def parse_string_block(blob):
    """RT_STRING 一块 = 16 个「WORD 长度 + UTF-16 字符」"""
    out, p = [], 0
    for _ in range(16):
        if p + 2 > len(blob):
            out.append("")
            continue
        ln = struct.unpack_from("<H", blob, p)[0]
        p += 2
        out.append(blob[p:p + ln * 2].decode("utf-16-le", "replace"))
        p += ln * 2
    return out


def build_string_block(items):
    b = b""
    for s in list(items)[:16]:
        b += struct.pack("<H", len(s)) + s.encode("utf-16-le")
    return b


def rebrand_strings(path, mapping):
    """把字符串表里出现的 mapping 键换成对应的值（长度可以不同）"""
    data, ents = pe_resources(path)
    jobs = []
    for p, off, size, cp in ents:
        if p[0] != RT_STRING:
            continue
        try:
            items = parse_string_block(data[off:off + size])
        except Exception:                                   # noqa: BLE001
            continue
        new, changed = [], False
        for s in items:
            t = s
            for k, v in mapping.items():
                if k in t:
                    t = t.replace(k, v)
                    changed = True
            new.append(t)
        if changed:
            jobs.append((p[1], p[2], build_string_block(new)))
    if not jobs:
        return 0
    with ResFile(path) as r:
        for name, lang, blob in jobs:
            r.update(_ptr(RT_STRING), _ptr(name), lang, blob)
    return len(jobs)
