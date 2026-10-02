"""找出 i18n 库里没有汉化的模组（有 en_us、缺 zh_cn 或 zh_cn 严重不全）。

用法：
    python src/ai-translate/find_untranslated.py \
        --manifest j20-manifest/file-selection.json \
        --config config/merger/i18n-source.json \
        [--mods mod_dir1,mod_dir2 ...]        # 额外检查清单外的模组
        [--output ../待审核/_untranslated.json]

判断：按 file_path_pattern 的候选路径拉 zh_cn.*；全失败但 en_us.* 能拉到 → 未汉化；
zh_cn 条目数 / en_us 条目数 < 0.5 → 视为严重不全，同样进入待 AI 初翻名单。
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import fetch_with_fallback, load_json, save_json  # noqa: E402
from ai_common import DEFAULT_PENDING_ROOT  # noqa: E402


def try_fetch_pattern(config: dict, mod: dict, vdirs: list[str], stem: str) -> tuple[bytes | None, str]:
    for vdir in vdirs:
        for fmt in mod.get("formats", ["json"]):
            rel = config["file_path_pattern"].format(
                mod_dir=mod["mod_dir"], i18n_version_dir=vdir,
                namespace=mod["namespace"], file=f"{stem}.{fmt}")
            content, url, _ = fetch_with_fallback(rel, config)
            if content is not None:
                return content, rel
    return None, ""


def count_keys(raw: bytes) -> int:
    try:
        data = json.loads(raw.decode("utf-8"))
        return len(data) if isinstance(data, dict) else 0
    except (ValueError, UnicodeDecodeError):
        return -1


def main() -> int:
    ap = argparse.ArgumentParser(description="找出 i18n 中未汉化/严重不全的模组")
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--config", required=True)
    ap.add_argument("--mods", default="", help="额外的 mod_dir,namespace 逗号对，如 create,create;foo,foo")
    ap.add_argument("--output", default=str(DEFAULT_PENDING_ROOT / "_untranslated.json"))
    args = ap.parse_args()

    selection = load_json(args.manifest)
    config = load_json(args.config)

    jobs = []
    for mc_version, group in selection["mc_versions"].items():
        for mod in group["mods"]:
            jobs.append((mc_version, group.get("i18n_version_dirs", [""]), mod))
    for pair in filter(None, args.mods.split(";")):
        mod_dir, _, ns = pair.partition(",")
        jobs.append(("*", ["1.20", "1.18", "1.16"],
                     {"mod_dir": mod_dir.strip(), "namespace": (ns or mod_dir).strip(), "formats": ["json"]}))

    untranslated, partial, ok = [], [], []
    for mc_version, vdirs, mod in jobs:
        en_raw, _ = try_fetch_pattern(config, mod, vdirs, "en_us")
        zh_raw, _ = try_fetch_pattern(config, mod, vdirs, "zh_cn")
        if en_raw is None:
            print(f"[SKIP] {mod['mod_dir']}: en_us 也拉不到（i18n 未收录），无法判断")
            continue
        n_en = count_keys(en_raw)
        if zh_raw is None:
            untranslated.append({"mc_version": mc_version, **mod, "en_keys": n_en})
            print(f"[未汉化] {mod['mod_dir']} (en_us {n_en} 条)")
        else:
            n_zh = count_keys(zh_raw)
            if n_en > 0 and n_zh >= 0 and n_zh / n_en < 0.5:
                partial.append({"mc_version": mc_version, **mod, "en_keys": n_en, "zh_keys": n_zh})
                print(f"[严重不全] {mod['mod_dir']} (zh {n_zh}/{n_en})")
            else:
                ok.append(mod["mod_dir"])

    report = {"untranslated": untranslated, "partial": partial, "ok": ok,
              "summary": {"untranslated": len(untranslated), "partial": len(partial), "ok": len(ok)}}
    save_json(args.output, report)
    print(f"\n完成：未汉化 {len(untranslated)}，严重不全 {len(partial)}，已汉化 {len(ok)}")
    print(f"名单已写入 {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
