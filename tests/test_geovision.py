#!/usr/bin/env python3
"""Controlli statici e di sintassi per GeoVision Nova."""

from __future__ import annotations

import re
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_HTML = ROOT / "GeoVision_Nova_v113_AI_QUARTIERI_RIPRISTINATI.html"
HTML = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else DEFAULT_HTML

if not HTML.exists():
    raise SystemExit(f"File non trovato: {HTML}")

source = HTML.read_text(encoding="utf-8")
checks: list[tuple[str, bool]] = []


def check(name: str, condition: bool) -> None:
    checks.append((name, bool(condition)))


version_match = re.search(r"_v(\d+)_", HTML.name)
version = version_match.group(1) if version_match else "113"

check("doctype HTML", source.lstrip().lower().startswith("<!doctype html>"))
check("titolo coerente con la versione", f"<title>GeoVision Nova v{version}</title>" in source)
check("charset UTF-8", 'charset="UTF-8"' in source or "charset=UTF-8" in source)
check("viewport mobile", 'name="viewport"' in source)
check("lingua italiana dichiarata", re.search(r'<html[^>]+lang=["\']it["\']', source, re.I) is not None)
check("Leaflet inizializzato", "leaflet@1.9.4" in source and "L.map('map'" in source)
check("nessuna chiave Google incorporata", not re.search(r"AIza[0-9A-Za-z_-]{30,}", source))
check("nessuna chiave Gemini incorporata", not re.search(r"AIzaSy[0-9A-Za-z_-]{20,}", source))

literal_ids = re.findall(r'\bid=["\']([^"\']+)["\']', source)
duplicate_ids = {name: count for name, count in Counter(literal_ids).items() if count > 1 and name != "g"}
check("nessun ID DOM duplicato", not duplicate_ids)
required_ids = {
    "map", "gmap", "manual", "poi", "place", "search", "menu", "macro",
    "locate", "ring", "reticleDot", "drawer", "sheet", "sheetBody",
    "voice", "sheetClose", "mapsSettings", "photoGallery", "toast",
}
check("controlli UI essenziali", not (required_ids - set(literal_ids)))

for fn in (
    "componentName",
    "googleLocalityAt",
    "googlePlaceById",
    "geographicNameFallback",
    "reverseFallback",
    "aiNarration",
    "aiNarrationRetry",
    "enrichNarration",
):
    check(f"funzione {fn}", re.search(rf"(?:async\s+)?function\s+{fn}\s*\(", source) is not None)

check("priorità quartiere Google", "'neighborhood', 'sublocality_level_5'" in source)
check("livello amministrativo locale Google", "'administrative_area_level_4'" in source)
check("quartiere OpenStreetMap", "a.neighbourhood || a.suburb || a.quarter || a.city_district" in source)
check("frazione OpenStreetMap", "a.hamlet || a.locality || a.village" in source)
check("reverse geocoding locale a zoom 16", "z >= 15 ? 16" in source)
check("rifiuto nomi geografici generici", "function isGenericPlaceName" in source)
check("recupero nome geografico", "await geographicNameFallback(pos)" in source)
check("classificazione quartiere/rione/frazione", "Quartiere / Rione / Frazione" in source)
check("Gemini modello principale", "'gemini-3.5-flash'" in source)
check("Gemini modello di compatibilità", "'gemini-2.5-flash'" in source)
check("stato chiave mancante", "geminiAiState = 'missing_key'" in source)
check("stato chiave non valida", "geminiAiState = 'invalid_key'" in source)
check("stato AI attiva visibile", "Audioguida AI · Gemini attiva" in source)
check("fallback dichiarato visibile", "AI non disponibile · testo informativo di riserva" in source)
check("nessun fallback presentato come AI", "Audioguida AI · verifica in corso" in source)
check("stop retry su errori permanenti", "geminiAiState === 'missing_key' || geminiAiState === 'invalid_key' || geminiAiState === 'quota'" in source)
check("richiesta Gemini con timeout", "new AbortController()" in source and "14000" in source)
check("prompt vieta copia Wikipedia", "Non copiare Wikipedia" in source)
check("voce italiana configurata", "u.lang = 'it-IT'" in source)
check("GPS diretto", "getCurrentPosition" in source and "watchPosition" in source)
check("failover chiavi Google", all(x in source for x in ("findNextConfiguredGoogleKey", "switchGoogleMapKey", "gm_authFailure")))
check("scheda e foto di riserva", "fallbackGeoCard" in source and "google-city-photos" in source)
check("pulizia asincrona e GPS", "clearTimeout" in source and "clearWatch" in source)

scripts = re.findall(r"<script(?:\s[^>]*)?>(.*?)</script>", source, flags=re.I | re.S)
inline_js = "\n".join(scripts)
with tempfile.NamedTemporaryFile("w", suffix=".js", encoding="utf-8") as tmp:
    tmp.write(inline_js)
    tmp.flush()
    syntax = subprocess.run(
        ["node", "--check", tmp.name],
        capture_output=True,
        text=True,
        check=False,
    )
check("sintassi JavaScript", syntax.returncode == 0)

failed = [name for name, ok in checks if not ok]
for name, ok in checks:
    print(f"{'PASS' if ok else 'FAIL'}  {name}")

print(f"\n{len(checks) - len(failed)}/{len(checks)} controlli superati")
if failed:
    if syntax.returncode:
        print(syntax.stderr.strip())
    raise SystemExit(1)
