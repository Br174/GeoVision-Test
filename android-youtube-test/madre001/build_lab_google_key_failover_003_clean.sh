#!/usr/bin/env bash
set -euo pipefail
ROOT='android-youtube-test'
EXPECTED_SIGNER='716c1a8a139ad956ef8a00f85f153eb0028d109c75b1b938bdf3bb3eb23c22b5'

# Ricostruisce da zero la CANDIDATA 003 nota come funzionante.
bash "$ROOT/madre001/build_candidate003_keybox_v2.sh"

# Applica SOLO il failover nel catch della diagnostica.
python "$ROOT/madre001/patch_google_key_failover_diag_only.py"
cp /tmp/GeoVision_MADRE_001_SOURCE.html "$ROOT/app/src/main/assets/geovision.html"

python - <<'PY'
from pathlib import Path
import re
root=Path('android-youtube-test')
g=root/'app/build.gradle'
s=g.read_text(encoding='utf-8')
s=re.sub(r"applicationId '[^']+'", "applicationId 'it.geovision.lab.googlekeys003'", s, count=1)
s=re.sub(r'versionCode\s+\d+', 'versionCode 1403', s, count=1)
s=re.sub(r"versionName '[^']+'", "versionName '1.0-lab-google-key-failover-003-clean'", s, count=1)
g.write_text(s,encoding='utf-8')

m=root/'app/src/main/AndroidManifest.xml'
x=m.read_text(encoding='utf-8')
x=re.sub(r'android:label="[^"]+"', 'android:label="GeoVision LAB KEY 003"', x, count=1)
m.write_text(x,encoding='utf-8')
PY

# Controlli mirati: niente hook globali, niente fallback grafico, pannello presente.
grep -q 'googleDiagImportKeyBox' /tmp/GeoVision_MADRE_001_SOURCE.html
grep -q 'gvDiagAdvanceGoogleKey' /tmp/GeoVision_MADRE_001_SOURCE.html
grep -q 'RESOURCE_EXHAUSTED' /tmp/GeoVision_MADRE_001_SOURCE.html
! grep -q 'gvInstallGoogleKeyFailoverHooks' /tmp/GeoVision_MADRE_001_SOURCE.html
! grep -q 'gm_authFailure' /tmp/GeoVision_MADRE_001_SOURCE.html
! grep -q 'fallbackGeoCard' /tmp/GeoVision_MADRE_001_SOURCE.html
! grep -q 'Scheda GeoVision' /tmp/GeoVision_MADRE_001_SOURCE.html
grep -q 'id="voice"' /tmp/GeoVision_MADRE_001_SOURCE.html
grep -q 'id="sheetPhotosVisual"' /tmp/GeoVision_MADRE_001_SOURCE.html
grep -q 'gmp-place-details' /tmp/GeoVision_MADRE_001_SOURCE.html

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
"$APKSIGNER" verify --print-certs "$APK" | tee /tmp/lab003-signer.txt
ACTUAL=$(grep -i 'certificate SHA-256 digest:' /tmp/lab003-signer.txt | head -1 | awk '{print $NF}' | tr '[:upper:]' '[:lower:]' | tr -d ':')
test "$ACTUAL" = "$EXPECTED_SIGNER"
"$AAPT" dump badging "$APK" | tee /tmp/lab003-badging.txt
grep -q "package: name='it.geovision.lab.googlekeys003'" /tmp/lab003-badging.txt
grep -q "application-label:'GeoVision LAB KEY 003'" /tmp/lab003-badging.txt

unzip -p "$APK" assets/geovision.html > /tmp/lab003-packaged.html
grep -q 'gvDiagAdvanceGoogleKey' /tmp/lab003-packaged.html
grep -q 'googleDiagImportKeyBox' /tmp/lab003-packaged.html
! grep -q 'gvInstallGoogleKeyFailoverHooks' /tmp/lab003-packaged.html
! grep -q 'fallbackGeoCard' /tmp/lab003-packaged.html

cp "$APK" GeoVision_LAB_KEY_FAILOVER_003_CLEAN.apk
cp /tmp/GeoVision_MADRE_001_SOURCE.html GeoVision_LAB_KEY_FAILOVER_003_CLEAN.html
LAB_SHA=$(sha256sum GeoVision_LAB_KEY_FAILOVER_003_CLEAN.apk | awk '{print $1}')
HTML_SHA=$(sha256sum GeoVision_LAB_KEY_FAILOVER_003_CLEAN.html | awk '{print $1}')
cat > MANIFEST_LAB_KEY_FAILOVER_003_CLEAN.txt <<EOF
GeoVision LAB KEY FAILOVER 003 CLEAN
Base ricostruita: CANDIDATA 003 KeyBox Import funzionante
Package isolato: it.geovision.lab.googlekeys003
Unica modifica funzionale: failover Google SOLO nel catch della Ricerca Places in diagnostica.
Nessun hook globale Google. Nessuna modifica ai listener/pulsanti/interfaccia.
Fallback grafico GeoVision: assente.
Pulsanti testata, KeyBox, audioguida e scheda Google ufficiale: preservati.
Firma SHA256: $EXPECTED_SIGNER
HTML SHA256: $HTML_SHA
APK SHA256: $LAB_SHA
EOF
zip -j GeoVision_LAB_KEY_FAILOVER_003_CLEAN.zip \
  GeoVision_LAB_KEY_FAILOVER_003_CLEAN.apk \
  GeoVision_LAB_KEY_FAILOVER_003_CLEAN.html \
  MANIFEST_LAB_KEY_FAILOVER_003_CLEAN.txt
sha256sum GeoVision_LAB_KEY_FAILOVER_003_CLEAN.apk GeoVision_LAB_KEY_FAILOVER_003_CLEAN.zip
