#!/usr/bin/env bash
set -euo pipefail
ROOT='android-youtube-test'
EXPECTED_SIGNER='716c1a8a139ad956ef8a00f85f153eb0028d109c75b1b938bdf3bb3eb23c22b5'

bash "$ROOT/madre001/build_madre_originale_002.sh"
python "$ROOT/madre001/patch_key_sync_006.py"
python "$ROOT/madre001/patch_android_key_sync_006.py"

python - <<'PY'
from pathlib import Path
import re
root=Path('android-youtube-test')
g=root/'app/build.gradle'
s=g.read_text(encoding='utf-8')
s=re.sub(r"applicationId '[^']+'", "applicationId 'it.geovision.madre.originale002sync'", s, count=1)
s=re.sub(r'versionCode\s+\d+', 'versionCode 2102', s, count=1)
s=re.sub(r"versionName '[^']+'", "versionName '1.0-madre-originale-002-sync'", s, count=1)
g.write_text(s,encoding='utf-8')
m=root/'app/src/main/AndroidManifest.xml'
x=m.read_text(encoding='utf-8')
x=re.sub(r'android:label="[^"]+"', 'android:label="MADRE 2 SYNC"', x, count=1)
m.write_text(x,encoding='utf-8')
PY

python - <<'PY'
from pathlib import Path
import re
p=Path('android-youtube-test/app/src/main/assets/geovision.html')
s=p.read_text(encoding='utf-8')
blocks=re.findall(r'<script(?:\s+type="module")?[^>]*>([\s\S]*?)</script>',s)
Path('/tmp/gv-m2sync-check.js').write_text('\n'.join(blocks),encoding='utf-8')
PY
node --check /tmp/gv-m2sync-check.js

grep -q 'gv-key-sync-006' "$ROOT/app/src/main/assets/geovision.html"
grep -q 'syncState()' "$ROOT/app/src/main/java/it/geovision/test/MainActivity.java"
grep -q 'SET_ACTIVE_INDEX' "$ROOT/app/src/main/java/it/geovision/test/MainActivity.java"

(cd "$ROOT" && gradle clean assembleDebug)
APK="$ROOT/app/build/outputs/apk/debug/app-debug.apk"
APKSIGNER=$(find "$ANDROID_HOME/build-tools" -type f -name apksigner | sort -V | tail -1)
AAPT=$(find "$ANDROID_HOME/build-tools" -type f -name aapt | sort -V | tail -1)
"$APKSIGNER" verify --print-certs "$APK" | tee /tmp/m2sync-cert.txt
ACT=$(grep -i 'certificate SHA-256 digest:' /tmp/m2sync-cert.txt|head -1|awk '{print $NF}'|tr '[:upper:]' '[:lower:]'|tr -d ':')
test "$ACT" = "$EXPECTED_SIGNER"
"$AAPT" dump badging "$APK" | tee /tmp/m2sync-badging.txt
grep -q "package: name='it.geovision.madre.originale002sync'" /tmp/m2sync-badging.txt
grep -q "application-label:'MADRE 2 SYNC'" /tmp/m2sync-badging.txt
cp "$APK" MADRE_ORIGINALE_2_SYNC.apk
cp "$ROOT/app/src/main/assets/geovision.html" MADRE_ORIGINALE_2_SYNC.html
cat > MANIFEST_MADRE_ORIGINALE_2_SYNC.txt <<EOF
MADRE ORIGINALE 2 SYNC
Base: MADRE ORIGINALE 2.
Unica modifica funzionale: client KeyBox Sync identico a LAB 006 KEY SYNC.
Package isolato: it.geovision.madre.originale002sync
VersionCode: 2102
VersionName: 1.0-madre-originale-002-sync
Firma SHA256: $EXPECTED_SIGNER
Questa build serve al confronto realistico senza sovrascrivere la MADRE ORIGINALE 2 installata.
EOF
zip -j MADRE_ORIGINALE_2_SYNC.zip MADRE_ORIGINALE_2_SYNC.apk MADRE_ORIGINALE_2_SYNC.html MANIFEST_MADRE_ORIGINALE_2_SYNC.txt
sha256sum MADRE_ORIGINALE_2_SYNC.apk MADRE_ORIGINALE_2_SYNC.html MADRE_ORIGINALE_2_SYNC.zip
