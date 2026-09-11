#!/usr/bin/env bash
set -euo pipefail
ROOT='android-youtube-test'
# Rebuild clean Mother 2 first.
bash "$ROOT/madre001/build_madre_originale_002.sh"
# Mother build leaves the exact Mother HTML in app assets.
python "$ROOT/madre001/patch_lab_014_simple_keys.py"
python - <<'PY'
from pathlib import Path
import re
root=Path('android-youtube-test')
g=root/'app/build.gradle'
s=g.read_text(encoding='utf-8')
s=re.sub(r"applicationId '[^']+'", "applicationId 'it.geovision.lab.simplekeys014'", s, count=1)
s=re.sub(r'versionCode\s+\d+', 'versionCode 2014', s, count=1)
s=re.sub(r"versionName '[^']+'", "versionName '1.0-simple-keys-014'", s, count=1)
g.write_text(s,encoding='utf-8')
m=root/'app/src/main/AndroidManifest.xml'
x=m.read_text(encoding='utf-8')
x=re.sub(r'android:label="[^"]+"', 'android:label="LAB 014 SIMPLE KEYS"', x, count=1)
m.write_text(x,encoding='utf-8')
PY
(
 cd "$ROOT"
 gradle clean assembleDebug
)
cp "$ROOT/app/build/outputs/apk/debug/app-debug.apk" LAB_014_SIMPLE_KEYS.apk
cp "$ROOT/app/src/main/assets/geovision.html" LAB_014_SIMPLE_KEYS.html
cat > README_LAB_014.txt <<'EOF'
LAB 014 SIMPLE KEYS
Base: MADRE ORIGINALE 2.
KeyBox usato solo per importazione manuale.
Pannello locale con Google1 Google2 Google3 AI YouTube, ON/OFF individuale e luci rosso/verde.
Nessun failover automatico e nessuna sincronizzazione automatica.
Package: it.geovision.lab.simplekeys014
EOF
zip -j LAB_014_SIMPLE_KEYS.zip LAB_014_SIMPLE_KEYS.apk LAB_014_SIMPLE_KEYS.html README_LAB_014.txt
