#!/usr/bin/env bash
set -euo pipefail
HOST_SHA='a15e5192709be6dbafb0c5633e4d1ab9dd0cdd6b'
SOURCE_SHA='68dacd3854ff121bdab368c6f591a52d60a538b2e1a92a5545aadfe90ee45b33'
APPROVED_HTML_SHA='a9968ed9870cdeeb27613b73f4e2ef5446696d3810e302f0282018583c338807'
DIAG_HTML_SHA='42f1320616c0add224a17a22fb76bf19ea2774950f48d2dfc469aa3a77146d2f'
ORIGINAL_PHOTO_FN_SHA='72f60e9a0e5e21473cf7a787ce0cd84f24d6fc7d8cd590e8cded137a9ff0b46c'
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
python "$ROOT/madre001/patch_google_key_failover_004_bootsafe.py"
cp /tmp/GeoVision_MADRE_001_SOURCE.html /tmp/GeoVision_LAB_001_SOURCE.html
test "$(sha256sum /tmp/GeoVision_LAB_001_SOURCE.html | awk '{print $1}')" = "$APPROVED_HTML_SHA"

# Certifica la funzione foto originale PRIMA della diagnostica.
python - <<'PY'
from pathlib import Path
import hashlib
s=Path('/tmp/GeoVision_LAB_001_SOURCE.html').read_text(encoding='utf-8')
st=s.find('async function googleLocalityPhotos(p)')
en=s.find('async function reverseFallback',st)
if st < 0 or en < 0: raise SystemExit('original photo function anchors missing')
h=hashlib.sha256(s[st:en].encode()).hexdigest()
print('Original photo function SHA:',h)
if h != '72f60e9a0e5e21473cf7a787ce0cd84f24d6fc7d8cd590e8cded137a9ff0b46c':
    raise SystemExit('original photo function changed unexpectedly')
PY

# Unica modifica: diagnostica. NON applicare patch_photo_territory_001.py.
python "$ROOT/madre001/patch_photo_diagnostic_002.py"
test "$(sha256sum /tmp/GeoVision_LAB_001_SOURCE.html | awk '{print $1}')" = "$DIAG_HTML_SHA"

# Verifica che la funzione foto originale sia rimasta identica byte-per-byte.
python - <<'PY'
from pathlib import Path
import hashlib
s=Path('/tmp/GeoVision_LAB_001_SOURCE.html').read_text(encoding='utf-8')
st=s.find('async function googleLocalityPhotos(p)')
en=s.find('async function gvPhotoDiagProbe',st)
if st < 0 or en < 0: raise SystemExit('diagnostic insertion anchors missing')
h=hashlib.sha256(s[st:en].encode()).hexdigest()
print('Preserved photo function SHA:',h)
if h != '72f60e9a0e5e21473cf7a787ce0cd84f24d6fc7d8cd590e8cded137a9ff0b46c':
    raise SystemExit('photo function was modified by diagnostic patch')
PY

grep -q 'DIAGNOSI FOTO 002' /tmp/GeoVision_LAB_001_SOURCE.html
grep -q 'gvPhotoDiagProbe' /tmp/GeoVision_LAB_001_SOURCE.html
grep -q 'Text Search senza filtro locality' /tmp/GeoVision_LAB_001_SOURCE.html
! grep -q 'GeoVisionPhotoDiag002.*territory' /tmp/GeoVision_LAB_001_SOURCE.html || true
grep -q 'instagram://search?query=' /tmp/GeoVision_LAB_001_SOURCE.html
grep -q 'intent://search/?keyword=' /tmp/GeoVision_LAB_001_SOURCE.html
grep -q 'googleDiagImportKeyBox' /tmp/GeoVision_LAB_001_SOURCE.html
grep -q 'gvDiagAdvanceGoogleKey' /tmp/GeoVision_LAB_001_SOURCE.html
! grep -q 'fallbackGeoCard' /tmp/GeoVision_LAB_001_SOURCE.html
! grep -q 'Scheda GeoVision' /tmp/GeoVision_LAB_001_SOURCE.html

git show "$HOST_SHA:$ROOT/app/build.gradle" > "$ROOT/app/build.gradle"
git show "$HOST_SHA:$ROOT/app/src/main/AndroidManifest.xml" > "$ROOT/app/src/main/AndroidManifest.xml"
git show "$HOST_SHA:$ROOT/app/src/main/java/it/geovision/test/MainActivity.java" > "$ROOT/app/src/main/java/it/geovision/test/MainActivity.java"
mkdir -p "$ROOT/app/src/main/assets"
cp /tmp/GeoVision_LAB_001_SOURCE.html "$ROOT/app/src/main/assets/geovision.html"
python "$ROOT/madre001/patch_mainactivity_keybox.py"
python "$ROOT/madre001/patch_social_native_links.py"

