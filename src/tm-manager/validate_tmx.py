"""TMX 校验器：检查 tm/ 下翻译记忆库的合法性（文档 4.4.2.6）。

用法: python src/tm-manager/validate_tmx.py tm/

检查项：XML 合法、根元素 tmx、header 含 srclang、tuid 无重复、每个 tu 含源/目标 seg。
"""
from __future__ import annotations

import sys
import xml.etree.ElementTree as ET
from pathlib import Path


def validate(path: Path) -> list[str]:
    errors = []
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError as e:
        return [f"{path.name}: XML 非法 {e}"]
    if root.tag != "tmx":
        errors.append(f"{path.name}: 根元素应为 tmx，实际 {root.tag}")
    header = root.find("header")
    if header is None or not header.get("srclang"):
        errors.append(f"{path.name}: header 缺少 srclang")
    body = root.find("body")
    if body is None:
        return errors + [f"{path.name}: 缺少 body"]
    seen = set()
    for tu in body.findall("tu"):
        tuid = tu.get("tuid", "")
        if tuid in seen:
            errors.append(f"{path.name}: tuid 重复 {tuid}")
        seen.add(tuid)
        tuvs = tu.findall("tuv")
        if len(tuvs) < 2:
            errors.append(f"{path.name}: tuid={tuid} 缺少源/目标对照")
            continue
        for tuv in tuvs:
            if tuv.find("seg") is None:
                errors.append(f"{path.name}: tuid={tuid} 的 tuv 缺少 seg")
    return errors


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__, file=sys.stderr)
        return 2
    target = Path(sys.argv[1])
    files = sorted(target.rglob("*.tmx")) if target.is_dir() else [target]
    all_errors: list[str] = []
    for f in files:
        errs = validate(f)
        all_errors.extend(errs)
        print(f"[{'PASS' if not errs else 'FAIL'}] {f.name}")
    for e in all_errors:
        print(f"[FAIL] {e}", file=sys.stderr)
    return 1 if all_errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
