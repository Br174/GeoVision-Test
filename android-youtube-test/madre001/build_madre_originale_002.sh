#!/usr/bin/env bash
set -euo pipefail
ROOT='android-youtube-test'
HOST_SHA='a15e5192709be6dbafb0c5633e4d1ab9dd0cdd6b'
APPROVED_CAND_HTML_SHA='42aead77c8cac5c36d3eb9ec7cf81b9efb69f8fd5979ebd52a5e4ca01c28cb9b'
EXPECTED_SIGNER='716c1a8a139ad956ef8a00f85f153eb0028d109c75b1b938bdf3bb3eb23c22b5'

# 1) Rigenera e verifica ESATTAMENTE CAND 001 FOTO usando il suo build approvato.
bash "$ROOT/madre001/build_candidate_photo_001.sh"
test -f CAND_001_FOTO.html
test "$(sha256sum CAND_001_FOTO.html | awk '{print $1}')" = "$APPROVED_CAND_HTML_SHA"

# 2) Promozione pura: stesso identico HTML della candidata; cambiano solo identita Android e metadati.
git show "$HOST_SHA:$ROOT/app/build.gradle" > "$ROOT/app/build.gradle"
git show "$HOST_SHA:$ROOT/app/src/main/AndroidManifest.xml" > "$ROOT/app/src/main/AndroidManifest.xml"
git show "$HOST_SHA:$ROOT/app/src/main/java/it/geovision/test/MainActivity.java" > "$ROOT/app/src/main/java/it/geovision/test/MainActivity.java"
mkdir -p "$ROOT/app/src/main/assets"
cp CAND_001_FOTO.html "$ROOT/app/src/main/assets/geovision.html"
python "$ROOT/madre001/patch_mainactivity_keybox.py"
python "$ROOT/madre001/patch_social_native_links.py"

python - <<'PY'
from pathlib import Path
import re
root=Path('android-youtube-test')
g=root/'app/build.gradle'
s=g.read_text(encoding='utf-8')
s=re.sub(r"applicationId '[^']+'", "applicationId 'it.geovision.madre.originale002'", s, count=1)
s=re.sub(r'versionCode\s+\d+', 'versionCode 1902', s, count=1)
s=re.sub(r"versionName '[^']+'", "versionName '1.0-madre-originale-002'", s, count=1)
g.write_text(s,encoding='utf-8')

m=root/'app/src/main/AndroidManifest.xml'
x=m.read_text(encoding='utf-8')
needle='    <uses-permission android:name="android.permission.ACCESS_COARSE_LOCATION" />'
extra='''    <uses-permission android:name="android.permission.ACCESS_COARSE_LOCATION" />\n    <uses-permission android:name="it.geovision.permission.KEYBOX_IMPORT" />\n    <queries>\n        <package android:name="it.geovision.keybox" />\n        <package android:name="com.instagram.android" />\n        <package android:name="com.zhiliaoapp.musically" />\n    </queries>'''
if needle not in x:
    raise SystemExit('manifest permission anchor missing')
x=x.replace(needle,extra,1)
x=re.sub(r'android:label="[^"]+"', 'android:label="MADRE ORIGINALE 2"', x, count=1)
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

test "$(sha256sum "$ROOT/app/src/main/assets/geovision.html" | awk '{print $1}')" = "$APPROVED_CAND_HTML_SHA"
cmp -s CAND_001_FOTO.html "$ROOT/app/src/main/assets/geovision.html"

(
  cd "$ROOT"
  gradle clean assembleDebug
)

APK="$ROOT/app/build/outputs/apk/debug/app-debug.apk"
APKSIGNER=$(find "$ANDROID_HOME/build-tools" -type f -name apksigner | sort -V | tail -1)
AAPT=$(find "$ANDROID_HOME/build-tools" -type f -name aapt | sort -V | tail -1)
"$APKSIGNER" verify --print-certs "$APK" | tee /tmp/madre-originale-002-signer.txt
ACTUAL=$(grep -i 'certificate SHA-256 digest:' /tmp/madre-originale-002-signer.txt | head -1 | awk '{print $NF}' | tr '[:upper:]' '[:lower:]' | tr -d ':')
test "$ACTUAL" = "$EXPECTED_SIGNER"
"$AAPT" dump badging "$APK" | tee /tmp/madre-originale-002-badging.txt
grep -q "package: name='it.geovision.madre.originale002'" /tmp/madre-originale-002-badging.txt
grep -q "application-label:'MADRE ORIGINALE 2'" /tmp/madre-originale-002-badging.txt
unzip -p "$APK" assets/geovision.html > /tmp/packaged.html
test "$(sha256sum /tmp/packaged.html | awk '{print $1}')" = "$APPROVED_CAND_HTML_SHA"
cmp -s CAND_001_FOTO.html /tmp/packaged.html

cp "$APK" MADRE_ORIGINALE_2.apk
cp CAND_001_FOTO.html MADRE_ORIGINALE_2.html
APK_SHA=$(sha256sum MADRE_ORIGINALE_2.apk | awk '{print $1}')
cat > MANIFEST_MADRE_ORIGINALE_2.txt <<EOF
MADRE ORIGINALE 2
Origine diretta: CAND 001 FOTO.
Promozione pura della candidata: nessun metodo reimplementato e nessuna modifica funzionale.
Differenze rispetto a CAND 001 FOTO: soltanto nome app, famiglia/package Android e metadati versione.
HTML candidata SHA256: $APPROVED_CAND_HTML_SHA
HTML MADRE ORIGINALE 2 SHA256: $(sha256sum MADRE_ORIGINALE_2.html | awk '{print $1}')
Verifica identita HTML: cmp esatto superato.
Package/famiglia Android separata: it.geovision.madre.originale002
VersionCode: 1902
VersionName: 1.0-madre-originale-002
Firma SHA256: $EXPECTED_SIGNER
APK SHA256: $APK_SHA
Nota: questa build NON corregge il problema di stabilita foto emerso dopo il test; serve come riferimento fedele della CAND 001 FOTO. Il problema foto verra' studiato in LAB separata.
EOF
zip -j MADRE_ORIGINALE_2.zip MADRE_ORIGINALE_2.apk MADRE_ORIGINALE_2.html MANIFEST_MADRE_ORIGINALE_2.txt
sha256sum MADRE_ORIGINALE_2.apk MADRE_ORIGINALE_2.html MADRE_ORIGINALE_2.zip
