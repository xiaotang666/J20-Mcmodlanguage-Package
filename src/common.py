"""J20-Mcmodlanguage-Package 共享工具库。

所有自动化脚本共用：JSON 读写、HTTP 拉取（多镜像回退 + 重试）、MD5、报告写入。
仅依赖 Python 标准库，保证本地与 CI 均可直接运行。
"""
from __future__ import annotations

import hashlib
import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
BUILD_DIR = REPO_ROOT / "build"


# ---------- JSON ----------

def load_json(path: Path | str):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path: Path | str, data, indent: int = 2) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, ensure_ascii=False, indent=indent)
        f.write("\n")


# ---------- HTTP ----------

def http_get(url: str, timeout: int = 30) -> bytes:
    """GET 一个 URL，成功返回 body，失败抛异常。"""
    req = urllib.request.Request(url, headers={"User-Agent": "J20-Mcmodlanguage-Package/0.0.1"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def fetch_with_fallback(path: str, config: dict) -> tuple[bytes | None, str | None, list[str]]:
    """按 base_url + fallback_urls 依次尝试拉取 i18n 仓库中的相对路径。

    返回 (内容, 命中的URL, 尝试过的URL列表)；全部失败返回 (None, None, tried)。
    确定性失败（404/403/400）不重试，直接换下一个源；仅超时/网络/5xx 按 retry_count 重试。
    """
    repo = config["source"]
    branch = config["branch"]
    bases = [config["base_url"]] + list(config.get("fallback_urls", []))
    retry_count = int(config.get("retry_count", 3))
    retry_delay = int(config.get("retry_delay", 5))
    timeout = int(config.get("request_timeout", 15))
    tried: list[str] = []
    for base in bases:
        url = base.format(repo=repo, branch=branch) + path
        for attempt in range(retry_count):
            tried.append(url)
            try:
                return http_get(url, timeout=timeout), url, tried
            except urllib.error.HTTPError as e:
                if e.code in (400, 403, 404, 410, 451):
                    break  # 确定性失败：文件在该源不存在，换下一个源
                if attempt < retry_count - 1:
                    time.sleep(retry_delay)
            except (urllib.error.URLError, TimeoutError, OSError):
                if attempt < retry_count - 1:
                    time.sleep(retry_delay)
    return None, None, tried


# ---------- 校验和 ----------

def md5_bytes(data: bytes) -> str:
    return hashlib.md5(data).hexdigest()


def md5_file(path: Path | str) -> str:
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


# ---------- 报告 ----------

def write_report(name: str, report: dict) -> Path:
    out = BUILD_DIR / name
    save_json(out, report)
    return out


def fail(msg: str) -> None:
    print(f"[FATAL] {msg}", file=sys.stderr)
    sys.exit(1)
