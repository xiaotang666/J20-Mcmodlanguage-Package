"""从 i18n 最新发布包拉取**全量**汉化基底（替代逐文件拉取作为打包底座）。

用法：
    python src/merger/fetch_i18n_release.py \
        --config config/merger/i18n-release.json \
        --pack-config config/packer/pack-config.json \
        --output build/i18n-extracted/ \
        [--download-dir build/i18n-packs/] \
        [--mirror-prefix https://ghproxy.net/] \
        [--mc-version 1.21]

行为：
- 按 pack-config 的版本组 × 内容组（forge/fabric）解析 i18n 发布包资产名（映射与回退见 config）；
- 下载 `releases/latest/download/<资产>`（已下载的缓存在 --download-dir，幂等）；
- 解包 `assets/**` 到 <output>/<版本组>/<content>/assets/...（自定义 pack.mcmeta/LICENSE 不带入）；
- fabric 资产缺失时回退同版本基座包；输出 build/i18n-release-report.json。
"""
from __future__ import annotations

import argparse
import io
import json
import sys
import urllib.request
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import REPO_ROOT, fail, load_json, save_json  # noqa: E402


def download(url: str, dest: Path, mirror_prefix: str) -> bool:
    full = mirror_prefix + url if mirror_prefix else url
    if dest.exists() and dest.stat().st_size > 0:
        print(f"[CACHE] {dest.name}")
        return True
    for attempt in range(1, 4):
        try:
            with urllib.request.urlopen(full, timeout=300) as r:
                data = r.read()
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(data)
            print(f"[GET]   {dest.name} ({len(data)} bytes)")
            return True
        except Exception as e:  # noqa: BLE001
            print(f"[RETRY {attempt}/3] {dest.name} -> {e}", file=sys.stderr)
    print(f"[FAIL]  {full} -> 三次尝试均失败", file=sys.stderr)
    return False


def extract_assets(zip_path: Path, target_dir: Path) -> int:
    n = 0
    with zipfile.ZipFile(zip_path) as zf:
        for name in zf.namelist():
            if not name.startswith("assets/") or name.endswith("/"):
                continue
            dest = target_dir / name
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(zf.read(name))
            n += 1
    return n


def main() -> int:
    ap = argparse.ArgumentParser(description="拉取 i18n 发布包全量基底")
    ap.add_argument("--config", default=str(REPO_ROOT / "config" / "merger" / "i18n-release.json"))
    ap.add_argument("--pack-config", default=str(REPO_ROOT / "config" / "packer" / "pack-config.json"))
    ap.add_argument("--output", default="build/i18n-extracted/")
    ap.add_argument("--download-dir", default="build/i18n-packs/")
    ap.add_argument("--mirror-prefix", default="", help="国内镜像前缀（本地用，如 https://ghproxy.net/）")
    ap.add_argument("--mc-version", default=None, help="只处理指定版本组（逗号分隔）")
    args = ap.parse_args()

    cfg = load_json(Path(args.config))
    pack_cfg = load_json(Path(args.pack_config))
    out_dir, dl_dir = Path(args.output), Path(args.download_dir)

    groups = sorted({p["mc_version"] for p in pack_cfg.get("packs", [])})
    if args.mc_version:
        want = {v.strip() for v in args.mc_version.split(",")}
        groups = [g for g in groups if g in want]
    content_groups = pack_cfg.get("content_groups", {"forge": {}})

    ver_keys: dict = cfg["version_keys"]
    tpl = cfg["asset_template"]
    url_tpl = cfg["release_url_template"].replace("{repo}", cfg["repo"])
    report = {"source": cfg["repo"], "groups": [], "failures": []}

    for group in groups:
        # 版本组 -> i18n 资产版本段（配置即回退：26.2/26.3 -> 26-1）
        ver_key = ver_keys.get(group)
        if not ver_key:
            msg = f"{group}: version_keys 无映射，跳过"
            report["failures"].append(msg)
            print(f"[WARN] {msg}", file=sys.stderr)
            continue
        base_asset = tpl.format(ver_key=ver_key, fabric_suffix="")
        for content in content_groups:
            fab = cfg.get("fabric_suffix", "-fabric") if content == "fabric" else ""
            asset = tpl.format(ver_key=ver_key, fabric_suffix=fab)
            zip_path = dl_dir / asset
            url = url_tpl.format(asset=asset)
            ok = download(url, zip_path, args.mirror_prefix)
            if not ok and content == "fabric":
                asset, zip_path, url = base_asset, dl_dir / base_asset, url_tpl.format(asset=base_asset)
                ok = download(url, zip_path, args.mirror_prefix)
                if ok:
                    print(f"[FALLBACK] {group}/fabric 回退基座包 {base_asset}")
            if not ok:
                report["failures"].append(f"{group}/{content}: {asset} 下载失败")
                continue
            n = extract_assets(zip_path, out_dir / group / content)
            report["groups"].append({"mc_version": group, "content": content,
                                     "asset": asset, "files": n})
            print(f"[BASE]  {group}/{content} <- {asset}（{n} 个文件）")

    save_json(Path("build/i18n-release-report.json"), report)
    if report["failures"]:
        print(f"\n存在失败：{len(report['failures'])}", file=sys.stderr)
        for f in report["failures"]:
            print(f"  - {f}", file=sys.stderr)
        return 1
    print(f"\ni18n 发布包基底完成：{len(report['groups'])} 组")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
