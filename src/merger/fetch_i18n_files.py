"""i18n 拉取器：按 file-selection.json 清单从 i18n 仓库逐文件拉取 zh_cn 语言文件。

用法：
    python src/merger/fetch_i18n_files.py \
        --manifest j20-manifest/file-selection.json \
        --config config/merger/i18n-source.json \
        --pack-config config/packer/pack-config.json \
        --output build/i18n-extracted/

行为约定：
- 按内容组（forge / fabric）分别拉取，落盘到 <output>/<版本组>/<content>/assets/<namespace>/lang/；
- Fabric 内容优先尝试 i18n 的 '<版本目录>-fabric' 变体，回退普通目录；Forge 只用普通目录；
- 对每个 (版本组, mod)：按 i18n_version_dirs 优先级 × formats 依次尝试候选路径，
  取第一个拉取成功的作为该模组的 zh_cn 文件；
- 8 线程并发；同 URL 只拉一次（共享缓存）；确认缺失的 (mod_dir, 版本目录) 不再重试；
- 某模组全部候选均失败 → 记录警告并跳过，不中断构建；
- 输出 build/fetch-report.json（成功/失败/跳过清单，含 content 字段）。
"""
from __future__ import annotations

import argparse
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import fetch_with_fallback, load_json, save_json, BUILD_DIR  # noqa: E402


def expand_version_dirs(base_dirs: list[str], suffixes: list[str]) -> list[str]:
    """按内容组的目录后缀偏好展开候选版本目录，保序去重。"""
    out: list[str] = []
    for base in base_dirs:
        for suf in suffixes:
            v = f"{base}{suf}"
            if v not in out:
                out.append(v)
    return out


def candidate_paths(mod: dict, version_dirs: list[str], file_pattern: str) -> list[str]:
    """生成候选拉取路径（相对 i18n 仓库根），按优先级排序。"""
    paths = []
    for vdir in version_dirs:
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
    ap.add_argument("--pack-config", required=True, help="config/packer/pack-config.json")
    ap.add_argument("--output", required=True, help="拉取输出目录，如 build/i18n-extracted/")
    ap.add_argument("--workers", type=int, default=8, help="并发线程数（默认 8）")
    args = ap.parse_args()

    selection = load_json(args.manifest)
    config = load_json(args.config)
    pack_cfg = load_json(args.pack_config)
    out_dir = Path(args.output)
    file_pattern = config["file_path_pattern"]
    content_groups = pack_cfg.get("content_groups", {"forge": {"i18n_dir_suffixes": [""]}})

    lock = threading.Lock()
    url_cache: dict[str, tuple[bytes | None, str | None]] = {}
    dir_miss: set[tuple[str, str]] = set()  # (mod_dir, 版本目录) 已确认缺失，跳过同目录其他格式
    fetched: list[dict] = []
    failed: list[dict] = []

    def fetch_one(mc_version: str, content: str, mod: dict, version_dirs: list[str]) -> None:
        ns, mod_dir = mod["namespace"], mod["mod_dir"]
        for rel in candidate_paths(mod, version_dirs, file_pattern):
            parts = rel.split("/")
            vdir = parts[3] if len(parts) > 3 else ""
            with lock:
                if (mod_dir, vdir) in dir_miss:
                    continue
                cached = url_cache.get(rel)
            if cached is not None:
                data, url = cached
            else:
                data, url, _tried = fetch_with_fallback(rel, config)
                with lock:
                    url_cache[rel] = (data, url)
                    if data is None:
                        dir_miss.add((mod_dir, vdir))
            if data is None:
                continue
            # 统一落盘为 <版本组>/<content>/assets/<namespace>/lang/zh_cn.<fmt>
            fmt = rel.rsplit(".", 1)[-1]
            target = out_dir / mc_version / content / "assets" / ns / "lang" / f"zh_cn.{fmt}"
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
            with lock:
                fetched.append({
                    "mc_version": mc_version,
                    "content": content,
                    "mod_dir": mod_dir,
                    "namespace": ns,
                    "path": rel,
                    "source_url": url,
                    "bytes": len(data),
                })
                print(f"[OK]   {mc_version}/{content} {mod_dir} -> {rel} ({len(data)} bytes)")
            return
        with lock:
            failed.append({"mc_version": mc_version, "content": content,
                           "mod_dir": mod_dir, "namespace": ns})
            print(f"[WARN] {mc_version}/{content} {mod_dir} 所有候选路径均拉取失败，跳过",
                  file=sys.stderr)

    tasks = []
    for mc_version, group in selection["mc_versions"].items():
        base_dirs = group.get("i18n_version_dirs", [""])
        for content, cg in content_groups.items():
            version_dirs = expand_version_dirs(base_dirs, cg.get("i18n_dir_suffixes", [""]))
            for mod in group["mods"]:
                tasks.append((mc_version, content, mod, version_dirs))

    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = [pool.submit(fetch_one, *t) for t in tasks]
        for f in futures:
            f.result()

    report = {"fetched_files_count": len(fetched), "failed_files_count": len(failed),
              "fetched": sorted(fetched, key=lambda e: (e["mc_version"], e["content"], e["mod_dir"])),
              "failed": sorted(failed, key=lambda e: (e["mc_version"], e["content"], e["mod_dir"]))}
    save_json(BUILD_DIR / "fetch-report.json", report)
    print(f"\n拉取完成：成功 {len(fetched)}，失败/跳过 {len(failed)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
