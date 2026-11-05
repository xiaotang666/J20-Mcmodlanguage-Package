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
- 下载 `releases/latest/download/<资产>`，按前缀列表逐个回退（直连 → fallback_prefixes 镜像），
  每前缀重试 2 次；下载内容过 **zip 完整性校验**（防截断/镜像错误页毒缓存）；
- 已下载的缓存在 --download-dir（幂等；缓存损坏自动重下）；
- 解包 `assets/**` 到 <output>/<版本组>/<content>/assets/...（自定义 pack.mcmeta/LICENSE 不带入）；
  解包失败自动删除缓存重下一次再试；
- fabric 资产缺失时回退同版本基座包；输出 build/i18n-release-report.json。
"""
from __future__ import annotations

import argparse
import io
import json
import sys
import time
import urllib.request
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import REPO_ROOT, fail, load_json, save_json  # noqa: E402


def download(url: str, dest: Path, prefixes: list[str]) -> bool:
    """按前缀列表逐个下载；zip 完整性校验通过才写缓存。"""
    if dest.exists() and dest.stat().st_size > 0:
        if zipfile.is_zipfile(dest):
            print(f"[CACHE] {dest.name}")
            return True
        print(f"[DROP]  {dest.name} 缓存不是合法 zip，删除重下", file=sys.stderr)
        dest.unlink()
    dest.parent.mkdir(parents=True, exist_ok=True)
    for prefix in prefixes:
        full = prefix + url
        for attempt in (1, 2):
            try:
                with urllib.request.urlopen(full, timeout=300) as r:
                    data = r.read()
                if not zipfile.is_zipfile(io.BytesIO(data)):
                    raise ValueError(f"内容不是合法 zip（{len(data)} bytes，可能被截断或镜像返回错误页）")
                dest.write_bytes(data)
                print(f"[GET]   {dest.name} ({len(data)} bytes) <- {prefix or 'direct'}")
                return True
            except Exception as e:  # noqa: BLE001
                print(f"[RETRY] {dest.name} <- {prefix or 'direct'} #{attempt}: {e}", file=sys.stderr)
                time.sleep(2)
    print(f"[FAIL]  {url} -> 全部前缀/重试均失败", file=sys.stderr)
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


def extract_or_redownload(url: str, zip_path: Path, target_dir: Path, prefixes: list[str]) -> int:
    """解包失败 → 删缓存重下一次再试；仍失败返回 -1（不抛异常炸整步）。"""
    try:
        return extract_assets(zip_path, target_dir)
    except Exception as e:  # noqa: BLE001
        print(f"[WARN] 解包失败 {zip_path.name}（{e}），删除缓存重下", file=sys.stderr)
        zip_path.unlink(missing_ok=True)
        if not download(url, zip_path, prefixes):
            return -1
        try:
            return extract_assets(zip_path, target_dir)
        except Exception as e2:  # noqa: BLE001
            print(f"[FAIL] 重下后仍无法解包 {zip_path.name}: {e2}", file=sys.stderr)
            return -1


def main() -> int:
    ap = argparse.ArgumentParser(description="拉取 i18n 发布包全量基底")
    ap.add_argument("--config", default=str(REPO_ROOT / "config" / "merger" / "i18n-release.json"))
    ap.add_argument("--pack-config", default=str(REPO_ROOT / "config" / "packer" / "pack-config.json"))
    ap.add_argument("--output", default="build/i18n-extracted/")
    ap.add_argument("--download-dir", default="build/i18n-packs/")
    ap.add_argument("--mirror-prefix", default="", help="优先镜像前缀（本地用，如 https://ghproxy.net/）")
    ap.add_argument("--mc-version", default=None, help="只处理指定版本组（逗号分隔）")
    args = ap.parse_args()

    cfg = load_json(Path(args.config))
    pack_cfg = load_json(Path(args.pack_config))
    out_dir, dl_dir = Path(args.output), Path(args.download_dir)

    # 下载前缀顺序：--mirror-prefix 优先 → 直连 → config 的 fallback_prefixes 镜像
    prefixes: list[str] = []
    if args.mirror_prefix:
        prefixes.append(args.mirror_prefix)
    prefixes.append("")
    prefixes.extend(cfg.get("fallback_prefixes", []))
    prefixes = list(dict.fromkeys(prefixes))

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
            ok = download(url, zip_path, prefixes)
            if not ok and content == "fabric":
                asset, zip_path, url = base_asset, dl_dir / base_asset, url_tpl.format(asset=base_asset)
                ok = download(url, zip_path, prefixes)
                if ok:
                    print(f"[FALLBACK] {group}/fabric 回退基座包 {base_asset}")
            if not ok:
                report["failures"].append(f"{group}/{content}: {asset} 下载失败")
                continue
            n = extract_or_redownload(url, zip_path, out_dir / group / content, prefixes)
            if n < 0:
                report["failures"].append(f"{group}/{content}: {asset} 解包失败")
                continue
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
