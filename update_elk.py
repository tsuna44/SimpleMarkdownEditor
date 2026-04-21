#!/usr/bin/env python3
"""
update_elk.py — Update elkjs inline in standalone_SimpleMarkdownEditor.html

Usage:
  python update_elk.py             # update to latest version
  python update_elk.py 0.11.1      # update to specific version
  python update_elk.py --check     # show current and latest versions only
"""
import sys
import re
import json
import urllib.request
from pathlib import Path

HTML_PATH     = Path(__file__).parent / "HTML" / "standalone_SimpleMarkdownEditor.html"
VENDOR_JS     = Path(__file__).parent / "vendor" / "elk.bundled.js"
VERSIONS_JSON = Path(__file__).parent / "vendor" / "VERSIONS.json"
CDN_BASE      = "https://cdn.jsdelivr.net/npm/elkjs@{version}/lib/elk.bundled.js"
NPM_LATEST    = "https://registry.npmjs.org/elkjs/latest"

BEGIN_PATTERN = re.compile(r"<!-- ELK_BEGIN v([\d.]+) -->")
BLOCK_PATTERN = re.compile(
    r"<!-- ELK_BEGIN v[\d.]+ -->.*?<!-- ELK_END -->",
    re.DOTALL,
)


def current_version(content: str) -> str:
    m = BEGIN_PATTERN.search(content)
    return m.group(1) if m else "unknown"


def latest_version() -> str:
    print("Fetching latest elkjs version from npm...")
    with urllib.request.urlopen(NPM_LATEST, timeout=15) as r:
        return json.loads(r.read())["version"]


def fetch_elk(version: str) -> str:
    url = CDN_BASE.format(version=version)
    print(f"Downloading elkjs v{version} from jsDelivr...")
    with urllib.request.urlopen(url, timeout=60) as r:
        if r.status != 200:
            raise RuntimeError(f"HTTP {r.status}: {url}")
        return r.read().decode("utf-8")


def main():
    args = sys.argv[1:]

    content = HTML_PATH.read_text(encoding="utf-8")
    cur = current_version(content)
    print(f"Current elkjs version : v{cur}")

    if "--check" in args:
        lat = latest_version()
        print(f"Latest  elkjs version : v{lat}")
        if cur == lat:
            print("Already up to date.")
        else:
            print(f"Run without --check to update: python update_elk.py {lat}")
        return

    target = args[0] if args else latest_version()
    print(f"Target  elkjs version : v{target}")

    if cur == target:
        print("Already at target version. Nothing to do.")
        return

    js = fetch_elk(target)
    replacement = (
        f"<!-- ELK_BEGIN v{target} -->\n"
        f"<script>{js}</script>\n"
        f"<!-- ELK_END -->"
    )

    new_content, count = BLOCK_PATTERN.subn(lambda _: replacement, content)
    if count == 0:
        print("ERROR: Could not find ELK_BEGIN/END markers in HTML file.", file=sys.stderr)
        sys.exit(1)

    new_content = re.sub(
        r"(mermaid v[\d.]+ / elkjs v)[\d.]+",
        lambda m: m.group(1) + target,
        new_content,
    )

    HTML_PATH.write_text(new_content, encoding="utf-8")
    print(f"Done. Updated v{cur} → v{target}")
    print(f"File: {HTML_PATH}")

    VENDOR_JS.parent.mkdir(parents=True, exist_ok=True)
    VENDOR_JS.write_text(js, encoding="utf-8")
    print(f"Updated vendor: {VENDOR_JS}")

    versions = {}
    if VERSIONS_JSON.exists():
        versions = json.loads(VERSIONS_JSON.read_text(encoding="utf-8"))
    versions["elkjs"] = target
    VERSIONS_JSON.write_text(json.dumps(versions, indent=2) + "\n", encoding="utf-8")
    print(f"Updated versions: {VERSIONS_JSON}")


if __name__ == "__main__":
    main()
