"""i18n 拉取器：按 file-selection.json 清单从 i18n 仓库逐文件拉取 zh_cn 语言文件。

用法：
    python src/merger/fetch_i18n_files.py \
        --manifest j20-manifest/file-selection.json \
        --config config/merger/i18n-source.json \
        --output build/i18n-extracted/

行为约定：
- 对每个 (mc_version, mod)：按 i18n_version_dirs 优先级 × formats 依次尝试候选路径，
  取第一个拉取成功的作为该模组的 zh_cn 文件；
- 某模组全部候选均失败 → 记录警告并跳过，不中断构建；
- 输出 build/merge-info.json 中的 fetched 部分（成功/失败/跳过清单）。
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import fetch_with_fallback, load_json, save_json, BUILD_DIR  # noqa: E402


def candidate_paths(mod: dict, i18n_version_dirs: list[str], file_pattern: str) -> list[str]:
    """生成候选拉取路径（相对 i18n 仓库根），按优先级排序。"""
    paths = []
    for vdir in i18n_version_dirs:
        for fmt in mod.get("formats", ["json"]):
            paths.append(file_pattern.format(
                mod_dir=mod["mod_dir"],
                i18n_version_dir=vdir,
                namespace=mod["namespace"],
                file=f"zh_cn.{fmt}",
            ))
    return paths


def main() -> int:
    ap = argparse.ArgumentParser(description="按清单从 i18n 仓库拉取指定模组的翻译文件")
    ap.add_argument("--manifest", required=True, help="j20-manifest/file-selection.json")
    ap.add_argument("--config", required=True, help="config/merger/i18n-source.json")
    ap.add_argument("--output", required=True, help="拉取输出目录，如 build/i18n-extracted/")
    args = ap.parse_args()

    selection = load_json(args.manifest)
    config = load_json(args.config)
    out_dir = Path(args.output)
    file_pattern = config["file_path_pattern"]

    fetched, failed = [], []
    for mc_version, group in selection["mc_versions"].items():
        for mod in group["mods"]:
            ns, mod_dir = mod["namespace"], mod["mod_dir"]
            done = False
            for rel in candidate_paths(mod, group.get("i18n_version_dirs", [""]), file_pattern):
                content, url, _tried = fetch_with_fallback(rel, config)
                if content is None:
                    continue
                # 统一落盘为 assets/<namespace>/lang/zh_cn.<fmt>
                fmt = rel.rsplit(".", 1)[-1]
                target = out_dir / "assets" / ns / "lang" / f"zh_cn.{fmt}"
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(content)
                fetched.append({
                    "mc_version": mc_version,
                    "mod_dir": mod_dir,
                    "namespace": ns,
                    "path": rel,
                    "source_url": url,
                    "bytes": len(content),
                })
                print(f"[OK]   {mc_version} {mod_dir} -> {rel} ({len(content)} bytes)")
                done = True
                break
            if not done:
                failed.append({"mc_version": mc_version, "mod_dir": mod_dir, "namespace": ns})
                print(f"[WARN] {mc_version} {mod_dir} 所有候选路径均拉取失败，跳过", file=sys.stderr)

    report = {"fetched_files_count": len(fetched), "failed_files_count": len(failed),
              "fetched": fetched, "failed": failed}
    save_json(BUILD_DIR / "fetch-report.json", report)
    print(f"\n拉取完成：成功 {len(fetched)}，失败/跳过 {len(failed)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
