# -*- coding: utf-8 -*-
"""
把 dist/ 里的安装包发到 GitHub Releases。

用法：
    set GHT=<你的 GitHub token>          # 或先跑 git credential fill
    python tools/publish_release.py 1.0.1 "修了候选窗配色"

注意：GitHub 的附件名（asset name）只允许 ASCII，中文会被静默过滤成
「-1.0-.exe」这种残骸。所以文件名用 HuanxiongIME-<版本>-Setup.exe，
中文标题放在 label 里，下载页显示的还是中文。

依赖：只用标准库。走系统代理（读 HTTPS_PROXY）。
"""
import json
import os
import subprocess
import sys
import urllib.parse
import urllib.request

REPO = "hu91xiao/HuanxiongIME"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIST = os.path.join(ROOT, "dist")
LOCAL_EXE = "幻熊输入法-1.0-安装程序.exe"   # dist 里的中文名，改版本号时同步改这里


def get_token():
    tok = os.environ.get("GHT", "").strip()
    if tok:
        return tok
    # 退而求其次：问 Git Credential Manager 要
    try:
        out = subprocess.run(
            ["git", "credential", "fill"],
            input="protocol=https\nhost=github.com\n\n",
            capture_output=True, text=True, timeout=60,
        ).stdout
        for line in out.splitlines():
            if line.startswith("password="):
                return line.split("=", 1)[1]
    except Exception:                                       # noqa: BLE001
        pass
    sys.exit("拿不到 token：设环境变量 GHT，或先 git credential-manager github login")


PROXY = os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy") or ""
handlers = [urllib.request.ProxyHandler({"http": PROXY, "https": PROXY})] if PROXY else []
OPENER = urllib.request.build_opener(*handlers)


def call(url, data=None, method=None, ctype="application/json", timeout=1800):
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", "Bearer " + TOKEN)
    req.add_header("Accept", "application/vnd.github+json")
    if data:
        req.add_header("Content-Type", ctype)
    with OPENER.open(req, timeout=timeout) as resp:
        raw = resp.read()
        return json.loads(raw.decode("utf-8")) if raw else {}


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    ver = sys.argv[1].lstrip("v")
    note = sys.argv[2] if len(sys.argv) > 2 else ""

    exe = os.path.join(DIST, LOCAL_EXE)
    if not os.path.isfile(exe):
        sys.exit("找不到安装包：%s\n先跑 python build.py installer" % exe)

    asset_name = "HuanxiongIME-%s-Setup.exe" % ver
    size = os.path.getsize(exe)
    print("→ 发布 v%s（%.1f MB）" % (ver, size / 1048576.0))

    body = note + ("\n\n---\n\n安装：下载 → 双击 → 更多信息 → 仍要运行（没有代码签名）→ 一路下一步。\n"
                   "装完按 Win+空格 切到「幻熊输入法」。\n\n"
                   "许可 GPL-3.0，基于 Rime 小狼毫 0.17.4。\n") if note else ""
    try:
        rel = call("https://api.github.com/repos/%s/releases" % REPO,
                   json.dumps({
                       "tag_name": "v" + ver,
                       "target_commitish": "main",
                       "name": "幻熊输入法 " + ver,
                       "body": body,
                       "draft": False,
                       "prerelease": False,
                   }, ensure_ascii=False).encode("utf-8"),
                   method="POST")
        print("   页面:", rel["html_url"])
    except urllib.error.HTTPError as e:
        if e.code != 422:
            raise
        sys.exit("v%s 已存在。先删掉旧 release，或换个版本号。" % ver)

    url = rel["upload_url"].split("{")[0]
    url += "?name=" + urllib.parse.quote(asset_name)
    url += "&label=" + urllib.parse.quote("幻熊输入法 %s 安装程序" % ver)
    print("→ 上传 %s" % asset_name)
    a = call(url, open(exe, "rb").read(), method="POST", ctype="application/octet-stream")
    print("   完成: %s | 显示名: %s | %.1f MB" % (a["name"], a.get("label"), a["size"] / 1048576.0))
    print("   下载:", a["browser_download_url"])


if __name__ == "__main__":
    TOKEN = get_token()
    main()
