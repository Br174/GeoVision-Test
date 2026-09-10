#!/usr/bin/env bash
set -euo pipefail
HOST_SHA='a15e5192709be6dbafb0c5633e4d1ab9dd0cdd6b'
SOURCE_SHA='68dacd3854ff121bdab368c6f591a52d60a538b2e1a92a5545aadfe90ee45b33'
APPROVED_HTML_SHA='a9968ed9870cdeeb27613b73f4e2ef5446696d3810e302f0282018583c338807'
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

# Freeze exactly the HTML approved on device in LAB SOCIAL NATIVE 001.
PATCHED_SHA=$(sha256sum /tmp/GeoVision_MADRE_001_SOURCE.html | awk '{print $1}')
test "$PATCHED_SHA" = "$APPROVED_HTML_SHA"
grep -q 'instagram://search?query=' /tmp/GeoVision_MADRE_001_SOURCE.html
grep -q 'intent://search/?keyword=' /tmp/GeoVision_MADRE_001_SOURCE.html
grep -q 'googleDiagImportKeyBox' /tmp/GeoVision_MADRE_001_SOURCE.html
grep -q 'gvDiagAdvanceGoogleKey' /tmp/GeoVision_MADRE_001_SOURCE.html
! grep -q 'fallbackGeoCard' /tmp/GeoVision_MADRE_001_SOURCE.html
! grep -q 'Scheda GeoVision' /tmp/GeoVision_MADRE_001_SOURCE.html

git show "$HOST_SHA:$ROOT/app/build.gradle" > "$ROOT/app/build.gradle"
git show "$HOST_SHA:$ROOT/app/src/main/AndroidManifest.xml" > "$ROOT/app/src/main/AndroidManifest.xml"
git show "$HOST_SHA:$ROOT/app/src/main/java/it/geovision/test/MainActivity.java" > "$ROOT/app/src/main/java/it/geovision/test/MainActivity.java"
mkdir -p "$ROOT/app/src/main/assets"
cp /tmp/GeoVision_MADRE_001_SOURCE.html "$ROOT/app/src/main/assets/geovision.html"
python "$ROOT/madre001/patch_mainactivity_keybox.py"
python "$ROOT/madre001/patch_social_native_links.py"

python - <<'PY'
from pathlib import Path
import re
root=Path('android-youtube-test')
g=root/'app/build.gradle'
s=g.read_text(encoding='utf-8')
s=re.sub(r"applicationId '[^']+'", "applicationId 'it.geovision.madre001'", s, count=1)
s=re.sub(r'versionCode\s+\d+', 'versionCode 1101', s, count=1)
s=re.sub(r"versionName '[^']+'", "versionName '1.0-madre-001-social-keybox-stabile'", s, count=1)
g.write_text(s,encoding='utf-8')

m=root/'app/src/main/AndroidManifest.xml'
x=m.read_text(encoding='utf-8')
needle='    <uses-permission android:name="android.permission.ACCESS_COARSE_LOCATION" />'
extra='''    <uses-permission android:name="android.permission.ACCESS_COARSE_LOCATION" />\n    <uses-permission android:name="it.geovision.permission.KEYBOX_IMPORT" />\n    <queries>\n        <package android:name="it.geovision.keybox" />\n        <package android:name="com.instagram.android" />\n        <package android:name="com.zhiliaoapp.musically" />\n    </queries>'''
if needle not in x: raise SystemExit('manifest permission anchor missing')
x=x.replace(needle,extra,1)
x=re.sub(r'android:label="[^"]+"', 'android:label="GeoVision MADRE 001"', x, count=1)
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
"$APKSIGNER" verify --print-certs "$APK" | tee /tmp/madre001-signer.txt
ACTUAL=$(grep -i 'certificate SHA-256 digest:' /tmp/madre001-signer.txt | head -1 | awk '{print $NF}' | tr '[:upper:]' '[:lower:]' | tr -d ':')
test "$ACTUAL" = "$EXPECTED_SIGNER"
"$AAPT" dump badging "$APK" | tee /tmp/madre001-badging.txt
grep -q "package: name='it.geovision.madre001'" /tmp/madre001-badging.txt
grep -q "application-label:'GeoVision MADRE 001'" /tmp/madre001-badging.txt
unzip -p "$APK" assets/geovision.html > /tmp/packaged.html
test "$(sha256sum /tmp/packaged.html | awk '{print $1}')" = "$APPROVED_HTML_SHA"
grep -q 'instagram://search?query=' /tmp/packaged.html
grep -q 'intent://search/?keyword=' /tmp/packaged.html
grep -q 'gvDiagAdvanceGoogleKey' /tmp/packaged.html
! grep -q 'fallbackGeoCard' /tmp/packaged.html

cp "$APK" GeoVision_MADRE_001_SOCIAL_KEYBOX_STABILE.apk
cp /tmp/GeoVision_MADRE_001_SOURCE.html GeoVision_MADRE_001_SOCIAL_KEYBOX_STABILE.html
APK_SHA=$(sha256sum GeoVision_MADRE_001_SOCIAL_KEYBOX_STABILE.apk | awk '{print $1}')
cat > MANIFEST_MADRE_001_SOCIAL_KEYBOX_STABILE.txt <<EOF
GeoVision MADRE 001 SOCIAL KEYBOX STABILE
PRIMA MADRE UFFICIALE.
Origine: LAB SOCIAL NATIVE 001 approvato su telefono.
Nessuna modifica funzionale rispetto al LAB approvato.
Funzioni verificate: UI/pulsanti, scheda Google, foto Google nella scheda ufficiale, KeyBox, failover chiavi Google, Instagram nativo, TikTok nativo.
Fallback grafico 'Scheda GeoVision': rimosso.
Package Madre fisso: it.geovision.madre001
VersionCode: 1101
VersionName: 1.0-madre-001-social-keybox-stabile
Firma SHA256: $EXPECTED_SIGNER
HTML APPROVATO SHA256: $APPROVED_HTML_SHA
APK SHA256: $APK_SHA
Regola: questa Madre non si usa per esperimenti; i test futuri partono da copie LAB isolate.
EOF
zip -j GeoVision_MADRE_001_SOCIAL_KEYBOX_STABILE.zip \
  GeoVision_MADRE_001_SOCIAL_KEYBOX_STABILE.apk \
  GeoVision_MADRE_001_SOCIAL_KEYBOX_STABILE.html \
  MANIFEST_MADRE_001_SOCIAL_KEYBOX_STABILE.txt
sha256sum GeoVision_MADRE_001_SOCIAL_KEYBOX_STABILE.apk GeoVision_MADRE_001_SOCIAL_KEYBOX_STABILE.html GeoVision_MADRE_001_SOCIAL_KEYBOX_STABILE.zip
