#!/usr/bin/env bash
set -euo pipefail
ROOT='android-keybox'
APP="$ROOT/app"
JAVA="$APP/src/main/java/it/geovision/keybox"
EXPECTED='716c1a8a139ad956ef8a00f85f153eb0028d109c75b1b938bdf3bb3eb23c22b5'
mkdir -p "$JAVA"
cat > "$APP/build.gradle" <<'EOF'
plugins { id 'com.android.application' }
android {
  namespace 'it.geovision.keybox'; compileSdk 35
  signingConfigs { stableDebug { storeFile file('../../android-youtube-test/signing/geovision-debug-stable.keystore'); storePassword 'android'; keyAlias 'androiddebugkey'; keyPassword 'android' } }
  defaultConfig { applicationId 'it.geovision.keybox'; minSdk 23; targetSdk 35; versionCode 2006; versionName '6.0-sync-safe' }
  buildTypes { debug { signingConfig signingConfigs.stableDebug } }
}
EOF
cat > "$APP/src/main/AndroidManifest.xml" <<'EOF'
<manifest xmlns:android="http://schemas.android.com/apk/res/android">
  <permission android:name="it.geovision.permission.KEYBOX_IMPORT" android:protectionLevel="signature"/>
  <application android:allowBackup="false" android:label="KEYBOX 006 SYNC SAFE" android:theme="@style/AppTheme">
    <activity android:name=".MainActivity" android:exported="true"><intent-filter><action android:name="android.intent.action.MAIN"/><category android:name="android.intent.category.LAUNCHER"/></intent-filter></activity>
    <activity android:name=".ExportKeysActivity" android:exported="true" android:permission="it.geovision.permission.KEYBOX_IMPORT" android:theme="@style/Theme.Transparent"><intent-filter><action android:name="it.geovision.keybox.EXPORT_KEYS"/><category android:name="android.intent.category.DEFAULT"/></intent-filter></activity>
    <receiver android:name=".SyncReceiver" android:exported="true" android:permission="it.geovision.permission.KEYBOX_IMPORT"><intent-filter><action android:name="it.geovision.keybox.SET_ACTIVE_INDEX"/><action android:name="it.geovision.keybox.GET_STATE"/></intent-filter></receiver>
  </application>
