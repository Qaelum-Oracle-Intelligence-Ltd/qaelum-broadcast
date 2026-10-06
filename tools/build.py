"""Build the passcode-locked QAELUM Build Broadcast page.

Reads the broadcast data (the JSON block from Nahum's master page, or a bare JSON
file), encrypts it, and writes a static site to --out:

    index.html   the page, carrying only ciphertext
    robots.txt   asks crawlers to stay out
    .nojekyll    tells GitHub Pages to serve files as they are

The passcode comes from the BROADCAST_PASSCODE environment variable and is never
written anywhere. Letters are upper-cased and anything that is not A-Z or 0-9 is
dropped before use, in the page and here alike, so "k7md-3xrp" and "K7MD 3XRP"
both work.

Encryption: AES-256-GCM. Key from PBKDF2-HMAC-SHA256, 600,000 iterations, random
16-byte salt. Fresh salt and nonce on every build.

Usage:
    BROADCAST_PASSCODE=... python3 build.py --data master.html --out ../
"""
import argparse, base64, codecs, json, os, re, secrets, sys
from pathlib import Path

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

ITERATIONS = 600_000
HERE = Path(__file__).resolve().parent


def normalise(code: str) -> str:
    return re.sub(r"[^A-Z0-9]", "", code.strip().upper())


def load_data(path: str) -> dict:
    text = Path(path).read_text(encoding="utf-8")
    m = re.search(r'<script type="application/json" id="broadcast-data">(.*?)</script>', text, re.S)
    data = json.loads(m.group(1) if m else text)
    if not isinstance(data.get("editions"), list) or not data["editions"]:
        raise SystemExit("no editions found in the data")
    return data


def seal(data: dict, code: str) -> dict:
    salt, iv = secrets.token_bytes(16), secrets.token_bytes(12)
    key = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=ITERATIONS).derive(code.encode())
    ct = AESGCM(key).encrypt(iv, json.dumps(data, ensure_ascii=False).encode("utf-8"), None)
    b = lambda x: base64.b64encode(x).decode("ascii")
    return {"v": 1, "kdf": "PBKDF2-SHA256", "iter": ITERATIONS, "salt": b(salt), "iv": b(iv), "ct": b(ct)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    raw = os.environ.get("BROADCAST_PASSCODE", "")
    code = normalise(raw)
    if len(code) < 12:
        raise SystemExit("BROADCAST_PASSCODE must have at least 12 letters or digits")

    data = load_data(args.data)
    sealed = seal(data, code)
    template = (HERE / "template.html").read_text(encoding="utf-8")
    page = template.replace("__SEALED_PAYLOAD__", json.dumps(sealed))

    # Refuse to publish anything that names the tools used to write it, in the
    # template or in the edition data. The names are ROT13-encoded so this file
    # does not contain them. The ciphertext is not scanned: it is random base64.
    tool_names = tuple(codecs.decode(w, "rot13") for w in ("pynhqr", "naguebcvp"))
    readable = (template + json.dumps(data, ensure_ascii=False)).lower()
    if any(name in readable for name in tool_names):
        raise SystemExit("refusing to write: a tooling name appears in the template or the edition data")

    # Refuse to write a page that leaks any edition text in the clear.
    for ed in data["editions"]:
        for field in ("headline", "summary"):
            snippet = ed.get(field, "")[:40]
            if snippet and snippet in page:
                raise SystemExit(f"refusing to write: plaintext from edition {ed.get('number')} found in output")

    out = Path(args.out); out.mkdir(parents=True, exist_ok=True)
    (out / "index.html").write_text(page, encoding="utf-8")
    (out / "robots.txt").write_text("User-agent: *\nDisallow: /\n", encoding="utf-8")
    (out / ".nojekyll").write_text("", encoding="utf-8")
    newest = max(data["editions"], key=lambda e: e["number"])
    print(f"built edition {newest['number']} ({len(data['editions'])} total) into {out / 'index.html'}")


if __name__ == "__main__":
    main()
