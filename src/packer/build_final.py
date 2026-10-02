"""最终资源包打包器：合并后的语言文件 + VP 补丁 + 协议/署名文件 → pack-{mc_version}-{loader}.zip。

用法：
    python src/packer/build_final.py --lang-dir build/i18n-extracted/ --output build/

资源包内部结构（冻结，不可变更）：
    pack.mcmeta                      # description 含 i18n 署名
    assets/<namespace>/lang/zh_cn.*  # 覆盖后的最终语言文件
    vaultpatcher/modules/*.json      # VP 硬编码补丁
    LICENSE-i18n / LICENSE-j20 / ATTRIBUTION.md
"""
from __future__ import annotations

import argparse
import json
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import REPO_ROOT, load_json  # noqa: E402

MCMETA_DESCRIPTION = [
    "§6J20-Mcmodlanguage-Package §7(合并 i18n 库)",
    "§7基于 §fCFPAOrg i18n 库 §7改编",
    "§7协议：§fCC BY-NC-SA 4.0",
]


def build_one(lang_dir: Path, modules_dir: Path, out_path: Path, pack_format: int, mc_version: str, loader: str) -> None:
    mcmeta = {"pack": {"pack_format": pack_format, "description": MCMETA_DESCRIPTION}}
    with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("pack.mcmeta", json.dumps(mcmeta, ensure_ascii=False, indent=2) + "\n")
        n_lang = 0
        for f in sorted(lang_dir.rglob("zh_cn.*")):
            rel = f.relative_to(lang_dir)
            zf.write(f, str(rel).replace("\\", "/"))
            n_lang += 1
        n_vp = 0
        for m in sorted(modules_dir.glob("*.json")):
            zf.write(m, f"vaultpatcher/modules/{m.name}")
            n_vp += 1
        for name, arc in (("LICENSE-i18n", "LICENSE-i18n"), ("LICENSE", "LICENSE-j20"),
                          ("ATTRIBUTION.md", "ATTRIBUTION.md")):
            src = REPO_ROOT / name
            if src.exists():
                zf.write(src, arc)
    print(f"[PACK] {out_path.name} mc={mc_version} loader={loader} "
          f"pack_format={pack_format} lang_files={n_lang} vp_modules={n_vp}")


def main() -> int:
    ap = argparse.ArgumentParser(description="打包最终资源包")
    ap.add_argument("--lang-dir", required=True, help="覆盖后的语言目录，如 build/i18n-extracted/")
    ap.add_argument("--output", default="build/", help="输出目录")
    ap.add_argument("--modules-dir", default=str(REPO_ROOT / "vaultpatcher" / "modules"))
    ap.add_argument("--config", default=str(REPO_ROOT / "config" / "packer" / "pack-config.json"))
    args = ap.parse_args()

    cfg = load_json(args.config)
    lang_dir = Path(args.lang_dir)
    if not lang_dir.is_dir():
        print(f"[WARN] 语言目录不存在：{lang_dir}", file=sys.stderr)

    out_dir = Path(args.output)
    out_dir.mkdir(parents=True, exist_ok=True)
    for pack in cfg["packs"]:
        out_path = out_dir / f"pack-{pack['mc_version']}-{pack['loader']}.zip"
        build_one(lang_dir, Path(args.modules_dir), out_path,
                  int(pack["pack_format"]), pack["mc_version"], pack["loader"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
