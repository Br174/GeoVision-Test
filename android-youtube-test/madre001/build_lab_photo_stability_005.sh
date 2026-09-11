#!/usr/bin/env bash
set -euo pipefail
HOST_SHA='a15e5192709be6dbafb0c5633e4d1ab9dd0cdd6b'
SOURCE_SHA='68dacd3854ff121bdab368c6f591a52d60a538b2e1a92a5545aadfe90ee45b33'
PREV_MADRE_HTML_SHA='a9968ed9870cdeeb27613b73f4e2ef5446696d3810e302f0282018583c338807'
MADRE1_HTML_SHA='42aead77c8cac5c36d3eb9ec7cf81b9efb69f8fd5979ebd52a5e4ca01c28cb9b'
LAB_HTML_SHA='762bd72e828a6811d9da3d07a12bc80ff7c7d09acd72a9b6e9b2d3bae668b8d8'
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
test "$(sha256sum /tmp/GeoVision_MADRE_001_SOURCE.html | awk '{print $1}')" = "$PREV_MADRE_HTML_SHA"

# Ricostruisce esattamente MADRE ORIGINALE 1 prima di qualsiasi nuovo esperimento.
cp /tmp/GeoVision_MADRE_001_SOURCE.html /tmp/GeoVision_LAB_001_SOURCE.html
python "$ROOT/madre001/patch_candidate_photo_001.py"
test "$(sha256sum /tmp/GeoVision_LAB_001_SOURCE.html | awk '{print $1}')" = "$MADRE1_HTML_SHA"

# LAB 005: aggiunge solo stabilizzazione foto/Places e failover diagnostico.
cp /tmp/GeoVision_LAB_001_SOURCE.html /tmp/GeoVision_LAB_005_SOURCE.html
python "$ROOT/madre001/patch_photo_stability_005.py"
test "$(sha256sum /tmp/GeoVision_LAB_005_SOURCE.html | awk '{print $1}')" = "$LAB_HTML_SHA"

grep -q 'gvPhotoRecover005' /tmp/GeoVision_LAB_005_SOURCE.html
grep -q 'gvPhoto005Record' /tmp/GeoVision_LAB_005_SOURCE.html
grep -q 'gvTerritoryPhotos003' /tmp/GeoVision_LAB_005_SOURCE.html
grep -q 'gvDiagAdvanceGoogleKey' /tmp/GeoVision_LAB_005_SOURCE.html
! grep -q 'gvLocalityPrecision004' /tmp/GeoVision_LAB_005_SOURCE.html
! grep -q 'fallbackGeoCard' /tmp/GeoVision_LAB_005_SOURCE.html

git show "$HOST_SHA:$ROOT/app/build.gradle" > "$ROOT/app/build.gradle"
git show "$HOST_SHA:$ROOT/app/src/main/AndroidManifest.xml" > "$ROOT/app/src/main/AndroidManifest.xml"
git show "$HOST_SHA:$ROOT/app/src/main/java/it/geovision/test/MainActivity.java" > "$ROOT/app/src/main/java/it/geovision/test/MainActivity.java"
mkdir -p "$ROOT/app/src/main/assets"
cp /tmp/GeoVision_LAB_005_SOURCE.html "$ROOT/app/src/main/assets/geovision.html"
python "$ROOT/madre001/patch_mainactivity_keybox.py"
python "$ROOT/madre001/patch_social_native_links.py"

python - <<'PY'
from pathlib import Path
import re
root=Path('android-youtube-test')
g=root/'app/build.gradle'
s=g.read_text(encoding='utf-8')
s=re.sub(r"applicationId '[^']+'", "applicationId 'it.geovision.lab.photo005'", s, count=1)
s=re.sub(r'versionCode\s+\d+', 'versionCode 2005', s, count=1)
s=re.sub(r"versionName '[^']+'", "versionName '1.0-lab-photo-stability-005'", s, count=1)
g.write_text(s,encoding='utf-8')

m=root/'app/src/main/AndroidManifest.xml'
x=m.read_text(encoding='utf-8')
needle='    <uses-permission android:name="android.permission.ACCESS_COARSE_LOCATION" />'
extra='''    <uses-permission android:name="android.permission.ACCESS_COARSE_LOCATION" />\n    <uses-permission android:name="it.geovision.permission.KEYBOX_IMPORT" />\n    <queries>\n        <package android:name="it.geovision.keybox" />\n        <package android:name="com.instagram.android" />\n        <package android:name="com.zhiliaoapp.musically" />\n    </queries>'''
if needle not in x: raise SystemExit('manifest permission anchor missing')
x=x.replace(needle,extra,1)
x=re.sub(r'android:label="[^"]+"', 'android:label="LAB 005 FOTO"', x, count=1)
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
"$APKSIGNER" verify --print-certs "$APK" | tee /tmp/lab005-signer.txt
ACTUAL=$(grep -i 'certificate SHA-256 digest:' /tmp/lab005-signer.txt | head -1 | awk '{print $NF}' | tr '[:upper:]' '[:lower:]' | tr -d ':')
test "$ACTUAL" = "$EXPECTED_SIGNER"
"$AAPT" dump badging "$APK" | tee /tmp/lab005-badging.txt
grep -q "package: name='it.geovision.lab.photo005'" /tmp/lab005-badging.txt
grep -q "application-label:'LAB 005 FOTO'" /tmp/lab005-badging.txt
unzip -p "$APK" assets/geovision.html > /tmp/packaged.html
test "$(sha256sum /tmp/packaged.html | awk '{print $1}')" = "$LAB_HTML_SHA"
grep -q 'gvPhotoRecover005' /tmp/packaged.html
grep -q 'gvPhoto005Record' /tmp/packaged.html
! grep -q 'gvLocalityPrecision004' /tmp/packaged.html

cp "$APK" LAB_005_FOTO.apk
cp /tmp/GeoVision_LAB_005_SOURCE.html LAB_005_FOTO.html
APK_SHA=$(sha256sum LAB_005_FOTO.apk | awk '{print $1}')
cat > MANIFEST_LAB_005_FOTO.txt <<EOF
LAB 005 FOTO
Base: MADRE ORIGINALE 1 pulita e verificata.
Scopo: rendere stabile il recupero foto/Place ID quando la stessa build smette di mostrare foto dopo un riavvio o un cambio stato delle API.
Metodo sperimentale: retry Places controllato + rilevazione errori chiave + failover automatico + recupero Place ID/foto senza modificare la scheda Google.
Package/famiglia Android separata: it.geovision.lab.photo005
VersionCode: 2005
VersionName: 1.0-lab-photo-stability-005
Firma SHA256: $EXPECTED_SIGNER
HTML MADRE ORIGINALE 1 SHA256: $MADRE1_HTML_SHA
HTML LAB 005 SHA256: $LAB_HTML_SHA
APK SHA256: $APK_SHA
Regola: questa LAB non diventa candidata per conversione. Se approvata, si prende solo il metodo e si applica a una candidata pulita ricostruita dalla MADRE ORIGINALE 1.
EOF
zip -j LAB_005_FOTO.zip LAB_005_FOTO.apk LAB_005_FOTO.html MANIFEST_LAB_005_FOTO.txt
sha256sum LAB_005_FOTO.apk LAB_005_FOTO.html LAB_005_FOTO.zip
