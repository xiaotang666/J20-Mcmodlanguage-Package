"""OmegaT .properties 译文 → zh_cn.json（json2properties 的逆转换）。

用法: python src/formatter/properties2json.py <zh_cn.properties> <zh_cn.json> [--en en_us.json]
--en 提供时按 en_us.json 的键顺序输出，缺失键报警告。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path


def unescape(v: str) -> str:
    out, i = [], 0
    while i < len(v):
        c = v[i]
        if c == "\\" and i + 1 < len(v):
            nxt = v[i + 1]
            out.append({"n": "\n", "t": "\t", "\\": "\\", "=": "=", ":": ":"}.get(nxt, nxt))
            i += 2
        else:
            out.append(c)
            i += 1
    return "".join(out)


def properties_to_json(props_file: Path, json_file: Path, en_file: Path | None = None) -> tuple[int, list[str]]:
    data = {}
    for line in props_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        data[k.strip()] = unescape(v.strip())
    warnings = []
    if en_file:
        order = json.loads(en_file.read_text(encoding="utf-8"))
        missing = [k for k in order if k not in data]
        if missing:
            warnings.append(f"缺少 {len(missing)} 个键：{missing[:10]} ...")
        data = {k: data[k] for k in order if k in data}
    json_file.write_text(json.dumps(data, ensure_ascii=False, indent=4) + "\n", encoding="utf-8")
    return len(data), warnings


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if len(args) != 2:
        print(__doc__, file=sys.stderr)
        return 2
    en_file = None
    if "--en" in sys.argv:
        en_file = Path(sys.argv[sys.argv.index("--en") + 1])
    n, warnings = properties_to_json(Path(args[0]), Path(args[1]), en_file)
    for w in warnings:
        print(f"[WARN] {w}", file=sys.stderr)
    print(f"已还原 {n} 条 -> {args[1]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
