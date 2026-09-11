#!/usr/bin/env bash
set -euo pipefail
ROOT='android-youtube-test'
HOST_SHA='a15e5192709be6dbafb0c5633e4d1ab9dd0cdd6b'
SOURCE_SHA='68dacd3854ff121bdab368c6f591a52d60a538b2e1a92a5545aadfe90ee45b33'
MADRE_HTML_SHA='a9968ed9870cdeeb27613b73f4e2ef5446696d3810e302f0282018583c338807'
MOTHER2_HTML_SHA='42aead77c8cac5c36d3eb9ec7cf81b9efb69f8fd5979ebd52a5e4ca01c28cb9b'
EXPECTED_SIGNER='716c1a8a139ad956ef8a00f85f153eb0028d109c75b1b938bdf3bb3eb23c22b5'

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
test "$(sha256sum /tmp/GeoVision_MADRE_001_SOURCE.html | awk '{print $1}')" = "$MADRE_HTML_SHA"
cp /tmp/GeoVision_MADRE_001_SOURCE.html /tmp/GeoVision_LAB_001_SOURCE.html
python "$ROOT/madre001/patch_candidate_photo_001.py"
test "$(sha256sum /tmp/GeoVision_LAB_001_SOURCE.html | awk '{print $1}')" = "$MOTHER2_HTML_SHA"

git show "$HOST_SHA:$ROOT/app/build.gradle" > "$ROOT/app/build.gradle"
git show "$HOST_SHA:$ROOT/app/src/main/AndroidManifest.xml" > "$ROOT/app/src/main/AndroidManifest.xml"
git show "$HOST_SHA:$ROOT/app/src/main/java/it/geovision/test/MainActivity.java" > "$ROOT/app/src/main/java/it/geovision/test/MainActivity.java"
mkdir -p "$ROOT/app/src/main/assets"
cp /tmp/GeoVision_LAB_001_SOURCE.html "$ROOT/app/src/main/assets/geovision.html"
python "$ROOT/madre001/patch_mainactivity_keybox.py"
python "$ROOT/madre001/patch_social_native_links.py"
python "$ROOT/madre001/patch_key_sync_007_fix.py"

python - <<'PY'
from pathlib import Path
import re
root=Path('android-youtube-test')

g=root/'app/build.gradle'
s=g.read_text(encoding='utf-8')
s=re.sub(r"applicationId '[^']+'", "applicationId 'it.geovision.lab.keysync007fix'", s, count=1)
s=re.sub(r'versionCode\s+\d+', 'versionCode 2007', s, count=1)
s=re.sub(r"versionName '[^']+'", "versionName '1.0-lab-key-sync-007-fix'", s, count=1)
g.write_text(s,encoding='utf-8')

m=root/'app/src/main/AndroidManifest.xml'
x=m.read_text(encoding='utf-8')
needle='    <uses-permission android:name="android.permission.ACCESS_COARSE_LOCATION" />'
extra='''    <uses-permission android:name="android.permission.ACCESS_COARSE_LOCATION" />\n    <uses-permission android:name="it.geovision.permission.KEYBOX_IMPORT" />\n    <queries>\n        <package android:name="it.geovision.keybox" />\n        <package android:name="com.instagram.android" />\n        <package android:name="com.zhiliaoapp.musically" />\n    </queries>'''
if needle not in x: raise SystemExit('manifest permission anchor missing')
x=x.replace(needle,extra,1)
x=re.sub(r'android:label="[^"]+"', 'android:label="LAB 007 KEY SYNC FIX"', x, count=1)
m.write_text(x,encoding='utf-8')

