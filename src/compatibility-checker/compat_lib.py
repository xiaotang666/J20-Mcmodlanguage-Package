"""接口兼容性检查共享库（文档第六章冻结契约）。

冻结项（只增不删、禁止改名/改含义）：
- manifest 路径：仓库根 manifest.json
- manifest 字段：schema_version / latest.version / latest.packages /
  packages[].mc_version / loader / asset_name / release_url / md5 / size
- 版本号格式：YYYY.MM.DD-NNN
- Release 资产命名：pack-{mc_version}-{loader}.zip / vp-modules-{mc_version}.zip
- 资源包内部结构：pack.mcmeta + assets/<ns>/lang/zh_cn.*
- VP 包内部结构：vaultpatcher/modules/*.json
"""
from __future__ import annotations

import json
import re
import zipfile
from pathlib import Path

VERSION_RE = re.compile(r"^\d{4}\.\d{2}\.\d{2}-\d{3}$")
ASSET_RE = re.compile(r"^pack-\d+\.\d+(?:\.\d+)?-(forge|fabric|neoforge)\.zip$")
VP_ASSET_RE = re.compile(r"^vp-modules-\d+\.\d+(?:\.\d+)?\.zip$")
LOADERS = {"forge", "fabric", "neoforge"}
MD5_RE = re.compile(r"^[0-9a-f]{32}$")
FROZEN_MANIFEST_FIELDS = ("schema_version",)
FROZEN_LATEST_FIELDS = ("version", "packages")
FROZEN_PACKAGE_FIELDS = ("mc_version", "loader", "asset_name", "release_url", "md5", "size")


def check_manifest(data: dict) -> list[str]:
    errors = []
    for f in FROZEN_MANIFEST_FIELDS:
        if f not in data:
            errors.append(f"manifest 缺少冻结字段 {f}")
    latest = data.get("latest")
    if not isinstance(latest, dict):
        return errors + ["manifest 缺少 latest 对象"]
    for f in FROZEN_LATEST_FIELDS:
        if f not in latest:
            errors.append(f"latest 缺少冻结字段 {f}")
    if "version" in latest and not VERSION_RE.match(str(latest["version"])):
        errors.append(f"latest.version 不符合 YYYY.MM.DD-NNN：{latest['version']}")
    packages = latest.get("packages")
    if not isinstance(packages, list):
        errors.append("latest.packages 必须是数组（禁止改为对象）")
        return errors
    for i, p in enumerate(packages):
        for f in FROZEN_PACKAGE_FIELDS:
            if f not in p:
                errors.append(f"packages[{i}] 缺少冻结字段 {f}")
        if "loader" in p and p["loader"] not in LOADERS:
            errors.append(f"packages[{i}].loader 非法：{p['loader']}（应为 forge/fabric/neoforge）")
        if "asset_name" in p and not ASSET_RE.match(str(p["asset_name"])):
            errors.append(f"packages[{i}].asset_name 不符合 pack-{{mc_version}}-{{loader}}.zip：{p['asset_name']}")
        if "md5" in p and not MD5_RE.match(str(p["md5"])):
            errors.append(f"packages[{i}].md5 不是 32 位小写十六进制：{p['md5']}")
        if "size" in p and not isinstance(p["size"], int):
            errors.append(f"packages[{i}].size 必须是整数（字节数）")
        if "release_url" in p and not str(p["release_url"]).startswith("https://"):
            errors.append(f"packages[{i}].release_url 必须可直接下载（https）")
    for i, p in enumerate(latest.get("vp_packages", []) or []):
        if "asset_name" in p and not VP_ASSET_RE.match(str(p["asset_name"])):
            errors.append(f"vp_packages[{i}].asset_name 不符合 vp-modules-{{mc_version}}.zip：{p['asset_name']}")
    return errors


def check_asset_names(build_dir: Path) -> list[str]:
    errors = []
    for f in sorted(build_dir.glob("*.zip")):
        if not (ASSET_RE.match(f.name) or VP_ASSET_RE.match(f.name)):
            errors.append(f"构建资产命名不合规：{f.name}")
    return errors


def check_md5(manifest: dict, build_dir: Path) -> list[str]:
    import hashlib
    errors = []
    for p in (manifest.get("latest", {}).get("packages", []) or []) + \
             (manifest.get("latest", {}).get("vp_packages", []) or []):
        f = build_dir / p.get("asset_name", "")
        if not f.exists():
            errors.append(f"manifest 引用的资产不存在：{p.get('asset_name')}")
            continue
        h = hashlib.md5(f.read_bytes()).hexdigest()
        if h != p.get("md5"):
            errors.append(f"MD5 不一致：{p.get('asset_name')} manifest={p.get('md5')} 实际={h}")
        if f.stat().st_size != p.get("size"):
            errors.append(f"size 不一致：{p.get('asset_name')}")
    return errors


def check_pack_zip_structure(path: Path) -> list[str]:
    errors = []
    with zipfile.ZipFile(path) as zf:
        names = zf.namelist()
        if "pack.mcmeta" not in names:
            errors.append(f"{path.name}: 缺少 pack.mcmeta")
        if not any(n.startswith("assets/") and "/lang/zh_cn." in n for n in names):
            errors.append(f"{path.name}: 缺少 assets/<ns>/lang/zh_cn.*")
    return errors


def check_vp_zip_structure(path: Path) -> list[str]:
    errors = []
    with zipfile.ZipFile(path) as zf:
        for n in zf.namelist():
            if not (n.startswith("vaultpatcher/modules/") and n.endswith(".json")):
                errors.append(f"{path.name}: VP 包内非法路径 {n}")
    return errors


def check_pack_format(projects_dir: Path, pack_config: dict) -> list[str]:
    """projects/<mc_version>/ 目录必须能在 pack_format_table 中映射到整数。"""
    errors = []
    table = pack_config.get("pack_format_table", {})
    for d in sorted(p for p in projects_dir.iterdir() if p.is_dir()):
        if d.name not in table:
            errors.append(f"projects/{d.name} 在 pack_format_table 中无映射，pack_format 无法确定")
    for pack in pack_config.get("packs", []):
        if pack["mc_version"] not in table:
            errors.append(f"目标包 {pack['mc_version']} 在 pack_format_table 中无映射")
        elif table[pack["mc_version"]] != pack["pack_format"]:
            errors.append(f"{pack['mc_version']} 的 pack_format 与映射表不一致："
                          f"{pack['pack_format']} != {table[pack['mc_version']]}")
    return errors


def check_vp_modules(vaultpatcher_dir: Path) -> list[str]:
    errors = []
    modules = sorted((vaultpatcher_dir / "modules").glob("*.json")) if (vaultpatcher_dir / "modules").is_dir() else []
    for m in modules:
        try:
            data = json.loads(m.read_text(encoding="utf-8"))
        except ValueError as e:
            errors.append(f"{m.name}: JSON 非法 {e}")
            continue
        if not isinstance(data, list) or not data:
            errors.append(f"{m.name}: VP 模块应为非空数组")
            continue
        head = data[0]
        for field in ("name", "authors", "mods"):
            if field not in head:
                errors.append(f"{m.name}: 模块头缺少字段 {field}")
        if len(data) < 2 or "target_classes" not in data[1] or "pairs" not in data[1]:
            errors.append(f"{m.name}: 缺少 target_classes/pairs 补丁体")
    return errors
