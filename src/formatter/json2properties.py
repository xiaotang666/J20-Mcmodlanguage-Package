"""JSON ↔ OmegaT .properties 双向转换（文档 4.4.2.3）。

用法:
    python src/formatter/json2properties.py <en_us.json> <en_us.properties>
    python src/formatter/properties2json.py <zh_cn.properties> <zh_cn.json>
"""
from __future__ import annotations

import json
import sys
from pathlib import Path


def json_to_properties(json_file: Path, props_file: Path) -> int:
    data = json.loads(json_file.read_text(encoding="utf-8"))
    lines = []
    for key, value in data.items():
        escaped = str(value).replace("\\", "\\\\").replace("\n", "\\n").replace("=", "\\=").replace(":", "\\:")
        lines.append(f"{key}={escaped}")
    props_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return len(data)


def main() -> int:
    if len(sys.argv) != 3:
        print(__doc__, file=sys.stderr)
        return 2
    n = json_to_properties(Path(sys.argv[1]), Path(sys.argv[2]))
    print(f"已转换 {n} 条 -> {sys.argv[2]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
