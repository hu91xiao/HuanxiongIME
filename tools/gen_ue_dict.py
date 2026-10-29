# -*- coding: utf-8 -*-
"""
把虚幻/游戏术语补进码表（五笔 + 拼音）。

做三件事：
1. 从 wubi86_jidian.dict.yaml 里取每个字的全码（最长的那个码）
2. 按 86 五笔的词组规则算出词条的编码
   - 二字词：两字各取前两码
   - 三字词：前两字各取第一码 + 第三字前两码
   - 四字词：每字各取第一码
   - 五字及以上：前三字各取第一码 + 末字第一码
3. 拼音同理：从 pinyin_simp.dict.yaml 取单字读音（取权重最高的那个音），直接拼起来

只补码表里没有的词（已有的不动）。写入带标记块，重复跑会先删旧块再加，不会重复。
"""
import os
import re
import sys

RIME = os.path.join(os.environ.get("APPDATA", ""), "Rime")
F_WUBI = os.path.join(RIME, "wubi86_jidian.dict.yaml")
F_WUBI_EXTRA = os.path.join(RIME, "wubi86_jidian_extra.dict.yaml")
F_WUBI_USER = os.path.join(RIME, "wubi86_jidian_user.dict.yaml")
F_PINYIN = os.path.join(RIME, "pinyin_simp.dict.yaml")
F_UE = os.path.join(RIME, "ue_terms.lua")
F_LUA = os.path.join(RIME, "rime.lua")

MARK_WUBI = "## @@UE_TERMS@@ 虚幻/游戏术语（脚本生成，重跑会覆盖这一块）"
MARK_PINYIN = "# @@UE_TERMS@@ 虚幻/游戏术语（脚本生成，重跑会覆盖这一块）"
WEIGHT_WUBI = "9999"
WEIGHT_PINYIN = "9999"


def read(p):
    with open(p, "r", encoding="utf-8", errors="replace") as f:
        return f.read()


def entries(text):
    """码表正文：跳过 yaml 头（--- 到 ... 之间）"""
    lines = text.splitlines()
    start = 0
    for i, ln in enumerate(lines):
        if ln.strip() == "...":
            start = i + 1
            break
    return lines, start


def char_codes(path):
    """单字 -> 全码（同一字有多个码时取最长的）"""
    out = {}
    text = read(path)
    lines, start = entries(text)
    for ln in lines[start:]:
        if not ln or ln.startswith("#"):
            continue
        parts = ln.split("\t")
        if len(parts) < 2:
            continue
        w, code = parts[0], parts[1].strip()
        if len(w) != 1:
            continue
        if not re.match(r"^[a-z]+$", code) or code.startswith("z"):
            continue
        if w not in out or len(code) > len(out[w]):
            out[w] = code
    return out


def char_pinyin(path):
    """单字 -> 读音（取权重最高的那个）"""
    out = {}
    best = {}
    text = read(path)
    lines, start = entries(text)
    for ln in lines[start:]:
        if not ln or ln.startswith("#"):
            continue
        parts = ln.split("\t")
        if len(parts) < 2 or len(parts[0]) != 1:
            continue
        w, py = parts[0], parts[1].strip()
        if not re.match(r"^[a-z]+$", py):
            continue
        try:
            wgt = float(parts[2]) if len(parts) > 2 else 0
        except ValueError:
            wgt = 0
        if w not in best or wgt > best[w]:
            best[w] = wgt
            out[w] = py
    return out


def word_codes(w, codes):
    """按 86 五笔词组规则算编码"""
    n = len(w)
    cs = [codes.get(ch) for ch in w]
    if any(c is None for c in cs):
        return None
    if any(len(c) < 2 for c in cs):
        return None
    if n == 2:
        return cs[0][:2] + cs[1][:2]
    if n == 3:
        return cs[0][:1] + cs[1][:1] + cs[2][:2]
    if n == 4:
        return "".join(c[:1] for c in cs)
    return cs[0][:1] + cs[1][:1] + cs[2][:1] + cs[-1][:1]


def word_pinyin(w, pys):
    if any(ch not in pys for ch in w):
        return None
    code = "".join(pys[ch] for ch in w)
    return code if len(code) <= 40 else None


def load_terms():
    """ue_terms.lua 的词 + rime.lua 手写表里的词，合在一起"""
    terms = {}
    pat = re.compile(r'\["([^"]+)"\]\s*=\s*"([^"]*)"')
    for p in (F_UE, F_LUA):
        if not os.path.isfile(p):
            continue
        for k, v in pat.findall(read(p)):
            if k and v and k not in terms:
                terms[k] = v
    return terms


def existing_words(paths):
    words = set()
    for p in paths:
        if not os.path.isfile(p):
            continue
        lines, start = entries(read(p))
        for ln in lines[start:]:
            if not ln or ln.startswith("#"):
                continue
            parts = ln.split("\t")
            if len(parts) >= 2 and parts[0]:
                words.add(parts[0])
    return words


def strip_block(text, mark):
    """删掉上次生成的块（标记行到最后一行都属于它，块永远追加在文件末尾）"""
    lines = text.splitlines()
    for i, ln in enumerate(lines):
        if ln.startswith(mark):
            return "\n".join(lines[:i]).rstrip("\n") + "\n"
    return text


def main():
    if not os.path.isfile(F_WUBI):
        print("找不到五笔码表：%s" % F_WUBI)
        return 1
    codes = char_codes(F_WUBI)
    if os.path.isfile(F_WUBI_EXTRA):
        for k, v in char_codes(F_WUBI_EXTRA).items():
            if k not in codes or len(v) > len(codes[k]):
                codes[k] = v
    pys = char_pinyin(F_PINYIN)
    print("单字五笔码 %d 个，单字拼音 %d 个" % (len(codes), len(pys)))

    terms = load_terms()
    have = existing_words([F_WUBI, F_WUBI_EXTRA, F_WUBI_USER, F_PINYIN])
    print("候选术语 %d 条，码表里已存在 %d 条"
          % (len(terms), sum(1 for t in terms if t in have)))

    wubi_rows, py_rows, skip = [], [], []
    for t in sorted(terms, key=lambda x: (-len(x), x)):
        if len(t) < 2 or t in have:
            continue
        wc = word_codes(t, codes)
        if wc and len(wc) == 4:
            wubi_rows.append("%s\t%s\t%s" % (t, wc, WEIGHT_WUBI))
        pc = word_pinyin(t, pys)
        if pc:
            py_rows.append("%s\t%s\t%s" % (t, pc, WEIGHT_PINYIN))
        if not wc and not pc:
            skip.append(t)

    print("五笔新增 %d 条，拼音新增 %d 条，两样都算不出 %d 条"
          % (len(wubi_rows), len(py_rows), len(skip)))
    for t in skip[:10]:
        print("  跳过：%s" % t)

    # 写五笔个人词库
    text = read(F_WUBI_USER)
    text = strip_block(text, MARK_WUBI)
    text = text.rstrip("\n") + "\n\n" + MARK_WUBI + "\n" + "\n".join(wubi_rows) + "\n"
    with open(F_WUBI_USER, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)

    # 写拼音码表
    text = read(F_PINYIN)
    text = strip_block(text, MARK_PINYIN)
    text = text.rstrip("\n") + "\n\n" + MARK_PINYIN + "\n" + "\n".join(py_rows) + "\n"
    with open(F_PINYIN, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)

    print("示例：")
    for row in wubi_rows[:6]:
        print("  五笔 " + row)
    for row in py_rows[:6]:
        print("  拼音 " + row)
    return 0


if __name__ == "__main__":
    sys.exit(main())
