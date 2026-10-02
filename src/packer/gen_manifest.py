"""清单生成器：生成 manifest.json（j20UpdateMod 的冻结接口）。

用法：
    python src/packer/gen_manifest.py --build-dir build/ [--version 2026.10.02-001]

版本号格式固定 YYYY.MM.DD-NNN（冻结契约）；不传 --version 时按当天日期 + 当日构建序号自动生成
（序号取自现有 manifest.json 的同日版本 +1，从 001 起）。

冻结字段（禁止删除/改名/改含义）：
    schema_version, latest.version, latest.packages,
    packages[].mc_version / loader / asset_name / release_url / md5 / size
"""
from __future__ import annotations

import argparse
import datetime as dt
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import REPO_ROOT, load_json, md5_file, save_json, BUILD_DIR  # noqa: E402

VERSION_RE = re.compile(r"^\d{4}\.\d{2}\.\d{2}-\d{3}$")


def next_version(existing: dict | None) -> str:
    today = dt.datetime.now(dt.timezone.utc).strftime("%Y.%m.%d")
    seq = 1
    if existing:
        cur = existing.get("latest", {}).get("version", "")
        m = re.match(r"^(\d{4}\.\d{2}\.\d{2})-(\d{3})$", cur)
        if m and m.group(1) == today:
            seq = int(m.group(2)) + 1
    return f"{today}-{seq:03d}"


def git_commit() -> str | None:
    try:
        out = subprocess.run(["git", "-C", str(REPO_ROOT), "rev-parse", "HEAD"],
                             capture_output=True, text=True, timeout=10)
        return out.stdout.strip() or None
    except Exception:
        return None


def main() -> int:
    ap = argparse.ArgumentParser(description="生成 manifest.json")
    ap.add_argument("--build-dir", default=str(BUILD_DIR))
    ap.add_argument("--config", default=str(REPO_ROOT / "config" / "packer" / "pack-config.json"))
    ap.add_argument("--version", default=None, help="YYYY.MM.DD-NNN；缺省自动生成")
    ap.add_argument("--output", default=str(REPO_ROOT / "manifest.json"))
    args = ap.parse_args()

    cfg = load_json(args.config)
    build_dir = Path(args.build_dir)
    out_path = Path(args.output)

    existing = load_json(out_path) if out_path.exists() else None
    version = args.version or next_version(existing)
    if not VERSION_RE.match(version):
        print(f"[FATAL] 版本号不符合 YYYY.MM.DD-NNN：{version}", file=sys.stderr)
        return 1

    packages = []
    vp_packages = []
    for pack in cfg["packs"]:
        asset = f"pack-{pack['mc_version']}-{pack['loader']}.zip"
        path = build_dir / asset
        if not path.exists():
            print(f"[WARN] 资产不存在，跳过：{asset}", file=sys.stderr)
            continue
        packages.append({
            "mc_version": pack["mc_version"],
            "loader": pack["loader"],
            "asset_name": asset,
            "release_url": f"{cfg['release_base_url']}/{version}/{asset}",
            "md5": md5_file(path),
            "size": path.stat().st_size,
        })
        # VP 模块包冻结命名 vp-modules-{mc_version}.zip；
        # 注意 packages[].loader 冻结为 forge/fabric/neoforge，故 VP 包只进新增可选字段 vp_packages
        vp = build_dir / f"vp-modules-{pack['mc_version']}.zip"
        if vp.exists() and not any(p["asset_name"] == vp.name for p in vp_packages):
            vp_packages.append({
                "mc_version": pack["mc_version"],
                "asset_name": vp.name,
                "release_url": f"{cfg['release_base_url']}/{version}/{vp.name}",
                "md5": md5_file(vp),
                "size": vp.stat().st_size,
            })

    merge_info = {"merge_strategy": "direct_fetch_j20_overlay"}
    mi = build_dir / "merge-info.json"
    if mi.exists():
        merge_info.update(load_json(mi))
    fetch_rep = build_dir / "fetch-report.json"
    if fetch_rep.exists():
        fr = load_json(fetch_rep)
        merge_info.setdefault("fetched_files_count", fr.get("fetched_files_count", 0))
        merge_info.setdefault("i18n_source", "CFPAOrg/Minecraft-Mod-Language-Package")
        merge_info.setdefault("i18n_branch", "main")

    manifest = {
        "schema_version": 1,
        "latest": {
            "version": version,
            "build_time": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "commit": git_commit(),
            "merge_info": merge_info,
            "packages": packages,
            "vp_packages": vp_packages,
        },
    }
    save_json(out_path, manifest)
    print(f"manifest.json 已生成：version={version} packages={len(packages)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
