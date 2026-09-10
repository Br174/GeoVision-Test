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
python "$ROOT/madre001/patch_google_key_failover_004_bootsafe.py"
PATCHED_SHA=$(sha256sum /tmp/GeoVision_MADRE_001_SOURCE.html | awk '{print $1}')

# Preserve the already-proven HTML social search routes byte-for-byte.
grep -q 'instagram://search?query=' /tmp/GeoVision_MADRE_001_SOURCE.html
grep -q 'intent://search/?keyword=' /tmp/GeoVision_MADRE_001_SOURCE.html
grep -q 'scheme=snssdk1233' /tmp/GeoVision_MADRE_001_SOURCE.html
grep -q 'package=com.zhiliaoapp.musically' /tmp/GeoVision_MADRE_001_SOURCE.html
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
s=re.sub(r"applicationId '[^']+'", "applicationId 'it.geovision.lab.social001'", s, count=1)
s=re.sub(r'versionCode\s+\d+', 'versionCode 1501', s, count=1)
s=re.sub(r"versionName '[^']+'", "versionName '1.0-lab-social-native-links-001'", s, count=1)
g.write_text(s,encoding='utf-8')

m=root/'app/src/main/AndroidManifest.xml'
x=m.read_text(encoding='utf-8')
needle='    <uses-permission android:name="android.permission.ACCESS_COARSE_LOCATION" />'
extra='''    <uses-permission android:name="android.permission.ACCESS_COARSE_LOCATION" />\n    <uses-permission android:name="it.geovision.permission.KEYBOX_IMPORT" />\n    <queries>\n        <package android:name="it.geovision.keybox" />\n        <package android:name="com.instagram.android" />\n        <package android:name="com.zhiliaoapp.musically" />\n    </queries>'''
if needle not in x: raise SystemExit('manifest permission anchor missing')
x=x.replace(needle,extra,1)
x=re.sub(r'android:label="[^"]+"', 'android:label="GeoVision LAB SOCIAL 001"', x, count=1)
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
"$APKSIGNER" verify --print-certs "$APK" | tee /tmp/social-signer.txt
ACTUAL=$(grep -i 'certificate SHA-256 digest:' /tmp/social-signer.txt | head -1 | awk '{print $NF}' | tr '[:upper:]' '[:lower:]' | tr -d ':')
test "$ACTUAL" = "$EXPECTED_SIGNER"
"$AAPT" dump badging "$APK" | tee /tmp/social-badging.txt
grep -q "package: name='it.geovision.lab.social001'" /tmp/social-badging.txt
grep -q "application-label:'GeoVision LAB SOCIAL 001'" /tmp/social-badging.txt
unzip -p "$APK" assets/geovision.html > /tmp/packaged.html
test "$(sha256sum /tmp/packaged.html | awk '{print $1}')" = "$PATCHED_SHA"
grep -q 'instagram://search?query=' /tmp/packaged.html
grep -q 'intent://search/?keyword=' /tmp/packaged.html
! grep -q 'fallbackGeoCard' /tmp/packaged.html

cp "$APK" GeoVision_LAB_SOCIAL_NATIVE_001.apk
cp /tmp/GeoVision_MADRE_001_SOURCE.html GeoVision_LAB_SOCIAL_NATIVE_001.html
LAB_SHA=$(sha256sum GeoVision_LAB_SOCIAL_NATIVE_001.apk | awk '{print $1}')
cat > MANIFEST_LAB_SOCIAL_NATIVE_001.txt <<EOF
GeoVision LAB SOCIAL NATIVE 001
Base: LAB KEY FAILOVER 004 BOOTSAFE, device-confirmed functional.
Unica modifica funzionale: il WebView Android intercetta schemi app/intent e li passa ad Android.
HTML Instagram preservato: instagram://search?query=...
HTML TikTok preservato: intent://search/?keyword=... con package com.zhiliaoapp.musically e browser fallback.
HTTP/HTTPS: comportamento WebView preesistente invariato.
Google card, KeyBox, failover Google, TTS e UI: non modificati.
Package isolato: it.geovision.lab.social001
Firma SHA256: $EXPECTED_SIGNER
HTML SHA256: $PATCHED_SHA
APK SHA256: $LAB_SHA
EOF
zip -j GeoVision_LAB_SOCIAL_NATIVE_001.zip \
  GeoVision_LAB_SOCIAL_NATIVE_001.apk \
  GeoVision_LAB_SOCIAL_NATIVE_001.html \
  MANIFEST_LAB_SOCIAL_NATIVE_001.txt
sha256sum GeoVision_LAB_SOCIAL_NATIVE_001.apk GeoVision_LAB_SOCIAL_NATIVE_001.zip