</manifest>
EOF
cat > "$JAVA/ExportKeysActivity.java" <<'EOF'
package it.geovision.keybox;
import android.app.*;import android.content.*;import android.os.*;
public class ExportKeysActivity extends Activity {
 public void onCreate(Bundle b){super.onCreate(b);String caller=getCallingPackage();if(caller==null||caller.trim().isEmpty()){setResult(RESULT_CANCELED);finish();return;}Intent o=StatePayload.make(this);setResult(RESULT_OK,o);finish();}
}
EOF
cat > "$JAVA/StatePayload.java" <<'EOF'
package it.geovision.keybox;
import android.content.*;
final class StatePayload {
 static Intent make(Context c){Intent o=new Intent();o.putExtra("google1",KeyVault.get(c,KeyVault.G1));o.putExtra("google2",KeyVault.get(c,KeyVault.G2));o.putExtra("google3",KeyVault.get(c,KeyVault.G3));o.putExtra("ai",KeyVault.get(c,KeyVault.AI));o.putExtra("youtube",KeyVault.get(c,KeyVault.YOUTUBE));o.putExtra("count",KeyVault.count(c));o.putExtra("activeIndex",KeyVault.activeIndex(c));o.putExtra("activeGeneration",KeyVault.generation(c));o.putExtra("switchTotalToday",KeyVault.switchTotalToday(c));o.putExtra("lastSwitchTime",KeyVault.lastSwitchTime(c));return o;}
}
EOF
cat > "$JAVA/SyncReceiver.java" <<'EOF'
package it.geovision.keybox;
import android.content.*;
public class SyncReceiver extends BroadcastReceiver {
 public void onReceive(Context c,Intent i){String a=i.getAction();if("it.geovision.keybox.SET_ACTIVE_INDEX".equals(a)){int x=i.getIntExtra("activeIndex",-1);KeyVault.setActiveIndex(c,x);return;}if("it.geovision.keybox.GET_STATE".equals(a)){String p=i.getStringExtra("replyPackage");if(p==null||p.trim().isEmpty())return;Intent out=StatePayload.make(c);out.setAction("it.geovision.keybox.STATE");out.setPackage(p);c.sendBroadcast(out,"it.geovision.permission.KEYBOX_IMPORT");}}
}
EOF
cat > "$JAVA/MainActivity.java" <<'EOF'
package it.geovision.keybox;
import android.app.*;import android.graphics.*;import android.os.*;import android.text.*;import android.view.*;import android.widget.*;
public class MainActivity extends Activity {
 EditText g1,g2,g3,ai,yt;TextView st;int dp(int v){return Math.round(v*getResources().getDisplayMetrics().density);}TextView tx(String s,int z,boolean b){TextView t=new TextView(this);t.setText(s);t.setTextSize(z);t.setTextColor(Color.rgb(30,41,59));if(b)t.setTypeface(t.getTypeface(),1);return t;}EditText f(String h){EditText e=new EditText(this);e.setHint(h);e.setSingleLine();e.setInputType(InputType.TYPE_CLASS_TEXT|InputType.TYPE_TEXT_VARIATION_PASSWORD);e.setPadding(dp(14),dp(12),dp(14),dp(12));return e;}
 public void onCreate(Bundle b){super.onCreate(b);ScrollView sc=new ScrollView(this);LinearLayout l=new LinearLayout(this);l.setOrientation(LinearLayout.VERTICAL);l.setPadding(dp(22),dp(28),dp(22),dp(30));sc.addView(l);l.addView(tx("KEYBOX 006 SYNC SAFE",25,true));TextView n=tx("Sincronizzazione centrale senza aperture automatiche, senza reload e senza interferire con le schede GeoVision.",14,false);n.setPadding(0,dp(8),0,dp(15));l.addView(n);g1=f("Google Maps API 1");g2=f("Google Maps API 2");g3=f("Google Maps API 3");ai=f("API Intelligenza Artificiale");yt=f("YouTube Data API");l.addView(g1);l.addView(g2);l.addView(g3);l.addView(ai);l.addView(yt);Button sv=new Button(this);sv.setText("SALVA LE 5 CHIAVI");sv.setOnClickListener(v->save());l.addView(sv);st=tx("",14,true);st.setPadding(0,dp(14),0,0);l.addView(st);setContentView(sc);load();status();}
 void load(){g1.setText(KeyVault.get(this,KeyVault.G1));g2.setText(KeyVault.get(this,KeyVault.G2));g3.setText(KeyVault.get(this,KeyVault.G3));ai.setText(KeyVault.get(this,KeyVault.AI));yt.setText(KeyVault.get(this,KeyVault.YOUTUBE));}
 void save(){try{KeyVault.put(this,KeyVault.G1,g1.getText().toString());KeyVault.put(this,KeyVault.G2,g2.getText().toString());KeyVault.put(this,KeyVault.G3,g3.getText().toString());KeyVault.put(this,KeyVault.AI,ai.getText().toString());KeyVault.put(this,KeyVault.YOUTUBE,yt.getText().toString());status();Toast.makeText(this,"Chiavi salvate",Toast.LENGTH_SHORT).show();}catch(Exception e){Toast.makeText(this,"Errore nel salvataggio",Toast.LENGTH_LONG).show();}}
 void status(){st.setText("Chiavi configurate: "+KeyVault.count(this)+" / 5\nGoogle attiva globale: "+(KeyVault.activeIndex(this)+1)+"\nGenerazione sync: "+KeyVault.generation(this)+"\nCambi oggi: "+KeyVault.switchTotalToday(this)+(KeyVault.lastSwitchTime(this).isEmpty()?"":"\nUltimo cambio: "+KeyVault.lastSwitchTime(this)));}
}
EOF
# KeyVault is committed in branch and retains prefs/keystore compatibility.
grep -q 'geovision_keybox_v1' "$JAVA/KeyVault.java"
grep -q 'GeoVisionKeyBoxMasterV1' "$JAVA/KeyVault.java"
grep -q 'activeIndex' "$JAVA/KeyVault.java"
grep -q 'GET_STATE' "$JAVA/SyncReceiver.java"
grep -q 'SET_ACTIVE_INDEX' "$JAVA/SyncReceiver.java"
gradle -p "$ROOT" clean assembleDebug
APK="$APP/build/outputs/apk/debug/app-debug.apk"
APKSIGNER=$(find "$ANDROID_HOME/build-tools" -type f -name apksigner | sort -V | tail -1); AAPT=$(find "$ANDROID_HOME/build-tools" -type f -name aapt | sort -V | tail -1)
"$APKSIGNER" verify --print-certs "$APK" | tee /tmp/kb006cert.txt
ACT=$(grep -i 'certificate SHA-256 digest:' /tmp/kb006cert.txt|head -1|awk '{print $NF}'|tr '[:upper:]' '[:lower:]'|tr -d ':'); test "$ACT" = "$EXPECTED"
"$AAPT" dump badging "$APK" | tee /tmp/kb006badging.txt
grep -q "package: name='it.geovision.keybox'" /tmp/kb006badging.txt
grep -q "versionCode='2006'" /tmp/kb006badging.txt
grep -q "application-label:'KEYBOX 006 SYNC SAFE'" /tmp/kb006badging.txt
cp "$APK" GeoVision_KEYBOX_006_SYNC_SAFE.apk
cat > README_KEYBOX_006_SYNC_SAFE.txt <<EOF
KEYBOX 006 SYNC SAFE
Package: it.geovision.keybox
VersionCode: 2006
Stessa firma/prefs/Keystore del KeyBox stabile.
Sync sicuro via broadcast firmati: GET_STATE / STATE / SET_ACTIVE_INDEX.
Nessun startActivityForResult automatico, nessun reload WebView, nessun pull da focus/visibility via Activity.
Mantiene activeIndex, activeGeneration, contatori giornalieri e ultimo cambio.
EOF
zip -j GeoVision_KEYBOX_006_SYNC_SAFE.zip GeoVision_KEYBOX_006_SYNC_SAFE.apk README_KEYBOX_006_SYNC_SAFE.txt
sha256sum GeoVision_KEYBOX_006_SYNC_SAFE.apk GeoVision_KEYBOX_006_SYNC_SAFE.zip
