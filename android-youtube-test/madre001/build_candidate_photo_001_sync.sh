#!/usr/bin/env bash
set -euo pipefail
ROOT='android-youtube-test'
EXPECTED_SIGNER='716c1a8a139ad956ef8a00f85f153eb0028d109c75b1b938bdf3bb3eb23c22b5'

bash "$ROOT/madre001/build_candidate_photo_001.sh"
python "$ROOT/madre001/patch_key_sync_006.py"
python "$ROOT/madre001/patch_android_key_sync_006.py"

python - <<'PY'
from pathlib import Path
import re
root=Path('android-youtube-test')
g=root/'app/build.gradle'
s=g.read_text(encoding='utf-8')
s=re.sub(r"applicationId '[^']+'", "applicationId 'it.geovision.cand.photo001sync'", s, count=1)
s=re.sub(r'versionCode\s+\d+', 'versionCode 2101', s, count=1)
s=re.sub(r"versionName '[^']+'", "versionName '1.0-cand-photo-001-sync'", s, count=1)
g.write_text(s,encoding='utf-8')
m=root/'app/src/main/AndroidManifest.xml'
x=m.read_text(encoding='utf-8')
x=re.sub(r'android:label="[^"]+"', 'android:label="CAND 001 FOTO SYNC"', x, count=1)
m.write_text(x,encoding='utf-8')
PY

python - <<'PY'
from pathlib import Path
import re
p=Path('android-youtube-test/app/src/main/assets/geovision.html')
s=p.read_text(encoding='utf-8')
blocks=re.findall(r'<script(?:\s+type="module")?[^>]*>([\s\S]*?)</script>',s)
Path('/tmp/gv-c1sync-check.js').write_text('\n'.join(blocks),encoding='utf-8')
PY
node --check /tmp/gv-c1sync-check.js

grep -q 'gv-key-sync-006' "$ROOT/app/src/main/assets/geovision.html"
grep -q 'syncState()' "$ROOT/app/src/main/java/it/geovision/test/MainActivity.java"
grep -q 'SET_ACTIVE_INDEX' "$ROOT/app/src/main/java/it/geovision/test/MainActivity.java"

(cd "$ROOT" && gradle clean assembleDebug)
APK="$ROOT/app/build/outputs/apk/debug/app-debug.apk"
APKSIGNER=$(find "$ANDROID_HOME/build-tools" -type f -name apksigner | sort -V | tail -1)
AAPT=$(find "$ANDROID_HOME/build-tools" -type f -name aapt | sort -V | tail -1)
"$APKSIGNER" verify --print-certs "$APK" | tee /tmp/c1sync-cert.txt
ACT=$(grep -i 'certificate SHA-256 digest:' /tmp/c1sync-cert.txt|head -1|awk '{print $NF}'|tr '[:upper:]' '[:lower:]'|tr -d ':')
test "$ACT" = "$EXPECTED_SIGNER"
"$AAPT" dump badging "$APK" | tee /tmp/c1sync-badging.txt
grep -q "package: name='it.geovision.cand.photo001sync'" /tmp/c1sync-badging.txt
grep -q "application-label:'CAND 001 FOTO SYNC'" /tmp/c1sync-badging.txt
cp "$APK" CAND_001_FOTO_SYNC.apk
cp "$ROOT/app/src/main/assets/geovision.html" CAND_001_FOTO_SYNC.html
cat > MANIFEST_CAND_001_FOTO_SYNC.txt <<EOF
CAND 001 FOTO SYNC
Base: CAND 001 FOTO.
Unica modifica funzionale: client KeyBox Sync identico a LAB 006 KEY SYNC.
Package isolato: it.geovision.cand.photo001sync
VersionCode: 2101
VersionName: 1.0-cand-photo-001-sync
Firma SHA256: $EXPECTED_SIGNER
Questa build serve al confronto realistico senza sovrascrivere la CAND 001 FOTO installata.
EOF
zip -j CAND_001_FOTO_SYNC.zip CAND_001_FOTO_SYNC.apk CAND_001_FOTO_SYNC.html MANIFEST_CAND_001_FOTO_SYNC.txt
sha256sum CAND_001_FOTO_SYNC.apk CAND_001_FOTO_SYNC.html CAND_001_FOTO_SYNC.zip
