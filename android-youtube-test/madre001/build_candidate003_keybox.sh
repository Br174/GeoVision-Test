#!/usr/bin/env bash
set -euo pipefail
HOST_SHA='a15e5192709be6dbafb0c5633e4d1ab9dd0cdd6b'
SOURCE_SHA='68dacd3854ff121bdab368c6f591a52d60a538b2e1a92a5545aadfe90ee45b33'
ROOT='android-youtube-test'

cat \
  "$ROOT/madre001/parts/part00a.b64" \
  "$ROOT/madre001/parts/part00b.b64" \
  "$ROOT/madre001/parts/part01.b64" \
  "$ROOT/madre001/parts/part02.b64" \
  | tr -d '\n\r ' | base64 -d | gzip -d > /tmp/GeoVision_MADRE_001_SOURCE.html

test "$(sha256sum /tmp/GeoVision_MADRE_001_SOURCE.html | awk '{print $1}')" = "$SOURCE_SHA"
python "$ROOT/madre001/patch_key_panel.py"
python "$ROOT/madre001/patch_no_fallback.py"
python "$ROOT/madre001/patch_keybox_import.py"
PATCHED_SHA=$(sha256sum /tmp/GeoVision_MADRE_001_SOURCE.html | awk '{print $1}')

grep -q 'googleDiagImportKeyBox' /tmp/GeoVision_MADRE_001_SOURCE.html
grep -q 'GeoVisionKeyBox' /tmp/GeoVision_MADRE_001_SOURCE.html
grep -q 'geovision_google_maps_api_key_1' /tmp/GeoVision_MADRE_001_SOURCE.html
grep -q 'geovision_google_maps_api_key_2' /tmp/GeoVision_MADRE_001_SOURCE.html
grep -q 'geovision_google_maps_api_key_3' /tmp/GeoVision_MADRE_001_SOURCE.html
grep -q 'geovision_ai_api_key' /tmp/GeoVision_MADRE_001_SOURCE.html
grep -q 'geovision_youtube_api_key' /tmp/GeoVision_MADRE_001_SOURCE.html
! grep -q 'fallbackGeoCard' /tmp/GeoVision_MADRE_001_SOURCE.html
! grep -q 'Scheda GeoVision' /tmp/GeoVision_MADRE_001_SOURCE.html
grep -q 'id="voice"' /tmp/GeoVision_MADRE_001_SOURCE.html
grep -q 'id="sheetPhotosVisual"' /tmp/GeoVision_MADRE_001_SOURCE.html
grep -q 'gmp-place-details' /tmp/GeoVision_MADRE_001_SOURCE.html

git show "$HOST_SHA:$ROOT/app/build.gradle" > "$ROOT/app/build.gradle"
git show "$HOST_SHA:$ROOT/app/src/main/AndroidManifest.xml" > "$ROOT/app/src/main/AndroidManifest.xml"
git show "$HOST_SHA:$ROOT/app/src/main/java/it/geovision/test/MainActivity.java" > "$ROOT/app/src/main/java/it/geovision/test/MainActivity.java"
mkdir -p "$ROOT/app/src/main/assets"
cp /tmp/GeoVision_MADRE_001_SOURCE.html "$ROOT/app/src/main/assets/geovision.html"
python "$ROOT/madre001/patch_mainactivity_keybox.py"

python - <<'PY'
from pathlib import Path
import re
root=Path('android-youtube-test')
g=root/'app/build.gradle'
s=g.read_text(encoding='utf-8')
s=re.sub(r"applicationId '[^']+'", "applicationId 'it.geovision.candidate003.keyboximport'", s, count=1)
s=re.sub(r'versionCode\s+\d+', 'versionCode 1301', s, count=1)
s=re.sub(r"versionName '[^']+'", "versionName '1.0-candidate-003-keybox-import'", s, count=1)
g.write_text(s,encoding='utf-8')

m=root/'app/src/main/AndroidManifest.xml'
x=m.read_text(encoding='utf-8')
needle='    <uses-permission android:name="android.permission.ACCESS_COARSE_LOCATION" />'
extra='''    <uses-permission android:name="android.permission.ACCESS_COARSE_LOCATION" />\n    <uses-permission android:name="it.geovision.permission.KEYBOX_IMPORT" />\n    <queries>\n        <package android:name="it.geovision.keybox" />\n    </queries>'''
if needle not in x: raise SystemExit('manifest permission anchor missing')
x=x.replace(needle,extra,1)
x=re.sub(r'android:label="[^"]+"', 'android:label="GeoVision CANDIDATA 003"', x, count=1)
m.write_text(x,encoding='utf-8')
PY

