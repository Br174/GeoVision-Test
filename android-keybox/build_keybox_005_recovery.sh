#!/usr/bin/env bash
set -euo pipefail

ROOT='android-keybox'
APP="$ROOT/app"
APK="$APP/build/outputs/apk/debug/app-debug.apk"
EXPECTED_SIGNER='716c1a8a139ad956ef8a00f85f153eb0028d109c75b1b938bdf3bb3eb23c22b5'

# Recovery purity checks: only simple vault + export, no global sync machinery.
grep -q "applicationId 'it.geovision.keybox'" "$APP/build.gradle"
grep -q 'versionCode 2005' "$APP/build.gradle"
grep -q "versionName '5.0-recovery-simple'" "$APP/build.gradle"
grep -q 'android:label="KEYBOX 005 RECOVERY"' "$APP/src/main/AndroidManifest.xml"
grep -q 'it.geovision.keybox.EXPORT_KEYS' "$APP/src/main/AndroidManifest.xml"
! grep -q 'SET_ACTIVE_INDEX' "$APP/src/main/AndroidManifest.xml"
! grep -q 'SyncReceiver' "$APP/src/main/AndroidManifest.xml"
! find "$APP/src/main/java" -type f -print0 | xargs -0 grep -q 'active_generation'
! find "$APP/src/main/java" -type f -print0 | xargs -0 grep -q 'switch_total_day'

grep -q 'geovision_keybox_v1' "$APP/src/main/java/it/geovision/keybox/KeyVault.java"
grep -q 'GeoVisionKeyBoxMasterV1' "$APP/src/main/java/it/geovision/keybox/KeyVault.java"
grep -q 'out.putExtra("google1"' "$APP/src/main/java/it/geovision/keybox/ExportKeysActivity.java"
grep -q 'out.putExtra("google2"' "$APP/src/main/java/it/geovision/keybox/ExportKeysActivity.java"
grep -q 'out.putExtra("google3"' "$APP/src/main/java/it/geovision/keybox/ExportKeysActivity.java"
grep -q 'out.putExtra("ai"' "$APP/src/main/java/it/geovision/keybox/ExportKeysActivity.java"
grep -q 'out.putExtra("youtube"' "$APP/src/main/java/it/geovision/keybox/ExportKeysActivity.java"

gradle -p "$ROOT" clean assembleDebug

test -f "$APK"
APKSIGNER=$(find "$ANDROID_HOME/build-tools" -type f -name apksigner | sort -V | tail -1)
AAPT=$(find "$ANDROID_HOME/build-tools" -type f -name aapt | sort -V | tail -1)
"$APKSIGNER" verify --print-certs "$APK" | tee /tmp/keybox005-cert.txt
ACTUAL=$(grep -i 'certificate SHA-256 digest:' /tmp/keybox005-cert.txt | head -1 | awk '{print $NF}' | tr '[:upper:]' '[:lower:]' | tr -d ':')
test "$ACTUAL" = "$EXPECTED_SIGNER"
"$AAPT" dump badging "$APK" | tee /tmp/keybox005-badging.txt
grep -q "package: name='it.geovision.keybox'" /tmp/keybox005-badging.txt
grep -q "versionCode='2005'" /tmp/keybox005-badging.txt
grep -q "application-label:'KEYBOX 005 RECOVERY'" /tmp/keybox005-badging.txt

cp "$APK" GeoVision_KEYBOX_005_RECOVERY.apk
APK_SHA=$(sha256sum GeoVision_KEYBOX_005_RECOVERY.apk | awk '{print $1}')
cat > README_KEYBOX_005_RECOVERY.txt <<EOF
GeoVision KEYBOX 005 RECOVERY SIMPLE

Scopo: test di isolamento del comparto chiavi.
Package: it.geovision.keybox
VersionCode: 2005
VersionName: 5.0-recovery-simple
Firma SHA256: $EXPECTED_SIGNER
APK SHA256: $APK_SHA

Mantiene volutamente:
- SharedPreferences: geovision_keybox_v1
- AndroidKeyStore alias: GeoVisionKeyBoxMasterV1
- le 5 chiavi: Google1, Google2, Google3, AI, YouTube
- azione di esportazione: it.geovision.keybox.EXPORT_KEYS

Rimosso/assente volutamente:
- active index globale
- active generation
- SyncReceiver / SET_ACTIVE_INDEX
- contatori switch
- monitor automatico
- sincronizzazione automatica
- chiamate API automatiche

Installare come AGGIORNAMENTO sopra KEYBOX 004. Non disinstallare prima, per preservare archivio e Keystore.
Dopo l'installazione verificare 5/5 chiavi, poi importarle manualmente nella MADRE ORIGINALE 2 invariata e testare scheda Google, foto, AI e YouTube.
EOF

zip -j GeoVision_KEYBOX_005_RECOVERY.zip GeoVision_KEYBOX_005_RECOVERY.apk README_KEYBOX_005_RECOVERY.txt
sha256sum GeoVision_KEYBOX_005_RECOVERY.apk GeoVision_KEYBOX_005_RECOVERY.zip
