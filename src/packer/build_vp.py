"""VP 模块打包器：把 vaultpatcher/modules/ 按版本回退链解析后打包为 vp-modules-{版本组}.zip。

源结构（版本差异层 + 通用层，与 projects/ 同规则）：
    vaultpatcher/modules/<模块名>.json            ← 通用层：所有版本共用
    vaultpatcher/modules/<版本组>/<模块名>.json   ← 版本差异层：仅某版本内容不同时才放

版本回退链（pack-config.json 的 project_version_chain，与资源包同链）：
    同名模块沿链查找（26.3→26.2→26.1→1.21→1.20），最先命中即用，均未命中取通用层。
    写在低版本目录的模块被高版本构建自动复用；仅当某版本类名/硬编码字符串不同时
    才在该版本目录另立一份同名文件（整体覆盖）。

用法：
    python src/packer/build_vp.py --output build/                    # 按 pack-config 的 vp_groups 全量产出
    python src/packer/build_vp.py --mc-version 1.20 --output build/  # 指定单个/逗号分隔多个版本组

zip 内部结构（冻结，不可变更）：
    vaultpatcher/modules/<模块名>.json   ← 恒为一层平铺（版本解析只发生在打包时）
"""
from __future__ import annotations

import argparse
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import REPO_ROOT, fail, load_json  # noqa: E402


def resolve_modules(modules_dir: Path, chain: list[str]) -> dict[str, Path]:
    """按回退链解析模块集：{模块名: 源文件}。链内版本目录先命中先赢，通用层兜底。"""
    chosen: dict[str, Path] = {}
    for ver in chain:
        vdir = modules_dir / ver
        if vdir.is_dir():
            for m in sorted(vdir.glob("*.json")):
                chosen.setdefault(m.name, m)
    for m in sorted(modules_dir.glob("*.json")):
        chosen.setdefault(m.name, m)
    return chosen


def main() -> int:
    ap = argparse.ArgumentParser(description="打包 VP 硬编码补丁模块（版本回退链解析）")
    ap.add_argument("--mc-version", default=None,
                    help="版本组（可逗号分隔）；省略则按 pack-config 的 vp_groups 全量产出")
    ap.add_argument("--output", default="build/", help="输出目录")
    ap.add_argument("--modules-dir", default=str(REPO_ROOT / "vaultpatcher" / "modules"))
    ap.add_argument("--config", default=str(REPO_ROOT / "config" / "packer" / "pack-config.json"))
    args = ap.parse_args()

    cfg = load_json(args.config)
    chains = cfg.get("project_version_chain", {})
    if args.mc_version:
        versions = [v.strip() for v in args.mc_version.split(",") if v.strip()]
    else:
        versions = list(cfg.get("vp_groups", []))
        if not versions:
            fail("pack-config 的 vp_groups 为空，且未指定 --mc-version")

    modules_dir = Path(args.modules_dir)
    out_dir = Path(args.output)
    out_dir.mkdir(parents=True, exist_ok=True)
    for version in versions:
        chain = chains.get(version) or [version]
        modules = resolve_modules(modules_dir, chain)
        if not modules:
            print(f"[WARN] {modules_dir} 及其版本目录下没有 VP 模块文件，生成空模块包", file=sys.stderr)
        out_path = out_dir / f"vp-modules-{version}.zip"
        with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for name, m in sorted(modules.items()):
                zf.write(m, f"vaultpatcher/modules/{name}")
        if not out_path.exists():
            fail("VP 模块包生成失败")
        srcs = ", ".join(f"{n}<-{p.parent.name}" for n, p in sorted(modules.items())) or "(空)"
        print(f"[VP] {out_path.name} modules={len(modules)} ({out_path.stat().st_size} bytes) [{srcs}]")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
