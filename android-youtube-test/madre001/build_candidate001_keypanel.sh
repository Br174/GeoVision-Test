#!/usr/bin/env bash
set -euo pipefail
HOST_SHA='a15e5192709be6dbafb0c5633e4d1ab9dd0cdd6b'
SOURCE_SHA='68dacd3854ff121bdab368c6f591a52d60a538b2e1a92a5545aadfe90ee45b33'
PATCHED_SHA='2eabcda1e3f585a5962a145e9c22412e51f38b0921e541c4b86476b1d2b4ed42'
ROOT='android-youtube-test'

cat \
  "$ROOT/madre001/parts/part00a.b64" \
  "$ROOT/madre001/parts/part00b.b64" \
  "$ROOT/madre001/parts/part01.b64" \
  "$ROOT/madre001/parts/part02.b64" \
  | tr -d '\n\r ' | base64 -d | gzip -d > /tmp/GeoVision_MADRE_001_SOURCE.html

ACTUAL=$(sha256sum /tmp/GeoVision_MADRE_001_SOURCE.html | awk '{print $1}')
test "$ACTUAL" = "$SOURCE_SHA"
python "$ROOT/madre001/patch_key_panel.py"
PATCHED=$(sha256sum /tmp/GeoVision_MADRE_001_SOURCE.html | awk '{print $1}')
test "$PATCHED" = "$PATCHED_SHA"
grep -q 'id="googleDiagKey"' /tmp/GeoVision_MADRE_001_SOURCE.html
grep -q 'id="googleDiagSave"' /tmp/GeoVision_MADRE_001_SOURCE.html

git show "$HOST_SHA:$ROOT/app/build.gradle" > "$ROOT/app/build.gradle"
git show "$HOST_SHA:$ROOT/app/src/main/AndroidManifest.xml" > "$ROOT/app/src/main/AndroidManifest.xml"
git show "$HOST_SHA:$ROOT/app/src/main/java/it/geovision/test/MainActivity.java" > "$ROOT/app/src/main/java/it/geovision/test/MainActivity.java"
mkdir -p "$ROOT/app/src/main/assets"
cp /tmp/GeoVision_MADRE_001_SOURCE.html "$ROOT/app/src/main/assets/geovision.html"

python - <<'PY'
from pathlib import Path
import re
root=Path('android-youtube-test')
g=root/'app/build.gradle'
s=g.read_text(encoding='utf-8')
s=re.sub(r"applicationId '[^']+'", "applicationId 'it.geovision.candidate001.keypanel'", s, count=1)
s=re.sub(r'versionCode\s+\d+', 'versionCode 1101', s, count=1)
s=re.sub(r"versionName '[^']+'", "versionName '1.0-candidate-001-key-panel'", s, count=1)
g.write_text(s,encoding='utf-8')
m=root/'app/src/main/AndroidManifest.xml'
x=m.read_text(encoding='utf-8')
x=re.sub(r'android:label="[^"]+"', 'android:label="GeoVision CANDIDATA 001"', x, count=1)
m.write_text(x,encoding='utf-8')
PY

python - <<'PY'
from pathlib import Path
import re
p=Path('android-youtube-test/app/src/main/assets/geovision.html')
s=p.read_text(encoding='utf-8')
blocks=re.findall(r'<script(?:\s+type="module")?[^>]*>([\s\S]*?)</script>',s)
Path('/tmp/geovision-check.js').write_text('\n'.join(blocks),encoding='utf-8')
print('HTML bytes:',p.stat().st_size,'script blocks:',len(blocks))
PY
node --check /tmp/geovision-check.js

(
  cd "$ROOT"
  gradle clean assembleDebug
)

APK="$ROOT/app/build/outputs/apk/debug/app-debug.apk"
APKSIGNER=$(find "$ANDROID_HOME/build-tools" -type f -name apksigner | sort -V | tail -1)
AAPT=$(find "$ANDROID_HOME/build-tools" -type f -name aapt | sort -V | tail -1)
"$APKSIGNER" verify --print-certs "$APK" | tee /tmp/apksigner.txt
EXPECTED_SIGNER='716c1a8a139ad956ef8a00f85f153eb0028d109c75b1b938bdf3bb3eb23c22b5'
ACTUAL_SIGNER=$(grep -i 'certificate SHA-256 digest:' /tmp/apksigner.txt | head -1 | awk '{print $NF}' | tr '[:upper:]' '[:lower:]' | tr -d ':')
test "$ACTUAL_SIGNER" = "$EXPECTED_SIGNER"
"$AAPT" dump badging "$APK" | tee /tmp/badging.txt
grep -q "package: name='it.geovision.candidate001.keypanel'" /tmp/badging.txt
grep -q "versionCode='1101'" /tmp/badging.txt
grep -q "application-label:'GeoVision CANDIDATA 001'" /tmp/badging.txt
unzip -p "$APK" assets/geovision.html > /tmp/packaged.html
PKG_SHA=$(sha256sum /tmp/packaged.html | awk '{print $1}')
test "$PKG_SHA" = "$PATCHED_SHA"

cp "$APK" GeoVision_CANDIDATA_001_KEY_PANEL.apk
cp /tmp/GeoVision_MADRE_001_SOURCE.html GeoVision_CANDIDATA_001_KEY_PANEL.html
APK_SHA=$(sha256sum GeoVision_CANDIDATA_001_KEY_PANEL.apk | awk '{print $1}')
cat > MANIFEST_CANDIDATA_001_KEY_PANEL.txt <<EOF
GeoVision CANDIDATA 001 · KEY PANEL
Base: sorgente v79 congelato della candidata Madre 001
Modifica unica: campo Chiave API Google + Salva e attiva dentro Diagnostica Google
Scheda Google: non modificata
Package Android isolato: it.geovision.candidate001.keypanel
Version code: 1101
Version name: 1.0-candidate-001-key-panel
HTML base SHA256: $SOURCE_SHA
HTML patched SHA256: $PATCHED_SHA
APK SHA256: $APK_SHA
Firma SHA256: $EXPECTED_SIGNER
EOF
zip -j GeoVision_CANDIDATA_001_KEY_PANEL.zip \
  GeoVision_CANDIDATA_001_KEY_PANEL.apk \
  GeoVision_CANDIDATA_001_KEY_PANEL.html \
  MANIFEST_CANDIDATA_001_KEY_PANEL.txt
sha256sum GeoVision_CANDIDATA_001_KEY_PANEL.apk GeoVision_CANDIDATA_001_KEY_PANEL.zip
