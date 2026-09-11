#!/usr/bin/env bash
set -euo pipefail
ROOT='android-youtube-test'
HOST_SHA='a15e5192709be6dbafb0c5633e4d1ab9dd0cdd6b'
SOURCE_SHA='68dacd3854ff121bdab368c6f591a52d60a538b2e1a92a5545aadfe90ee45b33'
MADRE_HTML_SHA='a9968ed9870cdeeb27613b73f4e2ef5446696d3810e302f0282018583c338807'
MOTHER2_HTML_SHA='42aead77c8cac5c36d3eb9ec7cf81b9efb69f8fd5979ebd52a5e4ca01c28cb9b'
EXPECTED_SIGNER='716c1a8a139ad956ef8a00f85f153eb0028d109c75b1b938bdf3bb3eb23c22b5'

# BASE LAB rapida: rigenera una sola volta il codice funzionale identico alla MADRE ORIGINALE 2.
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

# Host Android pulito + stesso HTML della Madre 2.
git show "$HOST_SHA:$ROOT/app/build.gradle" > "$ROOT/app/build.gradle"
git show "$HOST_SHA:$ROOT/app/src/main/AndroidManifest.xml" > "$ROOT/app/src/main/AndroidManifest.xml"
git show "$HOST_SHA:$ROOT/app/src/main/java/it/geovision/test/MainActivity.java" > "$ROOT/app/src/main/java/it/geovision/test/MainActivity.java"
mkdir -p "$ROOT/app/src/main/assets"
cp /tmp/GeoVision_LAB_001_SOURCE.html "$ROOT/app/src/main/assets/geovision.html"
python "$ROOT/madre001/patch_mainactivity_keybox.py"
python "$ROOT/madre001/patch_social_native_links.py"

# Unica modifica funzionale della LAB: client KEY SYNC 006.
python "$ROOT/madre001/patch_key_sync_006.py"

python - <<'PY'
from pathlib import Path
import re
root=Path('android-youtube-test')

# Identita Android isolata della LAB.
g=root/'app/build.gradle'
s=g.read_text(encoding='utf-8')
s=re.sub(r"applicationId '[^']+'", "applicationId 'it.geovision.lab.keysync006'", s, count=1)
s=re.sub(r'versionCode\s+\d+', 'versionCode 2006', s, count=1)
s=re.sub(r"versionName '[^']+'", "versionName '1.0-lab-key-sync-006'", s, count=1)
g.write_text(s,encoding='utf-8')

m=root/'app/src/main/AndroidManifest.xml'
x=m.read_text(encoding='utf-8')
needle='    <uses-permission android:name="android.permission.ACCESS_COARSE_LOCATION" />'
extra='''    <uses-permission android:name="android.permission.ACCESS_COARSE_LOCATION" />\n    <uses-permission android:name="it.geovision.permission.KEYBOX_IMPORT" />\n    <queries>\n        <package android:name="it.geovision.keybox" />\n        <package android:name="com.instagram.android" />\n        <package android:name="com.zhiliaoapp.musically" />\n    </queries>'''
if needle not in x: raise SystemExit('manifest permission anchor missing')
x=x.replace(needle,extra,1)
x=re.sub(r'android:label="[^"]+"', 'android:label="LAB 006 KEY SYNC"', x, count=1)
m.write_text(x,encoding='utf-8')

# Estende il bridge KeyBox senza toccare TTS/social/card.
j=root/'app/src/main/java/it/geovision/test/MainActivity.java'
s=j.read_text(encoding='utf-8')
old='''    private class KeyBoxBridge {\n        @JavascriptInterface\n        public void importKeys() {\n            main.post(() -> {\n                Intent intent = new Intent("it.geovision.keybox.EXPORT_KEYS");\n                intent.setPackage("it.geovision.keybox");\n                try {\n                    startActivityForResult(intent, REQ_KEYBOX);\n                } catch (ActivityNotFoundException e) {\n                    notifyKeyBoxError("Installa GeoVision KeyBox");\n                } catch (SecurityException e) {\n                    notifyKeyBoxError("KeyBox non autorizzato: verifica la firma GeoVision");\n                }\n            });\n        }\n    }\n'''
new='''    private class KeyBoxBridge {\n        private void requestState() {\n            main.post(() -> {\n                Intent intent = new Intent("it.geovision.keybox.EXPORT_KEYS");\n                intent.setPackage("it.geovision.keybox");\n                try {\n                    startActivityForResult(intent, REQ_KEYBOX);\n                } catch (ActivityNotFoundException e) {\n                    notifyKeyBoxError("Installa GeoVision KeyBox");\n                } catch (SecurityException e) {\n                    notifyKeyBoxError("KeyBox non autorizzato: verifica la firma GeoVision");\n                }\n            });\n        }\n        @JavascriptInterface public void importKeys() { requestState(); }\n        @JavascriptInterface public void syncState() { requestState(); }\n        @JavascriptInterface public void setActiveIndex(int index) {\n            if (index < 0 || index > 2) return;\n            main.post(() -> {\n                try {\n                    Intent intent = new Intent("it.geovision.keybox.SET_ACTIVE_INDEX");\n                    intent.setPackage("it.geovision.keybox");\n                    intent.putExtra("activeIndex", index);\n                    intent.putExtra("targetPackage", getPackageName());\n                    sendBroadcast(intent, "it.geovision.permission.KEYBOX_IMPORT");\n                } catch (Exception ignored) { }\n            });\n        }\n    }\n'''
if old not in s: raise SystemExit('KeyBoxBridge anchor missing')
s=s.replace(old,new,1)

