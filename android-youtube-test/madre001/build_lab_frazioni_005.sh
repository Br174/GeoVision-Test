#!/usr/bin/env bash
set -euo pipefail
ROOT='android-youtube-test'
HOST_SHA='a15e5192709be6dbafb0c5633e4d1ab9dd0cdd6b'
MADRE2_HTML_SHA='42aead77c8cac5c36d3eb9ec7cf81b9efb69f8fd5979ebd52a5e4ca01c28cb9b'
EXPECTED_SIGNER='716c1a8a139ad956ef8a00f85f153eb0028d109c75b1b938bdf3bb3eb23c22b5'

# Base pulita: MADRE ORIGINALE 2.
bash "$ROOT/madre001/build_madre_originale_002.sh"
test -f MADRE_ORIGINALE_2.html
test "$(sha256sum MADRE_ORIGINALE_2.html | awk '{print $1}')" = "$MADRE2_HTML_SHA"
cp MADRE_ORIGINALE_2.html /tmp/GeoVision_LAB_005_SOURCE.html

# Applica solo il metodo FRAZIONI/gerarchia territoriale della LAB 005.
python "$ROOT/madre001/patch_frazioni_005.py"

grep -q 'gvFineCandidate005' /tmp/GeoVision_LAB_005_SOURCE.html
grep -q 'gvExactArea005' /tmp/GeoVision_LAB_005_SOURCE.html
grep -q "Identifico città, paese o frazione" /tmp/GeoVision_LAB_005_SOURCE.html
grep -q 'z>=16' /tmp/GeoVision_LAB_005_SOURCE.html
grep -q 'gvTerritoryPhotos003' /tmp/GeoVision_LAB_005_SOURCE.html
! grep -q 'gvLocalityPrecision004' /tmp/GeoVision_LAB_005_SOURCE.html
! grep -q 'fallbackGeoCard' /tmp/GeoVision_LAB_005_SOURCE.html

# Ricostruisce host Android stabile con famiglia separata.
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
s=re.sub(r"applicationId '[^']+'", "applicationId 'it.geovision.lab.frazioni005'", s, count=1)
s=re.sub(r'versionCode\s+\d+', 'versionCode 2005', s, count=1)
s=re.sub(r"versionName '[^']+'", "versionName '1.0-lab-frazioni-005'", s, count=1)
g.write_text(s,encoding='utf-8')

m=root/'app/src/main/AndroidManifest.xml'
x=m.read_text(encoding='utf-8')
needle='    <uses-permission android:name="android.permission.ACCESS_COARSE_LOCATION" />'
extra='''    <uses-permission android:name="android.permission.ACCESS_COARSE_LOCATION" />\n    <uses-permission android:name="it.geovision.permission.KEYBOX_IMPORT" />\n    <queries>\n        <package android:name="it.geovision.keybox" />\n        <package android:name="com.instagram.android" />\n        <package android:name="com.zhiliaoapp.musically" />\n    </queries>'''
if needle not in x: raise SystemExit('manifest permission anchor missing')
x=x.replace(needle,extra,1)
x=re.sub(r'android:label="[^"]+"', 'android:label="LAB 005 FRAZIONI"', x, count=1)
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
"$APKSIGNER" verify --print-certs "$APK" | tee /tmp/lab005-signer.txt
ACTUAL=$(grep -i 'certificate SHA-256 digest:' /tmp/lab005-signer.txt | head -1 | awk '{print $NF}' | tr '[:upper:]' '[:lower:]' | tr -d ':')
test "$ACTUAL" = "$EXPECTED_SIGNER"
"$AAPT" dump badging "$APK" | tee /tmp/lab005-badging.txt
grep -q "package: name='it.geovision.lab.frazioni005'" /tmp/lab005-badging.txt
grep -q "application-label:'LAB 005 FRAZIONI'" /tmp/lab005-badging.txt
unzip -p "$APK" assets/geovision.html > /tmp/packaged.html
grep -q 'gvFineCandidate005' /tmp/packaged.html
grep -q 'gvTerritoryPhotos003' /tmp/packaged.html
! grep -q 'gvLocalityPrecision004' /tmp/packaged.html

cp "$APK" LAB_005_FRAZIONI.apk
cp /tmp/GeoVision_LAB_005_SOURCE.html LAB_005_FRAZIONI.html
LAB_HTML_SHA=$(sha256sum LAB_005_FRAZIONI.html | awk '{print $1}')
APK_SHA=$(sha256sum LAB_005_FRAZIONI.apk | awk '{print $1}')
cat > MANIFEST_LAB_005_FRAZIONI.txt <<EOF
LAB 005 FRAZIONI
Base: MADRE ORIGINALE 2 pulita.
Scopo: ripristinare il livello territoriale intermedio fra Comune e POI (frazioni, rioni, contrade, quartieri, localita).
Casi test prioritari: Ogliara (Salerno), Montoro Superiore e altre frazioni/localita.
Metodo FOTO della MADRE 2 preservato.
Famiglia Android separata: it.geovision.lab.frazioni005
VersionCode: 2005
VersionName: 1.0-lab-frazioni-005
Firma SHA256: $EXPECTED_SIGNER
HTML MADRE 2 SHA256: $MADRE2_HTML_SHA
HTML LAB 005 SHA256: $LAB_HTML_SHA
APK SHA256: $APK_SHA
Questa e' una LAB sperimentale. Se approvata, la futura candidata dovra' essere creata DA METODO, NON DA CONVERSIONE DELLA LAB, partendo dalla MADRE ORIGINALE 2, con famiglia Android separata.
EOF
zip -j LAB_005_FRAZIONI.zip LAB_005_FRAZIONI.apk LAB_005_FRAZIONI.html MANIFEST_LAB_005_FRAZIONI.txt
sha256sum LAB_005_FRAZIONI.apk LAB_005_FRAZIONI.html LAB_005_FRAZIONI.zip
