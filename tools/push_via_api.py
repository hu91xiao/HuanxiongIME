# -*- coding: utf-8 -*-
"""
当 github.com:443 连不上（git push 超时）时，改用 GitHub Git Data API 推送本地 HEAD。

原理：api.github.com 往往还能通。拿远端 tree 和本地 HEAD tree 逐个 blob 比对 sha，
只上传有差异的文件，然后建 commit、移动 main 指针。

用法：
    python tools/push_via_api.py

注意：这样推上去的 commit 是远端新建的，本地 HEAD 会和 origin/main 分叉。
网络恢复后对齐一次即可：
    git fetch origin && git reset --hard origin/main
"""
import base64
import json
import os
import subprocess
import sys
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
from publish_release import REPO, get_token  # noqa: E402

TOKEN = get_token()


def git(*args, binary=False):
    # core.quotepath=false：不然 ls-tree 会把中文路径转义成 \344\275\277
    r = subprocess.run(["git", "-c", "core.quotepath=false"] + list(args), cwd=ROOT, capture_output=True)
    if r.returncode != 0:
        raise SystemExit("git %s 失败:\n%s" % (" ".join(args), r.stderr.decode("utf-8", "ignore")))
    return r.stdout if binary else r.stdout.decode("utf-8", "ignore")


def api(path, data=None, method=None, timeout=300):
    url = path if path.startswith("http") else "https://api.github.com" + path
    body = json.dumps(data).encode("utf-8") if data is not None else None
    req = urllib.request.Request(url, data=body, method=method or ("POST" if body is not None else "GET"))
    req.add_header("Authorization", "Bearer " + TOKEN)
    req.add_header("Accept", "application/vnd.github+json")
    if body is not None:
        req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = resp.read()
        return json.loads(raw.decode("utf-8")) if raw else {}


def main():
    base_sha = api("/repos/%s/git/ref/heads/main" % REPO)["object"]["sha"]
    head_sha = git("rev-parse", "HEAD").strip()
    print("→ 远端 main: %s" % base_sha[:8])
    print("→ 本地 HEAD: %s  %s" % (head_sha[:8], git("log", "-1", "--pretty=%s", head_sha).strip()))

    remote = api("/repos/%s/git/trees/%s?recursive=1" % (REPO, base_sha))
    remote_files = {i["path"]: i["sha"] for i in remote["tree"] if i["type"] == "blob"}
    local_files = {}
    for line in git("ls-tree", "-r", "HEAD").splitlines():
        meta, path = line.split("\t", 1)
        mode, typ, sha = meta.split()
        if typ == "blob":
            local_files[path] = (mode, sha)

    changed = [p for p, (_m, s) in local_files.items() if remote_files.get(p) != s]
    deleted = [p for p in remote_files if p not in local_files]
    if not changed and not deleted:
        print("✓ 内容已一致，无需推送")
        return

    tree_items = []
    for path in changed:
        raw = git("show", "%s:%s" % (head_sha, path), binary=True)
        blob = api("/repos/%s/git/blobs" % REPO, {
            "content": base64.b64encode(raw).decode("ascii"),
            "encoding": "base64",
        })
        tree_items.append({"path": path, "mode": local_files[path][0],
                           "type": "blob", "sha": blob["sha"]})
        print("   改 %s  %.1f KB" % (path, len(raw) / 1024.0))
    for path in deleted:
        tree_items.append({"path": path, "mode": "100644", "type": "blob", "sha": None})
        print("   删 %s" % path)

    base_tree = api("/repos/%s/git/commits/%s" % (REPO, base_sha))["tree"]["sha"]
    tree = api("/repos/%s/git/trees" % REPO, {"base_tree": base_tree, "tree": tree_items})
    info = git("log", "-1", "--pretty=format:%s%n%an%n%ae", head_sha).splitlines()
    commit = api("/repos/%s/git/commits" % REPO, {
        "message": info[0],
        "tree": tree["sha"],
        "parents": [base_sha],
        "author": {"name": info[1], "email": info[2]},
    })
    api("/repos/%s/git/refs/heads/main" % REPO, {"sha": commit["sha"], "force": False}, method="PATCH")
    print("✓ 已推送 %s → main" % commit["sha"][:8])


if __name__ == "__main__":
    main()