old_payload='''            keys.put("count", data.getIntExtra("count", 0));\n            final String payload = keys.toString();'''
new_payload='''            keys.put("count", data.getIntExtra("count", 0));\n            keys.put("activeIndex", data.getIntExtra("activeIndex", 0));\n            keys.put("activeGeneration", data.getLongExtra("activeGeneration", 0L));\n            keys.put("switchTotalToday", data.getIntExtra("switchTotalToday", 0));\n            keys.put("switchKey1Today", data.getIntExtra("switchKey1Today", 0));\n            keys.put("switchKey2Today", data.getIntExtra("switchKey2Today", 0));\n            keys.put("switchKey3Today", data.getIntExtra("switchKey3Today", 0));\n            final String payload = keys.toString();'''
if old_payload not in s: raise SystemExit('payload anchor missing')
s=s.replace(old_payload,new_payload,1)

old_eval='''                            "window.gvReceiveKeyBox&&window.gvReceiveKeyBox(" + payload + ")", null);'''
new_eval='''                            "(function(p){if(window.gvReceiveKeyBoxSync)window.gvReceiveKeyBoxSync(p);if(window.gvReceiveKeyBox)window.gvReceiveKeyBox(p);})(" + payload + ")", null);'''
if old_eval not in s: raise SystemExit('evaluateJavascript anchor missing')
s=s.replace(old_eval,new_eval,1)
j.write_text(s,encoding='utf-8')
PY

# Controlli: Madre 2 intatta come base + solo KEY SYNC aggiunto.
grep -q 'gvTerritoryPhotos003' "$ROOT/app/src/main/assets/geovision.html"
grep -q 'gvResolveGeoPlace003' "$ROOT/app/src/main/assets/geovision.html"
grep -q 'gv-key-sync-006' "$ROOT/app/src/main/assets/geovision.html"
grep -q 'gvReportGlobalKey006' "$ROOT/app/src/main/assets/geovision.html"
grep -q 'syncState()' "$ROOT/app/src/main/java/it/geovision/test/MainActivity.java"
grep -q 'SET_ACTIVE_INDEX' "$ROOT/app/src/main/java/it/geovision/test/MainActivity.java"
! grep -q 'gvLocalityPrecision004' "$ROOT/app/src/main/assets/geovision.html"
! grep -q 'fallbackGeoCard' "$ROOT/app/src/main/assets/geovision.html"

python - <<'PY'
from pathlib import Path
import re
p=Path('android-youtube-test/app/src/main/assets/geovision.html')
s=p.read_text(encoding='utf-8')
blocks=re.findall(r'<script(?:\s+type="module")?[^>]*>([\s\S]*?)</script>',s)
Path('/tmp/geovision-check.js').write_text('\n'.join(blocks),encoding='utf-8')
print('LAB006 HTML bytes:',p.stat().st_size,'script blocks:',len(blocks))
PY
node --check /tmp/geovision-check.js

(
  cd "$ROOT"
  gradle clean assembleDebug
)

APK="$ROOT/app/build/outputs/apk/debug/app-debug.apk"
APKSIGNER=$(find "$ANDROID_HOME/build-tools" -type f -name apksigner | sort -V | tail -1)
AAPT=$(find "$ANDROID_HOME/build-tools" -type f -name aapt | sort -V | tail -1)
"$APKSIGNER" verify --print-certs "$APK" | tee /tmp/lab006-signer.txt
ACTUAL=$(grep -i 'certificate SHA-256 digest:' /tmp/lab006-signer.txt | head -1 | awk '{print $NF}' | tr '[:upper:]' '[:lower:]' | tr -d ':')
test "$ACTUAL" = "$EXPECTED_SIGNER"
"$AAPT" dump badging "$APK" | tee /tmp/lab006-badging.txt
grep -q "package: name='it.geovision.lab.keysync006'" /tmp/lab006-badging.txt
grep -q "application-label:'LAB 006 KEY SYNC'" /tmp/lab006-badging.txt

cp "$APK" LAB_006_KEY_SYNC.apk
cp "$ROOT/app/src/main/assets/geovision.html" LAB_006_KEY_SYNC.html
BASE_SHA=$(sha256sum /tmp/GeoVision_LAB_001_SOURCE.html | awk '{print $1}')
HTML_SHA=$(sha256sum LAB_006_KEY_SYNC.html | awk '{print $1}')
APK_SHA=$(sha256sum LAB_006_KEY_SYNC.apk | awk '{print $1}')
cat > MANIFEST_LAB_006_KEY_SYNC.txt <<EOF
LAB 006 KEY SYNC
Base funzionale: MADRE ORIGINALE 2, HTML base SHA256 $BASE_SHA.
Famiglia Android separata: it.geovision.lab.keysync006
Unica modifica funzionale: client di sincronizzazione KeyBox globale.
Comportamento: all'avvio/ritorno in primo piano legge activeIndex dal KeyBox; quando il failover sceglie una nuova chiave comunica l'indice al KeyBox.
Compatibile con KEYBOX 003 MONITOR: activeIndex, activeGeneration e contatori giornalieri.
Non contiene patch FRAZIONI della LAB 005.
HTML LAB SHA256: $HTML_SHA
APK SHA256: $APK_SHA
Firma SHA256: $EXPECTED_SIGNER
EOF
zip -j LAB_006_KEY_SYNC.zip LAB_006_KEY_SYNC.apk LAB_006_KEY_SYNC.html MANIFEST_LAB_006_KEY_SYNC.txt
sha256sum LAB_006_KEY_SYNC.apk LAB_006_KEY_SYNC.html LAB_006_KEY_SYNC.zip
