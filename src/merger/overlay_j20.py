"""覆盖调度器：用 J20 自有翻译（projects/）覆盖 i18n 拉取结果（build/i18n-extracted/）。

用法：
    python src/merger/overlay_j20.py --source projects/ --target build/i18n-extracted/

行为约定：
- 遍历 projects/<mc_version>/assets/<namespace>/lang/ 下的 zh_cn.* 文件；
- 目标目录已存在同名文件 → 覆盖（计入 overlaid）；不存在 → 新增（计入 added）；
- 输出 build/overlay-report.json 与 build/merge-info.json 的 overlay 部分。
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import BUILD_DIR, load_json, save_json  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description="J20 自有翻译覆盖 i18n 拉取结果")
    ap.add_argument("--source", required=True, help="J20 自有翻译目录，如 projects/")
    ap.add_argument("--target", required=True, help="拉取结果目录，如 build/i18n-extracted/")
    ap.add_argument("--mc-version", default="1.20.1", help="projects/ 下使用的 MC 版本目录")
    args = ap.parse_args()

    src_root = Path(args.source) / args.mc_version / "assets"
    dst_root = Path(args.target) / "assets"
    if not src_root.is_dir():
        print(f"[WARN] 自有翻译目录不存在：{src_root}", file=sys.stderr)

    overlaid, added = [], []
    for src in sorted(src_root.rglob("zh_cn.*")) if src_root.is_dir() else []:
        rel = src.relative_to(src_root)  # <namespace>/lang/zh_cn.<fmt>
        dst = dst_root / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        entry = {"namespace": rel.parts[0], "file": str(rel).replace("\\", "/"), "bytes": src.stat().st_size}
        # 覆盖/新增分类稍后与 fetch-report 对比得出
        overlaid.append(entry)
        print(f"[OVERLAY] {entry['file']}")

    # 修正覆盖/新增分类：与 fetch-report 对比
    fetch_report = BUILD_DIR / "fetch-report.json"
    fetched_files = set()
    if fetch_report.exists():
        rep = load_json(fetch_report)
        fetched_files = {e["namespace"] for e in rep.get("fetched", [])}
    for e in overlaid:
        e["type"] = "overlaid" if e["namespace"] in fetched_files else "added"
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
