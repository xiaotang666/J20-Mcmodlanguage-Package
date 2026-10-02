"""VP 模块打包器：把 vaultpatcher/modules/*.json 打包为 vp-modules-{mc_version}.zip。

用法：
    python src/packer/build_vp.py --mc-version 1.20.1 --output build/

zip 内部结构（冻结，不可变更）：
    vaultpatcher/modules/<modid>.json
"""
from __future__ import annotations

import argparse
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import REPO_ROOT, fail  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description="打包 VP 硬编码补丁模块")
    ap.add_argument("--mc-version", default="1.20.1")
    ap.add_argument("--output", default="build/", help="输出目录")
    ap.add_argument("--modules-dir", default=str(REPO_ROOT / "vaultpatcher" / "modules"))
    args = ap.parse_args()

    modules_dir = Path(args.modules_dir)
    modules = sorted(modules_dir.glob("*.json"))
    if not modules:
        print(f"[WARN] {modules_dir} 下没有 VP 模块文件，生成空模块包", file=sys.stderr)

    out_dir = Path(args.output)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"vp-modules-{args.mc_version}.zip"
    with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for m in modules:
            zf.write(m, f"vaultpatcher/modules/{m.name}")
            print(f"[VP] {m.name}")

    if not out_path.exists():
        fail("VP 模块包生成失败")
    print(f"\nVP 模块包：{out_path} ({out_path.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
