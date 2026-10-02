"""VP 模块打包器：把 vaultpatcher/modules/*.json 打包为 vp-modules-{版本组}.zip。

用法：
    python src/packer/build_vp.py --output build/                    # 按 pack-config 的 vp_groups 全量产出
    python src/packer/build_vp.py --mc-version 1.20 --output build/  # 指定单个/逗号分隔多个版本组
zip 内部结构（冻结，不可变更）：
    vaultpatcher/modules/<modid>.json
"""
from __future__ import annotations

import argparse
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import REPO_ROOT, fail, load_json  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description="打包 VP 硬编码补丁模块")
    ap.add_argument("--mc-version", default=None,
                    help="版本组（可逗号分隔）；省略则按 pack-config 的 vp_groups 全量产出")
    ap.add_argument("--output", default="build/", help="输出目录")
    ap.add_argument("--modules-dir", default=str(REPO_ROOT / "vaultpatcher" / "modules"))
    ap.add_argument("--config", default=str(REPO_ROOT / "config" / "packer" / "pack-config.json"))
    args = ap.parse_args()

    if args.mc_version:
        versions = [v.strip() for v in args.mc_version.split(",") if v.strip()]
    else:
        cfg = load_json(args.config)
        versions = list(cfg.get("vp_groups", []))
        if not versions:
            fail("pack-config 的 vp_groups 为空，且未指定 --mc-version")

    modules_dir = Path(args.modules_dir)
    modules = sorted(modules_dir.glob("*.json"))
    if not modules:
        print(f"[WARN] {modules_dir} 下没有 VP 模块文件，生成空模块包", file=sys.stderr)

    out_dir = Path(args.output)
    out_dir.mkdir(parents=True, exist_ok=True)
    for version in versions:
        out_path = out_dir / f"vp-modules-{version}.zip"
        with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for m in modules:
                zf.write(m, f"vaultpatcher/modules/{m.name}")
        if not out_path.exists():
            fail("VP 模块包生成失败")
        print(f"[VP] {out_path.name} modules={len(modules)} ({out_path.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
