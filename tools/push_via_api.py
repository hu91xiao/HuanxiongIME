# -*- coding: utf-8 -*-
"""
当 github.com:443 连不上（git push 超时）时，改用 GitHub Git Data API 推送本地提交。

原理：api.github.com 往往还能通。逐个文件建 blob → 建 tree → 建 commit → 移动 main 指针。

用法：
    python tools/push_via_api.py
"""
import base64
import json
import os
import subprocess
import sys
import urllib.error
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
from publish_release import REPO, get_token  # noqa: E402

TOKEN = get_token()


def git(*args, binary=False):
    r = subprocess.run(["git"] + list(args), cwd=ROOT, capture_output=True)
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
    if base_sha == head_sha:
        print("远程已是最新，无需推送")
        return

    info = git("log", "-1", "--pretty=format:%an%n%ae", head_sha).splitlines()
    author_name, author_email = info[0], info[1]
    subjects = git("log", "--pretty=format:%s", "%s..%s" % (base_sha, head_sha)).strip()
    print("→ 远程 main: %s" % base_sha[:8])
    print("→ 本地 HEAD: %s" % head_sha[:8])
    for s in subjects.splitlines():
        print("     · " + s)

    changes = []
    for line in git("diff", "--name-status", base_sha, head_sha).splitlines():
        parts = line.split("\t")
        changes.append((parts[0], parts[-1]))
    if not changes:
        print("没有文件差异")
        return

    tree_items = []
    for st, path in changes:
        if st.startswith("D"):
            tree_items.append({"path": path, "mode": "100644", "type": "blob", "sha": None})
            print("   删除 %s" % path)
            continue
        raw = git("show", "%s:%s" % (head_sha, path), binary=True)
        blob = api("/repos/%s/git/blobs" % REPO,
                   {"content": base64.b64encode(raw).decode("ascii"), "encoding": "base64"})
        print("   %s %s  %.1f KB" % ("修改" if st.startswith("M") else "新增", path, len(raw) / 1024.0))
        tree_items.append({"path": path, "mode": "100644", "type": "blob", "sha": blob["sha"]})

    base_tree = api("/repos/%s/git/commits/%s" % (REPO, base_sha))["tree"]["sha"]
    tree = api("/repos/%s/git/trees" % REPO, {"base_tree": base_tree, "tree": tree_items})
    commit = api("/repos/%s/git/commits" % REPO, {
        "message": subjects,
        "tree": tree["sha"],
        "parents": [base_sha],
        "author": {"name": author_name, "email": author_email},
    })
    api("/repos/%s/git/refs/heads/main" % REPO, {"sha": commit["sha"], "force": False}, method="PATCH")
    print("✓ 已推送 %s → main" % commit["sha"][:8])


if __name__ == "__main__":
    main()
