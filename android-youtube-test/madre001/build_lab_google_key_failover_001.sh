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
python "$ROOT/madre001/patch_google_key_failover.py"
PATCHED_SHA=$(sha256sum /tmp/GeoVision_MADRE_001_SOURCE.html | awk '{print $1}')

grep -q 'googleDiagImportKeyBox' /tmp/GeoVision_MADRE_001_SOURCE.html
grep -q 'gvRotateGoogleKey' /tmp/GeoVision_MADRE_001_SOURCE.html
grep -q 'gvInstallGoogleKeyFailoverHooks' /tmp/GeoVision_MADRE_001_SOURCE.html
grep -q 'RESOURCE_EXHAUSTED' /tmp/GeoVision_MADRE_001_SOURCE.html
grep -q 'geovision_google_active_key_index' /tmp/GeoVision_MADRE_001_SOURCE.html
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
s=re.sub(r"applicationId '[^']+'", "applicationId 'it.geovision.lab.googlekeys001'", s, count=1)
s=re.sub(r'versionCode\s+\d+', 'versionCode 1401', s, count=1)
s=re.sub(r"versionName '[^']+'", "versionName '1.0-lab-google-key-failover-001'", s, count=1)
g.write_text(s,encoding='utf-8')

m=root/'app/src/main/AndroidManifest.xml'
x=m.read_text(encoding='utf-8')
needle='    <uses-permission android:name="android.permission.ACCESS_COARSE_LOCATION" />'
extra='''    <uses-permission android:name="android.permission.ACCESS_COARSE_LOCATION" />\n    <uses-permission android:name="it.geovision.permission.KEYBOX_IMPORT" />\n    <queries>\n        <package android:name="it.geovision.keybox" />\n    </queries>'''
if needle not in x: raise SystemExit('manifest permission anchor missing')
x=x.replace(needle,extra,1)
x=re.sub(r'android:label="[^"]+"', 'android:label="GeoVision LAB KEY 001"', x, count=1)
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
"$APKSIGNER" verify --print-certs "$APK" | tee /tmp/lab-signer.txt
ACTUAL=$(grep -i 'certificate SHA-256 digest:' /tmp/lab-signer.txt | head -1 | awk '{print $NF}' | tr '[:upper:]' '[:lower:]' | tr -d ':')
test "$ACTUAL" = "$EXPECTED_SIGNER"
"$AAPT" dump badging "$APK" | tee /tmp/lab-badging.txt
grep -q "package: name='it.geovision.lab.googlekeys001'" /tmp/lab-badging.txt
grep -q "application-label:'GeoVision LAB KEY 001'" /tmp/lab-badging.txt
unzip -p "$APK" assets/geovision.html > /tmp/packaged.html
test "$(sha256sum /tmp/packaged.html | awk '{print $1}')" = "$PATCHED_SHA"
grep -q 'gvRotateGoogleKey' /tmp/packaged.html
grep -q 'geovision_google_active_key_index' /tmp/packaged.html
! grep -q 'fallbackGeoCard' /tmp/packaged.html

cp "$APK" GeoVision_LAB_KEY_FAILOVER_001.apk
cp /tmp/GeoVision_MADRE_001_SOURCE.html GeoVision_LAB_KEY_FAILOVER_001.html
LAB_SHA=$(sha256sum GeoVision_LAB_KEY_FAILOVER_001.apk | awk '{print $1}')
cat > MANIFEST_LAB_KEY_FAILOVER_001.txt <<EOF
GeoVision LAB KEY FAILOVER 001
Base funzionale: CANDIDATA 003 KeyBox Import + no fallback grafico
Unica nuova funzione: cambio automatico fra 3 chiavi Google
Comportamento: mantiene la chiave attiva finche funziona; su RESOURCE_EXHAUSTED/quota/autorizzazione marca la chiave temporaneamente non disponibile, seleziona la successiva e ricarica Google.
Se tutte le chiavi risultano non disponibili non entra in loop.
Le chiavi marcate vengono riammesse dopo 60 minuti e possono essere ritestate al successivo utilizzo.
Diagnostica: mostra quale Google 1/2/3 e attiva.
Package isolato: it.geovision.lab.googlekeys001
Fallback grafico GeoVision: assente
Pulsanti testata, audioguida e scheda Google ufficiale: preservati
Firma SHA256: $EXPECTED_SIGNER
HTML SHA256: $PATCHED_SHA
APK SHA256: $LAB_SHA
EOF
zip -j GeoVision_LAB_KEY_FAILOVER_001.zip \
  GeoVision_LAB_KEY_FAILOVER_001.apk \
  GeoVision_LAB_KEY_FAILOVER_001.html \
  MANIFEST_LAB_KEY_FAILOVER_001.txt
sha256sum GeoVision_LAB_KEY_FAILOVER_001.apk GeoVision_LAB_KEY_FAILOVER_001.zip
