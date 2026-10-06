"""Build Nahum's open master page from the same template the locked site uses.

The master page carries the broadcast data in the clear, in a
<script type="application/json" id="broadcast-data"> block, and opens straight to the
broadcast with no passcode. It is published as Nahum's private master copy and is
the single source build.py reads when it seals the public site.

Usage:
    python3 make_master.py --data broadcast.json --out qaelum_build_broadcast.html
    python3 make_master.py --data old_master.html --out qaelum_build_broadcast.html
"""
import argparse, json, re
from pathlib import Path

HERE = Path(__file__).resolve().parent
SEALED_TAG = '<script type="application/json" id="sealed">__SEALED_PAYLOAD__</script>'


def load(path: str) -> dict:
    text = Path(path).read_text(encoding="utf-8")
    m = re.search(r'<script type="application/json" id="broadcast-data">(.*?)</script>', text, re.S)
    data = json.loads(m.group(1) if m else text)
    if not isinstance(data.get("editions"), list) or not data["editions"]:
        raise SystemExit("no editions found in the data")
    return data


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    data = load(args.data)
    blob = json.dumps(data, ensure_ascii=False, indent=1).replace("</", "<\\/")
    page = (HERE / "template.html").read_text(encoding="utf-8")
    if SEALED_TAG not in page:
        raise SystemExit("template is missing the sealed payload tag")
    page = page.replace(SEALED_TAG, f'<script type="application/json" id="broadcast-data">\n{blob}\n</script>')
    page = page.replace('<div class="door" id="door">', '<div class="door" id="door" hidden>', 1)
    page = page.replace('<div class="wrap" id="show" hidden>', '<div class="wrap" id="show">', 1)
    Path(args.out).write_text(page, encoding="utf-8")
    newest = max(data["editions"], key=lambda e: e["number"])
    print(f"master page written with edition {newest['number']} ({len(data['editions'])} total): {args.out}")


if __name__ == "__main__":
    main()
