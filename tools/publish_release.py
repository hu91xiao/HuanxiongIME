# -*- coding: utf-8 -*-
"""
把 dist/ 里的安装包发到 GitHub Releases，并一并带上 install.ps1。

用法：
    python tools/publish_release.py 1.1 "修了候选窗配色"

版本已存在时不会报错退出，而是只补传缺失的附件（用来给老 release 补 install.ps1）。

注意：GitHub 的附件名（asset name）只允许 ASCII，中文会被静默过滤成
「-1.0-.exe」这种残骸。所以文件名用 HuanxiongIME-<版本>-Setup.exe，
中文标题放在 label 里，下载页显示的还是中文。

依赖：只用标准库。代理读 HTTPS_PROXY。
"""
import glob
import json
import os
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request

REPO = "hu91xiao/HuanxiongIME"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIST = os.path.join(ROOT, "dist")
SCRIPT = os.path.join(ROOT, "install.ps1")


def get_token():
    tok = os.environ.get("GHT", "").strip()
    if tok:
        return tok
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
_handlers = [urllib.request.ProxyHandler({"http": PROXY, "https": PROXY})] if PROXY else []
OPENER = urllib.request.build_opener(*_handlers)


def call(url, data=None, method=None, ctype="application/json", timeout=1800):
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", "Bearer " + TOKEN)
    req.add_header("Accept", "application/vnd.github+json")
    if data:
        req.add_header("Content-Type", ctype)
    with OPENER.open(req, timeout=timeout) as resp:
        raw = resp.read()
        return json.loads(raw.decode("utf-8")) if raw else {}


def find_exe(ver):
    """dist 里按版本号找中文名的安装包；找不到就退回任意一个。"""
    want = [p for p in glob.glob(os.path.join(DIST, "幻熊输入法-*-安装程序.exe"))
            if ver in os.path.basename(p)]
    if want:
        return want[0]
    any_exe = sorted(glob.glob(os.path.join(DIST, "幻熊输入法-*-安装程序.exe")))
    return any_exe[0] if any_exe else None


def upload(rel, path, name, label):
    for a in rel.get("assets", []):
        if a["name"] == name:
            print("   已存在 %s，跳过" % name)
            return a
    url = rel["upload_url"].split("{")[0]
    url += "?name=" + urllib.parse.quote(name) + "&label=" + urllib.parse.quote(label)
    print("→ 上传 %s（%.1f MB）" % (name, os.path.getsize(path) / 1048576.0))
    a = call(url, open(path, "rb").read(), method="POST", ctype="application/octet-stream")
    print("   完成: %s | 显示名: %s" % (a["name"], a.get("label")))
    print("   下载: %s" % a["browser_download_url"])
    return a


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    ver = sys.argv[1].lstrip("v")
    note = sys.argv[2] if len(sys.argv) > 2 else ""

    exe = find_exe(ver)
    if not exe:
        sys.exit("找不到安装包（dist/幻熊输入法-*-安装程序.exe）\n先跑 python build.py installer")
    if not os.path.isfile(SCRIPT):
        sys.exit("找不到 install.ps1")

    body = ("## 用 AI 一键装\n\n"
            "```\nirm https://github.com/%s/releases/latest/download/install.ps1 | iex\n```\n\n"
            "或在某台能跑命令的 AI（Claude Code / Cursor / WorkBuddy…）里说：\n"
            "「执行上面这行，装完告诉我输入法有没有注册成功」。\n\n"
            "## 手动装\n\n"
            "下载 `HuanxiongIME-%s-Setup.exe` → 双击 → 更多信息 → 仍要运行"
            "（没有代码签名）→ 一路下一步。装完按 Win+空格 切到「幻熊输入法」。\n\n"
            "---\n\n许可 GPL-3.0，基于 Rime 小狼毫 0.17.4。\n" % (REPO, ver))
    if note:
        body = note + "\n\n" + body

    print("→ 发布 v%s（%s，%.1f MB）" % (ver, os.path.basename(exe), os.path.getsize(exe) / 1048576.0))
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
        print("   v%s 已存在，改为补传缺失附件" % ver)
        rel = call("https://api.github.com/repos/%s/releases/tags/v%s" % (REPO, ver))

    upload(rel, exe, "HuanxiongIME-%s-Setup.exe" % ver, "幻熊输入法 %s 安装程序" % ver)
    upload(rel, SCRIPT, "install.ps1", "一键安装脚本")

    print("\n完成。")
    print("  一键装： irm https://github.com/%s/releases/latest/download/install.ps1 | iex" % REPO)
    print("  安装包： https://github.com/%s/releases/latest/download/HuanxiongIME-%s-Setup.exe"
          % (REPO, ver))


if __name__ == "__main__":
    TOKEN = get_token()
    main()
