"""发布冒烟校验：逐个下载 manifest 引用的 release_url，核对 md5/size 与 manifest 一致。

CI 在 Release 发布后、回写 manifest 前运行（build.yml）；防止仓库中出现指向
未发布资产（404）或内容不符的 manifest。也可本地运行做发布后抽查。

用法：
    python src/packer/verify_release.py [--manifest manifest.json]
"""
from __future__ import annotations

import argparse
import hashlib
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import REPO_ROOT, load_json  # noqa: E402


def check_entry(entry: dict) -> list[str]:
    name = entry.get("asset_name", "?")
    url = entry.get("release_url", "")
    try:
        with urllib.request.urlopen(url, timeout=120) as resp:
            data = resp.read()
    except Exception as e:  # noqa: BLE001 —— 任何下载失败都算冒烟失败
        return [f"{name}: 无法下载 {url}（{e}）"]
    errors = []
    h = hashlib.md5(data).hexdigest()
    if h != entry.get("md5"):
        errors.append(f"{name}: md5 不一致 manifest={entry.get('md5')} 实际={h}")
    if len(data) != entry.get("size"):
        errors.append(f"{name}: size 不一致 manifest={entry.get('size')} 实际={len(data)}")
    return errors


def main() -> int:
    ap = argparse.ArgumentParser(description="发布冒烟校验（逐资产下载 + md5/size 核对）")
    ap.add_argument("--manifest", default=str(REPO_ROOT / "manifest.json"))
    args = ap.parse_args()

    manifest = load_json(Path(args.manifest))
    latest = manifest.get("latest", {}) or {}
    entries = (latest.get("packages") or []) + (latest.get("vp_packages") or [])
    if not entries:
        print("[FATAL] manifest 中没有任何资产条目", file=sys.stderr)
        return 1

    errors: list[str] = []
    for entry in entries:
        errs = check_entry(entry)
        print(f"[{'PASS' if not errs else 'FAIL'}] {entry.get('asset_name')}")
        errors.extend(errs)

    for err in errors:
        print(f"[FAIL] {err}", file=sys.stderr)
    if errors:
        print(f"冒烟校验失败：{len(errors)} 项不通过", file=sys.stderr)
        return 1
    print(f"冒烟校验通过：{len(entries)} 个资产全部可下载且 md5/size 匹配")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
