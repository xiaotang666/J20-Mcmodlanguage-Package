"""最终资源包打包器：合并后的语言文件 + VP 补丁 + 协议/署名文件 → pack-{版本组}-{loader}.zip。

用法：
    python src/packer/build_final.py --lang-dir build/i18n-extracted/ --output build/

行为约定（对齐 i18n 的打包方案）：
- 按 pack-config.json 的 packs[] 逐个产出资产；内容按 content 字段取
  <lang-dir>/<forge|fabric>/ 下的语言树；
- NeoForge 包（copy_of: "forge"）与 Forge 包字节级相同，只改资产名
  —— i18n 的 "(Neoforge)" 共包模式，保证三个加载器都有可下载资产；
- pack.mcmeta 按版本组生成：1.20 用 pack_format + supported_formats（1.20.2+ 范围），
  1.21 双方案（旧客户端读 pack_format/supported_formats，1.21.9+ 读 min_format/max_format），
  26.x 只用 min_format/max_format 元组。

资源包内部结构（冻结，不可变更）：
    pack.mcmeta                      # description 含 i18n 署名
    assets/<namespace>/lang/zh_cn.*  # 覆盖后的最终语言文件
    vaultpatcher/modules/*.json      # VP 硬编码补丁
    LICENSE-i18n / LICENSE-j20 / ATTRIBUTION.md
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import REPO_ROOT, load_json  # noqa: E402


def build_mcmeta(fmt_spec: dict, mc_version: str, label: str) -> dict:
    pack: dict = {}
    if "pack_format" in fmt_spec:
        pack["pack_format"] = int(fmt_spec["pack_format"])
    if "supported_formats" in fmt_spec:
        pack["supported_formats"] = list(fmt_spec["supported_formats"])
    if "min_format" in fmt_spec:
        pack["min_format"] = list(fmt_spec["min_format"])
    if "max_format" in fmt_spec:
        pack["max_format"] = list(fmt_spec["max_format"])
    pack["description"] = [
        f"§6J20-Mcmodlanguage-Package §7({mc_version} {label})",
        "§7基于 §fCFPAOrg i18n 库 §7改编",
        "§7协议：§fCC BY-NC-SA 4.0",
    ]
    return {"pack": pack}


def build_one(lang_dir: Path, modules_dir: Path, out_path: Path,
              mcmeta: dict, mc_version: str, loader: str) -> None:
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
    fmt_desc = ", ".join(f"{k}={mcmeta['pack'][k]}" for k in
                         ("pack_format", "supported_formats", "min_format", "max_format")
                         if k in mcmeta["pack"])
    print(f"[PACK] {out_path.name} mc={mc_version} loader={loader} "
          f"[{fmt_desc}] lang_files={n_lang} vp_modules={n_vp}")


def main() -> int:
    ap = argparse.ArgumentParser(description="打包最终资源包")
    ap.add_argument("--lang-dir", required=True, help="拉取结果目录，如 build/i18n-extracted/（含 forge/ fabric/ 内容组）")
    ap.add_argument("--output", default="build/", help="输出目录")
    ap.add_argument("--modules-dir", default=str(REPO_ROOT / "vaultpatcher" / "modules"))
    ap.add_argument("--config", default=str(REPO_ROOT / "config" / "packer" / "pack-config.json"))
    args = ap.parse_args()

    cfg = load_json(args.config)
    lang_root = Path(args.lang_dir)
    out_dir = Path(args.output)
    out_dir.mkdir(parents=True, exist_ok=True)
    formats = cfg["pack_formats"]
    contents = cfg.get("content_groups", {})

    # 先构建真实内容包，再复制共享包（copy_of），保证复制源已存在
    real_packs = [p for p in cfg["packs"] if "copy_of" not in p]
    copy_packs = [p for p in cfg["packs"] if "copy_of" in p]

    for pack in real_packs:
        mc, loader, content = pack["mc_version"], pack["loader"], pack["content"]
        lang_dir = lang_root / mc / content
        if not lang_dir.is_dir():
            print(f"[WARN] 内容目录不存在：{lang_dir}", file=sys.stderr)
        if mc not in formats:
            print(f"[FATAL] pack_formats 缺少版本组 {mc}", file=sys.stderr)
            return 1
        label = contents.get(content, {}).get("label", loader)
        mcmeta = build_mcmeta(formats[mc], mc, label)
        out_path = out_dir / f"pack-{mc}-{loader}.zip"
        build_one(lang_dir, Path(args.modules_dir), out_path, mcmeta, mc, loader)

    for pack in copy_packs:
        mc, loader = pack["mc_version"], pack["loader"]
        src = out_dir / f"pack-{mc}-{pack['copy_of']}.zip"
        dst = out_dir / f"pack-{mc}-{loader}.zip"
        if not src.exists():
            print(f"[FATAL] 共享包源不存在：{src.name}", file=sys.stderr)
            return 1
        shutil.copyfile(src, dst)
        print(f"[COPY]  {dst.name} = {src.name}（{loader} 共用 {pack['copy_of']} 内容）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
