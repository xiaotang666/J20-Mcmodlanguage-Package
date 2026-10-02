"""覆盖调度器：用 J20 自有翻译（projects/）覆盖 i18n 拉取结果（build/i18n-extracted/）。

用法：
    python src/merger/overlay_j20.py --source projects/ --target build/i18n-extracted/
    python src/merger/overlay_j20.py --source projects/ --target build/i18n-extracted/ --mc-version 1.20

行为约定：
- target 布局为 <target>/<版本组>/<内容组>/assets/…（内容组即含 assets/ 的一级子目录）；
- 省略 --mc-version 时遍历 projects/ 下全部版本组；指定时只处理该组；
- 遍历 projects/<版本组>/assets/<namespace>/lang/ 下的 zh_cn.* 文件，应用到该组的每个内容组；
- 目标目录已存在同名文件 → 覆盖（计入 overlaid）；不存在 → 新增（计入 added）；
- 输出 build/overlay-report.json 与 build/merge-info.json 的 overlay 部分。
"""
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import BUILD_DIR, load_json, save_json  # noqa: E402


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


def main() -> int:
    ap = argparse.ArgumentParser(description="J20 自有翻译覆盖 i18n 拉取结果")
    ap.add_argument("--source", required=True, help="J20 自有翻译目录，如 projects/")
    ap.add_argument("--target", required=True, help="拉取结果目录，如 build/i18n-extracted/")
    ap.add_argument("--mc-version", default=None,
                    help="projects/ 下使用的版本组目录（如 1.20）；省略则处理全部")
    args = ap.parse_args()

    src_base = Path(args.source)
    target = Path(args.target)

    if args.mc_version:
        groups = [args.mc_version]
    else:
        groups = sorted(d.name for d in src_base.iterdir() if d.is_dir())

    overlaid = []
    for group in groups:
        src_root = src_base / group / "assets"
        if not src_root.is_dir():
            print(f"[WARN] 自有翻译目录不存在：{src_root}", file=sys.stderr)
            continue
        roots = content_roots(target / group)
        if not roots:
            print(f"[WARN] 拉取结果无内容组目录：{target / group}", file=sys.stderr)
            continue
        for content, dst_root in roots.items():
            for src in sorted(src_root.rglob("zh_cn.*")):
                rel = src.relative_to(src_root)  # <namespace>/lang/zh_cn.<fmt>
                dst = dst_root / "assets" / rel
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)
                entry = {"mc_version": group, "content": content, "namespace": rel.parts[0],
                         "file": str(rel).replace("\\", "/"), "bytes": src.stat().st_size}
                overlaid.append(entry)
                print(f"[OVERLAY] {group}/{content}/{entry['file']}")

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
    merge_info = {"merge_strategy": "direct_fetch_j20_overlay"}
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