grep -q 'it.geovision.permission.KEYBOX_IMPORT' "$ROOT/app/src/main/AndroidManifest.xml"
grep -q 'it.geovision.keybox' "$ROOT/app/src/main/AndroidManifest.xml"
grep -q 'it.geovision.keybox.EXPORT_KEYS' "$ROOT/app/src/main/java/it/geovision/test/MainActivity.java"

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
EXPECTED_SIGNER='716c1a8a139ad956ef8a00f85f153eb0028d109c75b1b938bdf3bb3eb23c22b5'
"$APKSIGNER" verify --print-certs "$APK" | tee /tmp/candidate-signer.txt
ACTUAL=$(grep -i 'certificate SHA-256 digest:' /tmp/candidate-signer.txt | head -1 | awk '{print $NF}' | tr '[:upper:]' '[:lower:]' | tr -d ':')
test "$ACTUAL" = "$EXPECTED_SIGNER"
"$AAPT" dump badging "$APK" | tee /tmp/candidate-badging.txt
grep -q "package: name='it.geovision.candidate003.keyboximport'" /tmp/candidate-badging.txt
grep -q "application-label:'GeoVision CANDIDATA 003'" /tmp/candidate-badging.txt
unzip -p "$APK" assets/geovision.html > /tmp/packaged.html
test "$(sha256sum /tmp/packaged.html | awk '{print $1}')" = "$PATCHED_SHA"
grep -q 'googleDiagImportKeyBox' /tmp/packaged.html
! grep -q 'fallbackGeoCard' /tmp/packaged.html

# Build KeyBox with the same stable GeoVision signing key.
mkdir -p android-keybox/app/src/main/res/drawable-nodpi
cp "$ROOT/app/src/main/res/drawable-nodpi/ic_launcher.png" android-keybox/app/src/main/res/drawable-nodpi/ic_launcher.png
(
  cd android-keybox
  gradle clean assembleDebug
)
KEYBOX_APK='android-keybox/app/build/outputs/apk/debug/app-debug.apk'
"$APKSIGNER" verify --print-certs "$KEYBOX_APK" | tee /tmp/keybox-signer.txt
KEYBOX_SIGNER=$(grep -i 'certificate SHA-256 digest:' /tmp/keybox-signer.txt | head -1 | awk '{print $NF}' | tr '[:upper:]' '[:lower:]' | tr -d ':')
test "$KEYBOX_SIGNER" = "$EXPECTED_SIGNER"
"$AAPT" dump badging "$KEYBOX_APK" | tee /tmp/keybox-badging.txt
grep -q "package: name='it.geovision.keybox'" /tmp/keybox-badging.txt
grep -q "application-label:'GeoVision KeyBox'" /tmp/keybox-badging.txt

cp "$APK" GeoVision_CANDIDATA_003_KEYBOX_IMPORT.apk
cp /tmp/GeoVision_MADRE_001_SOURCE.html GeoVision_CANDIDATA_003_KEYBOX_IMPORT.html
cp "$KEYBOX_APK" GeoVision_KEYBOX_001.apk

CANDIDATE_SHA=$(sha256sum GeoVision_CANDIDATA_003_KEYBOX_IMPORT.apk | awk '{print $1}')
KEYBOX_SHA=$(sha256sum GeoVision_KEYBOX_001.apk | awk '{print $1}')
cat > MANIFEST_CANDIDATA_003_KEYBOX_IMPORT.txt <<EOF
GeoVision CANDIDATA 003 · KEYBOX IMPORT
Base: Candidata 002 no-fallback + pannello chiave
Nuova funzione: Importa tutte da GeoVision KeyBox
Chiavi importate: Google Maps 1, Google Maps 2, Google Maps 3, AI, YouTube
La chiave Google 1 (o la prima non vuota) alimenta anche il campo Google già usato dalla base v79.
Fallback grafico GeoVision: assente
Pulsanti testata e scheda Google ufficiale: preservati
Package isolato: it.geovision.candidate003.keyboximport
Firma SHA256: $EXPECTED_SIGNER
HTML SHA256: $PATCHED_SHA
APK SHA256: $CANDIDATE_SHA
EOF

cat > README_KEYBOX_001.txt <<EOF
GeoVision KeyBox 001
Package: it.geovision.keybox
Contiene 5 campi: Google Maps 1/2/3, AI, YouTube.
Le chiavi sono cifrate con AES-GCM usando Android Keystore.
L'esportazione è protetta da permesso Android protectionLevel=signature: solo app firmate con la stessa firma GeoVision possono richiederle.
Firma SHA256: $EXPECTED_SIGNER
APK SHA256: $KEYBOX_SHA
EOF

zip -j GeoVision_CANDIDATA_003_KEYBOX_IMPORT.zip \
  GeoVision_CANDIDATA_003_KEYBOX_IMPORT.apk \
  GeoVision_CANDIDATA_003_KEYBOX_IMPORT.html \
  MANIFEST_CANDIDATA_003_KEYBOX_IMPORT.txt
zip -j GeoVision_KEYBOX_001.zip GeoVision_KEYBOX_001.apk README_KEYBOX_001.txt
zip -j GeoVision_KEYBOX_IMPORT_KIT.zip \
  GeoVision_KEYBOX_001.apk \
  GeoVision_CANDIDATA_003_KEYBOX_IMPORT.apk \
  GeoVision_CANDIDATA_003_KEYBOX_IMPORT.html \
  README_KEYBOX_001.txt \
  MANIFEST_CANDIDATA_003_KEYBOX_IMPORT.txt

sha256sum GeoVision_KEYBOX_001.apk GeoVision_CANDIDATA_003_KEYBOX_IMPORT.apk GeoVision_KEYBOX_001.zip GeoVision_CANDIDATA_003_KEYBOX_IMPORT.zip GeoVision_KEYBOX_IMPORT_KIT.zip
