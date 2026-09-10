#!/usr/bin/env bash
set -euo pipefail
HOST_SHA='a15e5192709be6dbafb0c5633e4d1ab9dd0cdd6b'
SOURCE_SHA='68dacd3854ff121bdab368c6f591a52d60a538b2e1a92a5545aadfe90ee45b33'
APPROVED_HTML_SHA='a9968ed9870cdeeb27613b73f4e2ef5446696d3810e302f0282018583c338807'
LAB_HTML_SHA='f33eeb5a1c194451ec285c38779cb7a7be3815814aa373e8147fafa1a5472a67'
ROOT='android-youtube-test'

# Ricostruisce la stessa sorgente congelata della MADRE 001.
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

# Prima di sperimentare, certifica che la base sia esattamente la MADRE approvata.
cp /tmp/GeoVision_MADRE_001_SOURCE.html /tmp/GeoVision_LAB_001_SOURCE.html
test "$(sha256sum /tmp/GeoVision_LAB_001_SOURCE.html | awk '{print $1}')" = "$APPROVED_HTML_SHA"
grep -q 'instagram://search?query=' /tmp/GeoVision_LAB_001_SOURCE.html
grep -q 'intent://search/?keyword=' /tmp/GeoVision_LAB_001_SOURCE.html
grep -q 'googleDiagImportKeyBox' /tmp/GeoVision_LAB_001_SOURCE.html
grep -q 'gvDiagAdvanceGoogleKey' /tmp/GeoVision_LAB_001_SOURCE.html
! grep -q 'fallbackGeoCard' /tmp/GeoVision_LAB_001_SOURCE.html
! grep -q 'Scheda GeoVision' /tmp/GeoVision_LAB_001_SOURCE.html

# Unica modifica funzionale del LAB: recupero foto territoriali/località.
python "$ROOT/madre001/patch_photo_territory_001.py"
test "$(sha256sum /tmp/GeoVision_LAB_001_SOURCE.html | awk '{print $1}')" = "$LAB_HTML_SHA"
grep -q 'window.gvPhotoDiag' /tmp/GeoVision_LAB_001_SOURCE.html
grep -q 'Montoro Superiore' "$ROOT/madre001/patch_photo_territory_001.py" || true
grep -q 'frazione|località|quartiere|territorio' /tmp/GeoVision_LAB_001_SOURCE.html

# Contenitore Android identico alla MADRE approvata, con KeyBox e social nativi.
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
s=re.sub(r"applicationId '[^']+'", "applicationId 'it.geovision.lab.photo001'", s, count=1)
s=re.sub(r'versionCode\s+\d+', 'versionCode 1701', s, count=1)
s=re.sub(r"versionName '[^']+'", "versionName '1.0-lab-photo-territory-001'", s, count=1)
g.write_text(s,encoding='utf-8')

m=root/'app/src/main/AndroidManifest.xml'
x=m.read_text(encoding='utf-8')
needle='    <uses-permission android:name="android.permission.ACCESS_COARSE_LOCATION" />'
extra='''    <uses-permission android:name="android.permission.ACCESS_COARSE_LOCATION" />\n    <uses-permission android:name="it.geovision.permission.KEYBOX_IMPORT" />\n    <queries>\n        <package android:name="it.geovision.keybox" />\n        <package android:name="com.instagram.android" />\n        <package android:name="com.zhiliaoapp.musically" />\n    </queries>'''
if needle not in x: raise SystemExit('manifest permission anchor missing')
x=x.replace(needle,extra,1)
x=re.sub(r'android:label="[^"]+"', 'android:label="GeoVision LAB FOTO 001"', x, count=1)
m.write_text(x,encoding='utf-8')
PY

JAVA="$ROOT/app/src/main/java/it/geovision/test/MainActivity.java"
grep -q 'it.geovision.keybox.EXPORT_KEYS' "$JAVA"
grep -q 'shouldOverrideUrlLoading' "$JAVA"
grep -q 'Intent.parseUri(url, Intent.URI_INTENT_SCHEME)' "$JAVA"
grep -q 'openExternalDeepLink' "$JAVA"

# Controllo sintassi JavaScript dell'HTML realmente impacchettato.
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
"$APKSIGNER" verify --print-certs "$APK" | tee /tmp/lab-photo001-signer.txt
ACTUAL=$(grep -i 'certificate SHA-256 digest:' /tmp/lab-photo001-signer.txt | head -1 | awk '{print $NF}' | tr '[:upper:]' '[:lower:]' | tr -d ':')
test "$ACTUAL" = "$EXPECTED_SIGNER"
"$AAPT" dump badging "$APK" | tee /tmp/lab-photo001-badging.txt
grep -q "package: name='it.geovision.lab.photo001'" /tmp/lab-photo001-badging.txt
grep -q "application-label:'GeoVision LAB FOTO 001'" /tmp/lab-photo001-badging.txt
unzip -p "$APK" assets/geovision.html > /tmp/packaged.html
test "$(sha256sum /tmp/packaged.html | awk '{print $1}')" = "$LAB_HTML_SHA"
grep -q 'instagram://search?query=' /tmp/packaged.html
grep -q 'intent://search/?keyword=' /tmp/packaged.html
grep -q 'googleDiagImportKeyBox' /tmp/packaged.html
grep -q 'gvDiagAdvanceGoogleKey' /tmp/packaged.html
grep -q 'window.gvPhotoDiag' /tmp/packaged.html
! grep -q 'fallbackGeoCard' /tmp/packaged.html

cp "$APK" GeoVision_LAB_FOTO_TERRITORIO_001.apk
cp /tmp/GeoVision_LAB_001_SOURCE.html GeoVision_LAB_FOTO_TERRITORIO_001.html
APK_SHA=$(sha256sum GeoVision_LAB_FOTO_TERRITORIO_001.apk | awk '{print $1}')
cat > MANIFEST_LAB_FOTO_TERRITORIO_001.txt <<EOF
GeoVision LAB FOTO TERRITORIO 001
Origine certificata: GeoVision MADRE 001 SOCIAL KEYBOX STABILE.
Modifica funzionale unica: recupero foto Google per città, comuni, frazioni, località, quartieri e territori quando il Place ID generale non contiene foto.
Strategia: Place ID diretto -> locality esatta -> sotto-località/quartiere ricavati dal punto geografico -> fallback Places legacy limitato alla stessa area.
Nessuna modifica a: scheda Google, TTS/AI, KeyBox, failover chiavi, social, grafica generale.
Package isolato: it.geovision.lab.photo001
VersionCode: 1701
VersionName: 1.0-lab-photo-territory-001
Firma SHA256: $EXPECTED_SIGNER
HTML MADRE SHA256: $APPROVED_HTML_SHA
HTML LAB SHA256: $LAB_HTML_SHA
APK SHA256: $APK_SHA
Diagnostica runtime disponibile in window.gvPhotoDiag / console [GeoVisionPhoto].
EOF
zip -j GeoVision_LAB_FOTO_TERRITORIO_001.zip \
  GeoVision_LAB_FOTO_TERRITORIO_001.apk \
  GeoVision_LAB_FOTO_TERRITORIO_001.html \
  MANIFEST_LAB_FOTO_TERRITORIO_001.txt
sha256sum GeoVision_LAB_FOTO_TERRITORIO_001.apk GeoVision_LAB_FOTO_TERRITORIO_001.html GeoVision_LAB_FOTO_TERRITORIO_001.zip
