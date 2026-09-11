#!/usr/bin/env bash
set -euo pipefail
HOST_SHA='a15e5192709be6dbafb0c5633e4d1ab9dd0cdd6b'
SOURCE_SHA='68dacd3854ff121bdab368c6f591a52d60a538b2e1a92a5545aadfe90ee45b33'
APPROVED_HTML_SHA='a9968ed9870cdeeb27613b73f4e2ef5446696d3810e302f0282018583c338807'
LAB003_HTML_SHA='42aead77c8cac5c36d3eb9ec7cf81b9efb69f8fd5979ebd52a5e4ca01c28cb9b'
LAB004_HTML_SHA='7b2dd92e4ba6c45cc4422a77d4924038900e4f9130f8354c8410b5242c04332c'
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

# Mantiene integralmente la correzione foto approvata del LAB 003.
python "$ROOT/madre001/patch_photo_repair_003.py"
test "$(sha256sum /tmp/GeoVision_LAB_001_SOURCE.html | awk '{print $1}')" = "$LAB003_HTML_SHA"

# Unica nuova modifica LAB 004: riconoscimento preciso di frazioni/località/quartieri.
python "$ROOT/madre001/patch_locality_precision_004.py"
test "$(sha256sum /tmp/GeoVision_LAB_001_SOURCE.html | awk '{print $1}')" = "$LAB004_HTML_SHA"

grep -q 'gvTerritoryPhotos003' /tmp/GeoVision_LAB_001_SOURCE.html
grep -q 'gvFineCandidate004' /tmp/GeoVision_LAB_001_SOURCE.html
grep -q 'gvExactArea004' /tmp/GeoVision_LAB_001_SOURCE.html
grep -q 'googleLocalityAt(lat,lng,preferSpecific=false)' /tmp/GeoVision_LAB_001_SOURCE.html
grep -q "googleLocalityAt(lat, lng, true)" /tmp/GeoVision_LAB_001_SOURCE.html
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
s=re.sub(r"applicationId '[^']+'", "applicationId 'it.geovision.lab.locality004'", s, count=1)
s=re.sub(r'versionCode\s+\d+', 'versionCode 1704', s, count=1)
s=re.sub(r"versionName '[^']+'", "versionName '1.0-lab-locality-004'", s, count=1)
g.write_text(s,encoding='utf-8')

m=root/'app/src/main/AndroidManifest.xml'
x=m.read_text(encoding='utf-8')
needle='    <uses-permission android:name="android.permission.ACCESS_COARSE_LOCATION" />'
extra='''    <uses-permission android:name="android.permission.ACCESS_COARSE_LOCATION" />\n    <uses-permission android:name="it.geovision.permission.KEYBOX_IMPORT" />\n    <queries>\n        <package android:name="it.geovision.keybox" />\n        <package android:name="com.instagram.android" />\n        <package android:name="com.zhiliaoapp.musically" />\n    </queries>'''
if needle not in x: raise SystemExit('manifest permission anchor missing')
x=x.replace(needle,extra,1)
x=re.sub(r'android:label="[^"]+"', 'android:label="LAB 004 FRAZIONI"', x, count=1)
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
"$APKSIGNER" verify --print-certs "$APK" | tee /tmp/lab004-signer.txt
ACTUAL=$(grep -i 'certificate SHA-256 digest:' /tmp/lab004-signer.txt | head -1 | awk '{print $NF}' | tr '[:upper:]' '[:lower:]' | tr -d ':')
test "$ACTUAL" = "$EXPECTED_SIGNER"
"$AAPT" dump badging "$APK" | tee /tmp/lab004-badging.txt
grep -q "package: name='it.geovision.lab.locality004'" /tmp/lab004-badging.txt
grep -q "application-label:'LAB 004 FRAZIONI'" /tmp/lab004-badging.txt
unzip -p "$APK" assets/geovision.html > /tmp/packaged.html
test "$(sha256sum /tmp/packaged.html | awk '{print $1}')" = "$LAB004_HTML_SHA"
grep -q 'gvTerritoryPhotos003' /tmp/packaged.html
grep -q 'gvFineCandidate004' /tmp/packaged.html
grep -q 'gvExactArea004' /tmp/packaged.html
! grep -q 'fallbackGeoCard' /tmp/packaged.html

cp "$APK" LAB_004_FRAZIONI.apk
cp /tmp/GeoVision_LAB_001_SOURCE.html LAB_004_FRAZIONI.html
APK_SHA=$(sha256sum LAB_004_FRAZIONI.apk | awk '{print $1}')
cat > MANIFEST_LAB_004_FRAZIONI.txt <<EOF
LAB 004 FRAZIONI
Base operativa: LAB 003 FOTO, con correzione foto preservata.
Problema: selezionando una frazione/località (es. Montoro Superiore) GeoVision poteva risalire al comune più ampio (Montoro).
Correzione: sui click/ricerche esplicite vengono privilegiate sublocality, neighborhood e località distinte dal comune; la frazione viene risolta con nome + comune/provincia e non viene ricondotta automaticamente al comune.
La località live mentre si sposta la mappa conserva il comportamento precedente: la precisione extra si attiva sulla selezione/ricerca, riducendo regressioni.
Correzione foto LAB 003 mantenuta integralmente.
Nessuna modifica a TTS/AI, KeyBox, failover, social o grafica generale.
Package isolato: it.geovision.lab.locality004
VersionCode: 1704
VersionName: 1.0-lab-locality-004
Firma SHA256: $EXPECTED_SIGNER
HTML BASE SHA256: $APPROVED_HTML_SHA
HTML LAB 003 SHA256: $LAB003_HTML_SHA
HTML LAB 004 SHA256: $LAB004_HTML_SHA
APK SHA256: $APK_SHA
EOF
zip -j LAB_004_FRAZIONI.zip LAB_004_FRAZIONI.apk LAB_004_FRAZIONI.html MANIFEST_LAB_004_FRAZIONI.txt
sha256sum LAB_004_FRAZIONI.apk LAB_004_FRAZIONI.html LAB_004_FRAZIONI.zip
