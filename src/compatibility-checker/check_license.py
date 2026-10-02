"""协议合规检查入口（委托 src/merger/check_license.py）。用法: python src/compatibility-checker/check_license.py <zip>|--repo"""
from __future__ import annotations

import runpy
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
runpy.run_path(str(Path(__file__).resolve().parents[1] / "merger" / "check_license.py"), run_name="__main__")
