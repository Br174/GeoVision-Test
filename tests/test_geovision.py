#!/usr/bin/env python3
import re
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path


HTML = Path(sys.argv[1] if len(sys.argv) > 1 else "GeoVision_Nova_v112_QUARTIERI_POI_CORRETTI.html")
source = HTML.read_text(encoding="utf-8")


def check(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)
    print(f"OK  {message}")


check(source.lstrip().lower().startswith("<!doctype html>"), "doctype HTML5 presente")
check(bool(re.search(r'<html[^>]+lang=["\']it["\']', source, re.I)), "lingua italiana dichiarata")
check(bool(re.search(r'<meta[^>]+name=["\']viewport["\']', source, re.I)), "viewport mobile presente")
check("<title>GeoVision Nova v112</title>" in source, "titolo della versione corretto")
check("leaflet@1.9.4" in source and "L.map('map'" in source, "Leaflet inizializzato")

literal_ids = re.findall(r'\bid=["\']([^"\']+)["\']', source)
duplicate_dom_ids = {
    name: count
    for name, count in Counter(literal_ids).items()
    if count > 1 and name != "g"
}
check(not duplicate_dom_ids, f"nessun ID DOM duplicato: {duplicate_dom_ids}")

required_ids = {
    "map", "gmap", "manual", "poi", "place", "search", "menu", "macro",
    "locate", "ring", "reticleDot", "drawer", "sheet", "sheetBody",
    "voice", "sheetClose", "mapsSettings", "photoGallery", "toast",
}
check(not (required_ids - set(literal_ids)), f"controlli UI essenziali presenti: {sorted(required_ids - set(literal_ids))}")

functions = set(re.findall(r'(?:async\s+)?function\s+([A-Za-z_$][\w$]*)\s*\(', source))
required_functions = {
    "currentCenter", "currentZoom", "reverseFallback", "googleLocalityAt",
    "googlePlaceById", "renderOfficialGoogleCard", "openPhotoGallery",
    "startGpsTracking", "stopGpsTracking", "mapLabels", "macroCandidates",
    "scanMacro", "initGoogleMaps", "scheduleLiveLocality", "speak", "stopSpeech",
}
check(not (required_functions - functions), f"funzioni principali presenti: {sorted(required_functions - functions)}")

check(
    "getCurrentPosition" in source
    and "watchPosition" in source
    and "navigator.permissions" not in source,
    "GPS diretto senza pre-controllo Permissions API",
)
check(
    all(token in source for token in ("exactGooglePoi", "googlePlaceById", "poiLocalityName")),
    "catena POI e località completa",
)
check(
    all(token in source for token in ("findNextConfiguredGoogleKey", "switchGoogleMapKey", "gm_authFailure")),
    "gestione e failover delle chiavi Google presenti",
)
check(
    "speechSynthesis" in source and "SpeechSynthesisUtterance" in source,
    "Text-to-Speech Android presente",
)
check(
    "fallbackGeoCard" in source and "google-city-photos" in source,
    "scheda Google e fallback foto presenti",
)
check(
    not re.search(r'AIza[0-9A-Za-z_-]{25,}|sk-[A-Za-z0-9_-]{20,}|gh[pousr]_[A-Za-z0-9]{20,}', source),
    "nessuna chiave o token incorporato nel file",
)
check(
    "AbortController" in source and "clearTimeout" in source and "clearWatch" in source,
    "protezioni asincrone e pulizia GPS presenti",
)

inline_scripts = [
    body
    for attrs, body in re.findall(r"<script([^>]*)>(.*?)</script>", source, re.I | re.S)
    if "src=" not in attrs.lower()
]
with tempfile.NamedTemporaryFile("w", suffix=".js", encoding="utf-8") as js:
    js.write("\n".join(inline_scripts))
    js.flush()
    syntax = subprocess.run(["node", "--check", js.name], capture_output=True, text=True)
check(syntax.returncode == 0, f"sintassi JavaScript valida: {syntax.stderr.strip()}")

print(f"\nTutti i 16 controlli sono superati per {HTML.name}.")
