"""覆盖调度器：用 J20 自有翻译（projects/）覆盖 i18n 拉取结果（build/i18n-extracted/）。

源结构（对齐 i18n 库）：
    projects/assets/<模组>/<版本组>/<命名空间>/lang/zh_cn.*

版本回退链（pack-config.json 的 project_version_chain）：
    构建某版本组时，同一份文件（模组 + 相对路径）沿链查找，命中即用——
    写在低版本目录的翻译会被高版本构建自动复用（如 1.21/ 的内容进 26.x 包）；
    某版本内容不同，就在该版本目录单独立一份（同名文件整体覆盖，非按键合并）。

用法：
    python src/merger/overlay_j20.py --source projects/ --target build/i18n-extracted/
    python src/merger/overlay_j20.py --source projects/ --target build/i18n-extracted/ --mc-version 1.20

行为约定：
- target 布局为 <target>/<版本组>/<内容组>/assets/…（内容组即含 assets/ 的一级子目录）；
- 省略 --mc-version 时按 project_version_chain 全部版本组；指定时只处理该组；
- 应用到该组的每个内容组（forge / fabric 各一份，内容相同）；
- 目标目录已存在同名文件 → 覆盖（计入 overlaid）；不存在 → 新增（计入 added）；
- 输出 build/overlay-report.json 与 build/merge-info.json 的 overlay 部分。
"""
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import BUILD_DIR, REPO_ROOT, load_json, save_json  # noqa: E402


def content_roots(group_dir: Path) -> dict[str, Path]:
    """识别内容组子目录：本身含 assets/ 的一级子目录；无子目录时视为单一 default。"""
    roots: dict[str, Path] = {}
    if (group_dir / "assets").is_dir():
        roots["default"] = group_dir
    if group_dir.is_dir():
        for child in sorted(group_dir.iterdir()):
            if child.is_dir() and (child / "assets").is_dir():
                roots[child.name] = child
    return roots


def resolve_group(mods_root: Path, chain: list[str]) -> tuple[dict[str, Path], list[str]]:
    """按回退链解析一个版本组的最终文件集：{(模组, 相对路径): 源文件}。

    同一 (模组, 相对路径) 以链条中最先命中的版本目录为准（整体文件覆盖）。
    返回 (文件映射, 警告列表)。
    """
    warnings: list[str] = []
    chosen: dict[tuple[str, str], Path] = {}
    for mod_dir in sorted(p for p in mods_root.iterdir() if p.is_dir()):
        mod = mod_dir.name
        version_dirs = {d.name for d in mod_dir.iterdir() if d.is_dir()}
        stray = {d.name for d in mod_dir.iterdir() if not d.is_dir()}
        if stray:
            warnings.append(f"{mod}: 模组目录下存在非版本目录文件：{sorted(stray)}（应只含版本目录）")
        unknown = version_dirs - set(chain)
        if unknown:
            warnings.append(f"{mod}: 版本目录 {sorted(unknown)} 不在回退链 {chain} 中（检查是否拼错版本）")
        for version in chain:  # 链序即优先级：先命中先赢
            vdir = mod_dir / version
            if not vdir.is_dir():
                continue
            for src in sorted(vdir.rglob("zh_cn.*")):
                rel = str(src.relative_to(vdir)).replace("\\", "/")  # <ns>/lang/zh_cn.*
                key = (mod, rel)
                if key not in chosen:
                    chosen[key] = src
    return chosen, warnings


def main() -> int:
    ap = argparse.ArgumentParser(description="J20 自有翻译覆盖 i18n 拉取结果（i18n 式源结构 + 版本回退链）")
    ap.add_argument("--source", required=True, help="J20 自有翻译目录，如 projects/")
    ap.add_argument("--target", required=True, help="拉取结果目录，如 build/i18n-extracted/")
    ap.add_argument("--mc-version", default=None, help="只处理该版本组（如 1.20）；省略则处理全部")
    ap.add_argument("--config", default=str(REPO_ROOT / "config" / "packer" / "pack-config.json"),
                    help="pack-config.json（读取 project_version_chain）")
    args = ap.parse_args()

    cfg = load_json(Path(args.config))
    chains: dict[str, list[str]] = cfg.get("project_version_chain", {})
    if not chains:
        print("[FATAL] pack-config.json 缺少 project_version_chain（版本回退链）", file=sys.stderr)
        return 1

    mods_root = Path(args.source) / "assets"
    if not mods_root.is_dir():
        print(f"[FATAL] 自有翻译源目录不存在：{mods_root}", file=sys.stderr)
        return 1
    target = Path(args.target)

    groups = [args.mc_version] if args.mc_version else list(chains)

    overlaid = []
    for group in groups:
        chain = chains.get(group)
        if not chain:
            print(f"[FATAL] project_version_chain 缺少版本组 {group}", file=sys.stderr)
            return 1
        chosen, warnings = resolve_group(mods_root, chain)
        for w in warnings:
            print(f"[WARN] {w}", file=sys.stderr)
        roots = content_roots(target / group)
        if not roots:
            print(f"[WARN] 拉取结果无内容组目录：{target / group}", file=sys.stderr)
            continue
        for content, dst_root in roots.items():
            for (mod, rel), src in sorted(chosen.items()):
                dst = dst_root / "assets" / rel
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)
                entry = {"mc_version": group, "content": content, "mod": mod,
                         "namespace": rel.split("/")[0],
                         "file": rel, "bytes": src.stat().st_size,
                         "source_version": str(src.relative_to(mods_root / mod).parts[0])}
                overlaid.append(entry)
                print(f"[OVERLAY] {group}/{content}/{rel} <- {mod}/{entry['source_version']}")

    # 覆盖/新增分类：与 fetch-report 对比
    fetch_report = BUILD_DIR / "fetch-report.json"
    fetched_files = set()
    if fetch_report.exists():
        rep = load_json(fetch_report)
        fetched_files = {(e["namespace"], e.get("mc_version"), e.get("content", "default"))
                         for e in rep.get("fetched", [])}
    for e in overlaid:
        e["type"] = ("overlaid" if (e["namespace"], e["mc_version"], e["content"]) in fetched_files
                     else "added")
    n_overlaid = sum(1 for e in overlaid if e["type"] == "overlaid")
    n_added = len(overlaid) - n_overlaid

    report = {"overlaid_files_count": n_overlaid, "added_files_count": n_added, "files": overlaid}
    save_json(BUILD_DIR / "overlay-report.json", report)

    # 合并 merge-info（fetch 部分由拉取器写入 fetch-report.json，这里聚合）
    merge_info = {"merge_strategy": "i18n_release_base_j20_overlay"}
    if fetch_report.exists():
        fr = load_json(fetch_report)
        merge_info["fetched_files_count"] = fr["fetched_files_count"]
    merge_info["overlaid_files_count"] = n_overlaid
    merge_info["added_files_count"] = n_added
    save_json(BUILD_DIR / "merge-info.json", merge_info)

    print(f"\n覆盖完成：覆盖 {n_overlaid}，新增 {n_added}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