python - <<'PY'
from pathlib import Path
import re
root=Path('android-youtube-test')
g=root/'app/build.gradle'
s=g.read_text(encoding='utf-8')
s=re.sub(r"applicationId '[^']+'", "applicationId 'it.geovision.lab.photodiag002'", s, count=1)
s=re.sub(r'versionCode\s+\d+', 'versionCode 1702', s, count=1)
s=re.sub(r"versionName '[^']+'", "versionName '1.0-lab-photo-diagnostic-002'", s, count=1)
g.write_text(s,encoding='utf-8')

m=root/'app/src/main/AndroidManifest.xml'
x=m.read_text(encoding='utf-8')
needle='    <uses-permission android:name="android.permission.ACCESS_COARSE_LOCATION" />'
extra='''    <uses-permission android:name="android.permission.ACCESS_COARSE_LOCATION" />\n    <uses-permission android:name="it.geovision.permission.KEYBOX_IMPORT" />\n    <queries>\n        <package android:name="it.geovision.keybox" />\n        <package android:name="com.instagram.android" />\n        <package android:name="com.zhiliaoapp.musically" />\n    </queries>'''
if needle not in x: raise SystemExit('manifest permission anchor missing')
x=x.replace(needle,extra,1)
x=re.sub(r'android:label="[^"]+"', 'android:label="GeoVision FOTO DIAG 002"', x, count=1)
m.write_text(x,encoding='utf-8')
PY

JAVA="$ROOT/app/src/main/java/it/geovision/test/MainActivity.java"
grep -q 'it.geovision.keybox.EXPORT_KEYS' "$JAVA"
grep -q 'shouldOverrideUrlLoading' "$JAVA"
grep -q 'Intent.parseUri(url, Intent.URI_INTENT_SCHEME)' "$JAVA"
grep -q 'openExternalDeepLink' "$JAVA"

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
"$APKSIGNER" verify --print-certs "$APK" | tee /tmp/lab-photodiag002-signer.txt
ACTUAL=$(grep -i 'certificate SHA-256 digest:' /tmp/lab-photodiag002-signer.txt | head -1 | awk '{print $NF}' | tr '[:upper:]' '[:lower:]' | tr -d ':')
test "$ACTUAL" = "$EXPECTED_SIGNER"
"$AAPT" dump badging "$APK" | tee /tmp/lab-photodiag002-badging.txt
grep -q "package: name='it.geovision.lab.photodiag002'" /tmp/lab-photodiag002-badging.txt
grep -q "application-label:'GeoVision FOTO DIAG 002'" /tmp/lab-photodiag002-badging.txt
unzip -p "$APK" assets/geovision.html > /tmp/packaged.html
test "$(sha256sum /tmp/packaged.html | awk '{print $1}')" = "$DIAG_HTML_SHA"
grep -q 'DIAGNOSI FOTO 002' /tmp/packaged.html
grep -q 'instagram://search?query=' /tmp/packaged.html
grep -q 'intent://search/?keyword=' /tmp/packaged.html
grep -q 'googleDiagImportKeyBox' /tmp/packaged.html
grep -q 'gvDiagAdvanceGoogleKey' /tmp/packaged.html
! grep -q 'fallbackGeoCard' /tmp/packaged.html

cp "$APK" GeoVision_LAB_FOTO_DIAG_002.apk
cp /tmp/GeoVision_LAB_001_SOURCE.html GeoVision_LAB_FOTO_DIAG_002.html
APK_SHA=$(sha256sum GeoVision_LAB_FOTO_DIAG_002.apk | awk '{print $1}')
cat > MANIFEST_LAB_FOTO_DIAG_002.txt <<EOF
GeoVision LAB FOTO DIAG 002
Origine: GeoVision MADRE 001 SOCIAL KEYBOX STABILE.
Base foto: IDENTICA al LAB 001 approvato; patch FOTO TERRITORIO 001 esclusa perché ha introdotto una regressione.
Modifica unica: diagnostica visibile soltanto quando la funzione foto originale restituisce zero URL.
Mostra: Place ID, Place Details, Text Search senza filtro locality, Places legacy ed eventuali errori.
Non mostra né registra le chiavi API.
Package isolato: it.geovision.lab.photodiag002
VersionCode: 1702
VersionName: 1.0-lab-photo-diagnostic-002
Firma SHA256: $EXPECTED_SIGNER
HTML MADRE/LAB BASE SHA256: $APPROVED_HTML_SHA
Funzione foto originale SHA256: $ORIGINAL_PHOTO_FN_SHA
HTML DIAG SHA256: $DIAG_HTML_SHA
APK SHA256: $APK_SHA
EOF
zip -j GeoVision_LAB_FOTO_DIAG_002.zip \
  GeoVision_LAB_FOTO_DIAG_002.apk \
  GeoVision_LAB_FOTO_DIAG_002.html \
  MANIFEST_LAB_FOTO_DIAG_002.txt
sha256sum GeoVision_LAB_FOTO_DIAG_002.apk GeoVision_LAB_FOTO_DIAG_002.html GeoVision_LAB_FOTO_DIAG_002.zip