j=root/'app/src/main/java/it/geovision/test/MainActivity.java'
s=j.read_text(encoding='utf-8')
old='''    private class KeyBoxBridge {\n        @JavascriptInterface\n        public void importKeys() {\n            main.post(() -> {\n                Intent intent = new Intent("it.geovision.keybox.EXPORT_KEYS");\n                intent.setPackage("it.geovision.keybox");\n                try {\n                    startActivityForResult(intent, REQ_KEYBOX);\n                } catch (ActivityNotFoundException e) {\n                    notifyKeyBoxError("Installa GeoVision KeyBox");\n                } catch (SecurityException e) {\n                    notifyKeyBoxError("KeyBox non autorizzato: verifica la firma GeoVision");\n                }\n            });\n        }\n    }\n'''
new='''    private class KeyBoxBridge {\n        @JavascriptInterface\n        public void importKeys() {\n            main.post(() -> {\n                Intent intent = new Intent("it.geovision.keybox.EXPORT_KEYS");\n                intent.setPackage("it.geovision.keybox");\n                try { startActivityForResult(intent, REQ_KEYBOX); }\n                catch (ActivityNotFoundException e) { notifyKeyBoxError("Installa GeoVision KeyBox"); }\n                catch (SecurityException e) { notifyKeyBoxError("KeyBox non autorizzato: verifica la firma GeoVision"); }\n            });\n        }\n        @JavascriptInterface\n        public void setActiveIndex(int index) {\n            if (index < 0 || index > 2) return;\n            main.post(() -> {\n                try {\n                    Intent intent = new Intent("it.geovision.keybox.SET_ACTIVE_INDEX");\n                    intent.setPackage("it.geovision.keybox");\n                    intent.putExtra("activeIndex", index);\n                    intent.putExtra("targetPackage", getPackageName());\n                    sendBroadcast(intent, "it.geovision.permission.KEYBOX_IMPORT");\n                } catch (Exception ignored) { }\n            });\n        }\n    }\n'''
if old not in s: raise SystemExit('KeyBoxBridge anchor missing')
s=s.replace(old,new,1)
old_payload='''            keys.put("count", data.getIntExtra("count", 0));\n            final String payload = keys.toString();'''
new_payload='''            keys.put("count", data.getIntExtra("count", 0));\n            keys.put("activeIndex", data.getIntExtra("activeIndex", 0));\n            keys.put("activeGeneration", data.getLongExtra("activeGeneration", 0L));\n            keys.put("switchTotalToday", data.getIntExtra("switchTotalToday", 0));\n            final String payload = keys.toString();'''
if old_payload not in s: raise SystemExit('payload anchor missing')
s=s.replace(old_payload,new_payload,1)
old_eval='''                            "window.gvReceiveKeyBox&&window.gvReceiveKeyBox(" + payload + ")", null);'''
new_eval='''                            "(function(p){if(window.gvApplyKeyBoxState007)window.gvApplyKeyBoxState007(p);if(window.gvReceiveKeyBox)window.gvReceiveKeyBox(p);})(" + payload + ")", null);'''
if old_eval not in s: raise SystemExit('evaluateJavascript anchor missing')
s=s.replace(old_eval,new_eval,1)
j.write_text(s,encoding='utf-8')
PY

# Regression guards: panel/card code still present, old intrusive auto-pull absent.
grep -q 'googleDiagImportKeyBox' "$ROOT/app/src/main/assets/geovision.html"
grep -q 'gvTerritoryPhotos003' "$ROOT/app/src/main/assets/geovision.html"
grep -q 'renderOfficialGoogleCard' "$ROOT/app/src/main/assets/geovision.html"
grep -q 'gv-key-sync-007-fix' "$ROOT/app/src/main/assets/geovision.html"
grep -q 'gvReportGlobalKey007' "$ROOT/app/src/main/assets/geovision.html"
! grep -q 'gvPullGlobalKey006' "$ROOT/app/src/main/assets/geovision.html"
! grep -q 'location.reload(), 250' "$ROOT/app/src/main/assets/geovision.html"
! grep -q 'fallbackGeoCard' "$ROOT/app/src/main/assets/geovision.html"

python - <<'PY'
from pathlib import Path
import re
p=Path('android-youtube-test/app/src/main/assets/geovision.html')
s=p.read_text(encoding='utf-8')
blocks=re.findall(r'<script(?:\s+type="module")?[^>]*>([\s\S]*?)</script>',s)
Path('/tmp/geovision-check.js').write_text('\n'.join(blocks),encoding='utf-8')
PY
node --check /tmp/geovision-check.js

(cd "$ROOT"; gradle clean assembleDebug)
APK="$ROOT/app/build/outputs/apk/debug/app-debug.apk"
APKSIGNER=$(find "$ANDROID_HOME/build-tools" -type f -name apksigner | sort -V | tail -1)
AAPT=$(find "$ANDROID_HOME/build-tools" -type f -name aapt | sort -V | tail -1)
"$APKSIGNER" verify --print-certs "$APK" | tee /tmp/lab007cert.txt
ACTUAL=$(grep -i 'certificate SHA-256 digest:' /tmp/lab007cert.txt | head -1 | awk '{print $NF}' | tr '[:upper:]' '[:lower:]' | tr -d ':')
test "$ACTUAL" = "$EXPECTED_SIGNER"
"$AAPT" dump badging "$APK" | tee /tmp/lab007badging.txt
grep -q "package: name='it.geovision.lab.keysync007fix'" /tmp/lab007badging.txt
grep -q "application-label:'LAB 007 KEY SYNC FIX'" /tmp/lab007badging.txt
cp "$APK" LAB_007_KEY_SYNC_FIX.apk
cp "$ROOT/app/src/main/assets/geovision.html" LAB_007_KEY_SYNC_FIX.html
cat > MANIFEST_LAB_007_KEY_SYNC_FIX.txt <<EOF
LAB 007 KEY SYNC FIX
Base: MADRE ORIGINALE 2.
Package isolato: it.geovision.lab.keysync007fix
Correzione: rimosso il pull automatico KeyBox con startActivityForResult all'avvio/focus che poteva interrompere l'interazione WebView e innescare reload. Mantiene pannello chiavi e Google card originali. La sincronizzazione globale viene applicata quando si usa il KeyBox/import e il failover comunica comunque il nuovo activeIndex al KeyBox.
Firma SHA256: $EXPECTED_SIGNER
EOF
zip -j LAB_007_KEY_SYNC_FIX.zip LAB_007_KEY_SYNC_FIX.apk LAB_007_KEY_SYNC_FIX.html MANIFEST_LAB_007_KEY_SYNC_FIX.txt
