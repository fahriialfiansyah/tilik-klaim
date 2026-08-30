#!/usr/bin/env python3
"""Bongkar bundel Claude Design canvas menjadi berkas yang bisa dibaca manusia.

Tim desain mengirim mockup sebagai satu berkas HTML mandiri: markup dan CSS-nya
disimpan sebagai JSON ter-escape, sedangkan font serta logo disimpan sebagai
blob gzip+base64 berkunci UUID. Bentuk itu bisa dibuka di peramban, tetapi tidak
bisa dibaca saat seseorang harus mengimplementasikan ulang layarnya di React.

Skrip ini menghasilkan dua turunan:

    reference.html   markup + CSS, font diarahkan ke Google Fonts, logo di-inline
    tokens.css       token warna tema terang & gelap, apa adanya dari mockup

Pakai saat tim desain mengirim bundel baru, supaya penyegaran bersifat mekanis
dan tidak ada nilai yang tersalin keliru dengan tangan:

    python3 design/mockup/unpack.py design/mockup/tilik-klaim-v2.bundle.html

Bagian tipografi, jarak, dan alias semantik di design/tokens.css ditulis tangan
dan TIDAK ditimpa — hanya blok warna yang disegarkan.
"""

from __future__ import annotations

import base64
import gzip
import json
import re
import sys
from pathlib import Path

FONT_LINK = (
    '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?'
    "family=IBM+Plex+Mono:wght@400;500;600&"
    'family=IBM+Plex+Sans:wght@400;500;600;700&display=swap">'
)

BANNER = """<!-- TURUNAN - JANGAN DIEDIT LANGSUNG.
     Dibongkar dari {source} lewat design/mockup/unpack.py.
     Interaksi JS sengaja dilepas, jadi placeholder {{{{ ... }}}} tampil apa adanya -
     itu justru menandai titik pengikatan data. -->
"""

UUID_RE = r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"


def read_block(src: str, name: str) -> str:
    """Ambil satu blok <script type="__bundler/NAME"> dari bundel."""
    match = re.search(
        r'<script type="__bundler/%s">\s*(.*?)\s*</script>' % name, src, re.S
    )
    if match is None:
        raise SystemExit(f"blok __bundler/{name} tidak ditemukan — format bundel berubah?")
    return match.group(1)


def decode_asset(entry: dict) -> bytes:
    raw = base64.b64decode(entry["data"])
    return gzip.decompress(raw) if entry.get("compressed") else raw


def build_reference(template: str, manifest: dict, source_name: str) -> str:
    html = re.sub(r'<script src="%s"></script>\s*' % UUID_RE, "", template)
    html = re.sub(r'<script type="text/x-dc".*?</script>', "", html, flags=re.S)
    html = re.sub(r"/\*[^*]*\*/\s*@font-face\s*\{[^}]*\}", "", html)
    html = re.sub(r"@font-face\s*\{[^}]*\}", "", html)

    for uid, entry in manifest.items():
        mime = entry.get("mime", "")
        if not mime.startswith("image/"):
            continue
        blob = base64.b64encode(decode_asset(entry)).decode()
        html = html.replace(f'src="{uid}"', f'src="data:{mime};base64,{blob}"')

    html = html.replace("<head>", "\n".join(("<head>", FONT_LINK)), 1)
    html = html.replace("<html>", '<html lang="id" data-theme="light">', 1)
    return html.replace(
        "<!DOCTYPE html>", "<!DOCTYPE html>\n" + BANNER.format(source=source_name), 1
    )


def extract_tokens(template: str) -> tuple[dict[str, str], dict[str, str]]:
    def block(selector: str) -> dict[str, str]:
        match = re.search(re.escape(selector) + r"\s*\{([^}]*)\}", template)
        if match is None:
            raise SystemExit(f"selector {selector} tidak ditemukan — token pindah tempat?")
        return {
            name: value.strip()
            for name, value in re.findall(r"(--[a-z0-9-]+)\s*:\s*([^;]+)", match.group(1))
        }

    light, dark = block("[data-theme]"), block('[data-theme="dark"]')
    if set(light) != set(dark):
        raise SystemExit(f"token terang/gelap tidak sepadan: {set(light) ^ set(dark)}")
    return light, dark


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)

    bundle = Path(sys.argv[1])
    src = bundle.read_text(encoding="utf-8")
    template = json.loads(read_block(src, "template"))
    manifest = json.loads(read_block(src, "manifest"))

    reference = bundle.with_name("reference.html")
    reference.write_text(build_reference(template, manifest, bundle.name), encoding="utf-8")
    print(f"{reference}  {len(reference.read_bytes()):,} B")

    light, dark = extract_tokens(template)
    print(f"token terbaca: {len(light)} terang + {len(dark)} gelap")
    print("Bandingkan dengan design/tokens.css; segarkan blok warna bila ada selisih.")


if __name__ == "__main__":
    main()
