#!/usr/bin/env bash
set -euo pipefail
ROOT='android-youtube-test'
HOST_SHA='a15e5192709be6dbafb0c5633e4d1ab9dd0cdd6b'
BASE_HTML_SHA='42aead77c8cac5c36d3eb9ec7cf81b9efb69f8fd5979ebd52a5e4ca01c28cb9b'
EXPECTED_SIGNER='716c1a8a139ad956ef8a00f85f153eb0028d109c75b1b938bdf3bb3eb23c22b5'

bash "$ROOT/madre001/build_candidate_photo_001.sh"
test -f CAND_001_FOTO.html
test "$(sha256sum CAND_001_FOTO.html | awk '{print $1}')" = "$BASE_HTML_SHA"
cp CAND_001_FOTO.html /tmp/GeoVision_MADRE_001_SOURCE.html
python "$ROOT/madre001/patch_key_panel_monitor_008.py"
PATCHED_SHA=$(sha256sum /tmp/GeoVision_MADRE_001_SOURCE.html | awk '{print $1}')

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
s=re.sub(r"applicationId '[^']+'", "applicationId 'it.geovision.lab.keypanel008'", s, count=1)
s=re.sub(r'versionCode\s+\d+', 'versionCode 2008', s, count=1)
s=re.sub(r"versionName '[^']+'", "versionName '1.0-lab-key-panel-monitor-008'", s, count=1)
g.write_text(s,encoding='utf-8')

m=root/'app/src/main/AndroidManifest.xml'
x=m.read_text(encoding='utf-8')
needle='    <uses-permission android:name="android.permission.ACCESS_COARSE_LOCATION" />'
extra='''    <uses-permission android:name="android.permission.ACCESS_COARSE_LOCATION" />\n    <uses-permission android:name="it.geovision.permission.KEYBOX_IMPORT" />\n    <queries>\n        <package android:name="it.geovision.keybox" />\n        <package android:name="com.instagram.android" />\n        <package android:name="com.zhiliaoapp.musically" />\n    </queries>'''
if needle in x:x=x.replace(needle,extra,1)
x=re.sub(r'android:label="[^"]+"', 'android:label="LAB 008 KEY PANEL"', x, count=1)
m.write_text(x,encoding='utf-8')
PY

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
"$APKSIGNER" verify --print-certs "$APK" | tee /tmp/lab008cert.txt
ACT=$(grep -i 'certificate SHA-256 digest:' /tmp/lab008cert.txt|head -1|awk '{print $NF}'|tr '[:upper:]' '[:lower:]'|tr -d ':')
test "$ACT" = "$EXPECTED_SIGNER"
"$AAPT" dump badging "$APK" | tee /tmp/lab008badging.txt
grep -q "package: name='it.geovision.lab.keypanel008'" /tmp/lab008badging.txt
grep -q "application-label:'LAB 008 KEY PANEL'" /tmp/lab008badging.txt
unzip -p "$APK" assets/geovision.html > /tmp/packaged.html
test "$(sha256sum /tmp/packaged.html | awk '{print $1}')" = "$PATCHED_SHA"

cp "$APK" LAB_008_KEY_PANEL.apk
cp /tmp/GeoVision_MADRE_001_SOURCE.html LAB_008_KEY_PANEL.html
APK_SHA=$(sha256sum LAB_008_KEY_PANEL.apk | awk '{print $1}')
cat > MANIFEST_LAB_008_KEY_PANEL.txt <<EOF
GeoVision LAB 008 KEY PANEL
Base funzionale: MADRE ORIGINALE 2 / CAND 001 FOTO HTML $BASE_HTML_SHA
Modifica: pannello chiavi interno graficamente stile KeyBox Monitor, senza cambiare scheda Google o logica operativa esistente.
AI: pallino verde solo dopo test reale Gemini riuscito; rosso su assenza/errore/rete.
YouTube: pallino verde solo dopo test reale YouTube Data API riuscito; rosso su assenza/errore/rete.
Google 1/2/3: verde solo chiave selezionata attiva; rosso le altre/assenti. Nessun nuovo sync automatico o reload automatico.
Package isolato: it.geovision.lab.keypanel008
VersionCode: 2008
VersionName: 1.0-lab-key-panel-monitor-008
HTML patched SHA256: $PATCHED_SHA
APK SHA256: $APK_SHA
Firma SHA256: $EXPECTED_SIGNER
EOF
zip -j LAB_008_KEY_PANEL.zip LAB_008_KEY_PANEL.apk LAB_008_KEY_PANEL.html MANIFEST_LAB_008_KEY_PANEL.txt
sha256sum LAB_008_KEY_PANEL.apk LAB_008_KEY_PANEL.html LAB_008_KEY_PANEL.zip
