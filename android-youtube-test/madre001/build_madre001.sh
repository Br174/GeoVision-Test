#!/usr/bin/env bash
set -euo pipefail

HOST_SHA='a15e5192709be6dbafb0c5633e4d1ab9dd0cdd6b'
SOURCE_SHA='68dacd3854ff121bdab368c6f591a52d60a538b2e1a92a5545aadfe90ee45b33'
EXPECTED_SIGNER='716c1a8a139ad956ef8a00f85f153eb0028d109c75b1b938bdf3bb3eb23c22b5'

# Restore the known clean Android host from v138.
git show "$HOST_SHA:android-youtube-test/app/build.gradle" > android-youtube-test/app/build.gradle
git show "$HOST_SHA:android-youtube-test/app/src/main/AndroidManifest.xml" > android-youtube-test/app/src/main/AndroidManifest.xml
git show "$HOST_SHA:android-youtube-test/app/src/main/java/it/geovision/test/MainActivity.java" > android-youtube-test/app/src/main/java/it/geovision/test/MainActivity.java

# Reconstruct ONLY the verified frozen v79 source chunks.
cat \
  android-youtube-test/madre001/parts/part00a.b64 \
  android-youtube-test/madre001/parts/part00b.b64 \
  android-youtube-test/madre001/parts/part01.b64 \
  android-youtube-test/madre001/parts/part02.b64 \
  | tr -d '\n\r ' | base64 -d | gzip -d > /tmp/GeoVision_MADRE_001_SOURCE.html

ACTUAL_SOURCE=$(sha256sum /tmp/GeoVision_MADRE_001_SOURCE.html | awk '{print $1}')
test "$ACTUAL_SOURCE" = "$SOURCE_SHA"
grep -q 'v79 SOLO GRAFICA' /tmp/GeoVision_MADRE_001_SOURCE.html
if grep -q 'v80 SOLO GRAFICA' /tmp/GeoVision_MADRE_001_SOURCE.html; then
  echo 'ERROR: source contains v80 patch'
  exit 1
fi
mkdir -p android-youtube-test/app/src/main/assets
cp /tmp/GeoVision_MADRE_001_SOURCE.html android-youtube-test/app/src/main/assets/geovision.html

python - <<'PY'
from pathlib import Path
import re

g = Path('android-youtube-test/app/build.gradle')
s = g.read_text(encoding='utf-8')
s = re.sub(r"applicationId '[^']+'", "applicationId 'it.geovision.madre001'", s, count=1)
s = re.sub(r'versionCode\s+\d+', 'versionCode 1001', s, count=1)
s = re.sub(r"versionName '[^']+'", "versionName '1.0-madre-001-core-stabile'", s, count=1)
g.write_text(s, encoding='utf-8')

m = Path('android-youtube-test/app/src/main/AndroidManifest.xml')
x = m.read_text(encoding='utf-8')
x = re.sub(r'android:label="[^"]+"', 'android:label="GeoVision MADRE 001"', x, count=1)
m.write_text(x, encoding='utf-8')
PY

grep -q "applicationId 'it.geovision.madre001'" android-youtube-test/app/build.gradle
grep -q 'versionCode 1001' android-youtube-test/app/build.gradle
grep -q 'android:label="GeoVision MADRE 001"' android-youtube-test/app/src/main/AndroidManifest.xml
grep -q 'System.currentTimeMillis()' android-youtube-test/app/src/main/java/it/geovision/test/MainActivity.java
grep -q 'geovision.html?gv=' android-youtube-test/app/src/main/java/it/geovision/test/MainActivity.java

python - <<'PY'
from pathlib import Path
import re
s=Path('android-youtube-test/app/src/main/assets/geovision.html').read_text(encoding='utf-8')
blocks=re.findall(r'<script(?:\s+type="module")?[^>]*>([\s\S]*?)</script>',s)
Path('/tmp/geovision-check.js').write_text('\n'.join(blocks),encoding='utf-8')
print('HTML bytes:', len(s.encode('utf-8')), 'script blocks:', len(blocks))
PY
node --check /tmp/geovision-check.js

(cd android-youtube-test && gradle clean assembleDebug)

APK='android-youtube-test/app/build/outputs/apk/debug/app-debug.apk'
APKSIGNER=$(find "$ANDROID_HOME/build-tools" -type f -name apksigner | sort -V | tail -1)
AAPT=$(find "$ANDROID_HOME/build-tools" -type f -name aapt | sort -V | tail -1)
"$APKSIGNER" verify --print-certs "$APK" | tee /tmp/apksigner.txt
ACTUAL_SIGNER=$(grep -i 'certificate SHA-256 digest:' /tmp/apksigner.txt | head -1 | awk '{print $NF}' | tr '[:upper:]' '[:lower:]' | tr -d ':')
test "$ACTUAL_SIGNER" = "$EXPECTED_SIGNER"
"$AAPT" dump badging "$APK" | tee /tmp/badging.txt
grep -q "package: name='it.geovision.madre001'" /tmp/badging.txt
grep -q "versionCode='1001'" /tmp/badging.txt
grep -q "application-label:'GeoVision MADRE 001'" /tmp/badging.txt

unzip -p "$APK" assets/geovision.html > /tmp/packaged.html
PACKAGED_SHA=$(sha256sum /tmp/packaged.html | awk '{print $1}')
test "$PACKAGED_SHA" = "$SOURCE_SHA"

cp "$APK" GeoVision_MADRE_001_CORE_STABILE.apk
cp /tmp/GeoVision_MADRE_001_SOURCE.html GeoVision_MADRE_001_CORE_STABILE.html
APK_SHA=$(sha256sum GeoVision_MADRE_001_CORE_STABILE.apk | awk '{print $1}')
cat > MANIFEST_MADRE_001.txt <<EOF
GeoVision MADRE 001 CORE STABILE
Package Android isolato: it.geovision.madre001
Version code: 1001
Version name: 1.0-madre-001-core-stabile
Sorgente HTML SHA256: $SOURCE_SHA
APK SHA256: $APK_SHA
Firma SHA256: $EXPECTED_SIGNER
Host Android: v138 cache-bust pulito
Regola: la Madre non viene usata come laboratorio; ogni futura prova usa applicationId diverso.
EOF
zip -j GeoVision_MADRE_001_CORE_STABILE.zip GeoVision_MADRE_001_CORE_STABILE.apk GeoVision_MADRE_001_CORE_STABILE.html MANIFEST_MADRE_001.txt
sha256sum GeoVision_MADRE_001_CORE_STABILE.apk GeoVision_MADRE_001_CORE_STABILE.zip
