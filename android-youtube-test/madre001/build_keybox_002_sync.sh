#!/usr/bin/env bash
set -euo pipefail
ROOT='android-youtube-test'
APP="$ROOT/app"
rm -rf "$APP/src/main/java/it/geovision/keybox"
mkdir -p "$APP/src/main/java/it/geovision/keybox"
cat > "$APP/build.gradle" <<'EOF'
plugins { id 'com.android.application' }
android {
  namespace 'it.geovision.keybox'
  compileSdk 35
  signingConfigs { stableDebug { storeFile file('../signing/geovision-debug-stable.keystore'); storePassword 'android'; keyAlias 'androiddebugkey'; keyPassword 'android' } }
  defaultConfig { applicationId 'it.geovision.keybox'; minSdk 23; targetSdk 35; versionCode 2002; versionName '2.0-key-sync' }
  buildTypes { debug { signingConfig signingConfigs.stableDebug } }
}
dependencies { }
EOF
cat > "$APP/src/main/AndroidManifest.xml" <<'EOF'
<manifest xmlns:android="http://schemas.android.com/apk/res/android">
  <permission android:name="it.geovision.permission.KEYBOX_IMPORT" android:protectionLevel="signature" />
  <application android:theme="@style/AppTheme" android:label="KEYBOX 002 SYNC" android:allowBackup="false">
    <activity android:name=".MainActivity" android:exported="true"><intent-filter><action android:name="android.intent.action.MAIN"/><category android:name="android.intent.category.LAUNCHER"/></intent-filter></activity>
    <activity android:name=".ExportKeysActivity" android:exported="true" android:permission="it.geovision.permission.KEYBOX_IMPORT"><intent-filter><action android:name="it.geovision.keybox.EXPORT_KEYS"/><category android:name="android.intent.category.DEFAULT"/></intent-filter></activity>
    <receiver android:name=".SyncReceiver" android:exported="true" android:permission="it.geovision.permission.KEYBOX_IMPORT"><intent-filter><action android:name="it.geovision.keybox.SET_ACTIVE_INDEX"/></intent-filter></receiver>
  </application>
</manifest>
EOF
cat > "$APP/src/main/java/it/geovision/keybox/KeyVault.java" <<'EOF'
package it.geovision.keybox;
import android.content.*; import android.security.keystore.*; import android.util.Base64; import java.nio.charset.StandardCharsets; import java.security.*; import javax.crypto.*; import javax.crypto.spec.GCMParameterSpec;
public final class KeyVault {
 static final String PREFS="geovision_keybox_v1", ALIAS="GeoVisionKeyBoxMasterV1";
 static SharedPreferences prefs(Context c){return c.getSharedPreferences(PREFS,Context.MODE_PRIVATE);}
 static SecretKey key() throws Exception {KeyStore ks=KeyStore.getInstance("AndroidKeyStore");ks.load(null);if(!ks.containsAlias(ALIAS)){KeyGenerator kg=KeyGenerator.getInstance("AES","AndroidKeyStore");kg.init(new KeyGenParameterSpec.Builder(ALIAS,KeyProperties.PURPOSE_ENCRYPT|KeyProperties.PURPOSE_DECRYPT).setBlockModes(KeyProperties.BLOCK_MODE_GCM).setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE).setKeySize(256).build());kg.generateKey();}return ((KeyStore.SecretKeyEntry)ks.getEntry(ALIAS,null)).getSecretKey();}
 static String enc(String v) throws Exception {Cipher c=Cipher.getInstance("AES/GCM/NoPadding");c.init(Cipher.ENCRYPT_MODE,key());byte[] iv=c.getIV(),e=c.doFinal(v.getBytes(StandardCharsets.UTF_8)),p=new byte[1+iv.length+e.length];p[0]=(byte)iv.length;System.arraycopy(iv,0,p,1,iv.length);System.arraycopy(e,0,p,1+iv.length,e.length);return Base64.encodeToString(p,Base64.NO_WRAP);}
 static String dec(String s) throws Exception {byte[] p=Base64.decode(s,Base64.NO_WRAP);int n=p[0]&255;if(n<8||1+n>=p.length)throw new Exception("bad");byte[] iv=new byte[n],e=new byte[p.length-1-n];System.arraycopy(p,1,iv,0,n);System.arraycopy(p,1+n,e,0,e.length);Cipher c=Cipher.getInstance("AES/GCM/NoPadding");c.init(Cipher.DECRYPT_MODE,key(),new GCMParameterSpec(128,iv));return new String(c.doFinal(e),StandardCharsets.UTF_8);}
 static void put(Context c,String k,String v) throws Exception {prefs(c).edit().putString(k,enc(v==null?"":v.trim())).apply();}
 static String get(Context c,String k){try{String v=prefs(c).getString(k,"");return v.isEmpty()?"":dec(v);}catch(Exception e){return "";}}
 static int active(Context c){int i=prefs(c).getInt("active_index",0);return i<0||i>2?0:i;}
 static long generation(Context c){return prefs(c).getLong("active_generation",0L);}
 static void setActive(Context c,int i){if(i<0||i>2)return;SharedPreferences p=prefs(c);p.edit().putInt("active_index",i).putLong("active_generation",p.getLong("active_generation",0L)+1L).apply();}
}
EOF
cat > "$APP/src/main/java/it/geovision/keybox/ExportKeysActivity.java" <<'EOF'
package it.geovision.keybox;
import android.app.*; import android.content.*; import android.os.Bundle;
public class ExportKeysActivity extends Activity { @Override public void onCreate(Bundle b){super.onCreate(b);Intent out=new Intent();String[] n={"google1","google2","google3","ai","youtube"};int count=0;for(String k:n){String v=KeyVault.get(this,k);out.putExtra(k,v);if(!v.isEmpty())count++;}out.putExtra("count",count);out.putExtra("activeIndex",KeyVault.active(this));out.putExtra("activeGeneration",KeyVault.generation(this));setResult(RESULT_OK,out);finish();} }
EOF
cat > "$APP/src/main/java/it/geovision/keybox/SyncReceiver.java" <<'EOF'
package it.geovision.keybox;
import android.content.*;
public class SyncReceiver extends BroadcastReceiver { public void onReceive(Context c,Intent i){int x=i.getIntExtra("activeIndex",-1);if(x>=0&&x<=2){KeyVault.setActive(c,x);Intent b=new Intent("it.geovision.keybox.ACTIVE_INDEX_CHANGED");b.putExtra("activeIndex",x);b.putExtra("activeGeneration",KeyVault.generation(c));b.setPackage(i.getStringExtra("targetPackage"));c.sendBroadcast(b,"it.geovision.permission.KEYBOX_IMPORT");}} }
EOF
cat > "$APP/src/main/java/it/geovision/keybox/MainActivity.java" <<'EOF'
package it.geovision.keybox;
import android.app.*;import android.os.*;import android.graphics.Color;import android.graphics.Typeface;import android.text.InputType;import android.view.*;import android.widget.*;import java.util.*;
public class MainActivity extends Activity {
 final LinkedHashMap<String,EditText> f=new LinkedHashMap<>(); TextView status;
 int dp(int x){return Math.round(x*getResources().getDisplayMetrics().density);} TextView t(String s,int z,boolean b){TextView v=new TextView(this);v.setText(s);v.setTextSize(z);v.setTextColor(Color.rgb(30,41,59));if(b)v.setTypeface(Typeface.DEFAULT_BOLD);v.setPadding(0,dp(8),0,dp(8));return v;}
 @Override public void onCreate(Bundle b){super.onCreate(b);ScrollView sc=new ScrollView(this);LinearLayout l=new LinearLayout(this);l.setOrientation(LinearLayout.VERTICAL);l.setPadding(dp(22),dp(28),dp(22),dp(28));sc.addView(l);l.addView(t("GeoVision KeyBox 002",26,true));l.addView(t("Chiavi condivise + sincronizzazione della chiave Google attiva",15,false));String[][] rows={{"google1","Google Maps API 1"},{"google2","Google Maps API 2"},{"google3","Google Maps API 3"},{"ai","API Intelligenza Artificiale"},{"youtube","YouTube Data API"}};for(String[] r:rows){l.addView(t(r[1],14,true));EditText e=new EditText(this);e.setSingleLine(true);e.setInputType(InputType.TYPE_CLASS_TEXT|InputType.TYPE_TEXT_VARIATION_PASSWORD);e.setText(KeyVault.get(this,r[0]));l.addView(e);f.put(r[0],e);}Button save=new Button(this);save.setText("SALVA LE 5 CHIAVI");save.setOnClickListener(v->save());l.addView(save);status=t("",15,true);l.addView(status);update();setContentView(sc);}
 void save(){try{for(Map.Entry<String,EditText> e:f.entrySet())KeyVault.put(this,e.getKey(),e.getValue().getText().toString());Toast.makeText(this,"Chiavi salvate",Toast.LENGTH_SHORT).show();update();}catch(Exception e){Toast.makeText(this,"Errore nel salvataggio",Toast.LENGTH_LONG).show();}}
 void update(){int c=0;for(String k:f.keySet())if(!KeyVault.get(this,k).isEmpty())c++;status.setText("Chiavi configurate: "+c+" / 5\nChiave Google attiva globale: "+(KeyVault.active(this)+1)+"\nGenerazione sync: "+KeyVault.generation(this));}
}
EOF
(
 cd "$ROOT"; gradle clean assembleDebug
)
APK="$APP/build/outputs/apk/debug/app-debug.apk"
APKSIGNER=$(find "$ANDROID_HOME/build-tools" -type f -name apksigner | sort -V | tail -1)
AAPT=$(find "$ANDROID_HOME/build-tools" -type f -name aapt | sort -V | tail -1)
EXPECTED='716c1a8a139ad956ef8a00f85f153eb0028d109c75b1b938bdf3bb3eb23c22b5'
"$APKSIGNER" verify --print-certs "$APK" | tee /tmp/kb2cert.txt
ACT=$(grep -i 'certificate SHA-256 digest:' /tmp/kb2cert.txt|head -1|awk '{print $NF}'|tr '[:upper:]' '[:lower:]'|tr -d ':'); test "$ACT" = "$EXPECTED"
"$AAPT" dump badging "$APK" | tee /tmp/kb2badging.txt
grep -q "package: name='it.geovision.keybox'" /tmp/kb2badging.txt
grep -q "application-label:'KEYBOX 002 SYNC'" /tmp/kb2badging.txt
cp "$APK" GeoVision_KEYBOX_002_SYNC.apk
cat > README_KEYBOX_002_SYNC.txt <<EOF
GeoVision KEYBOX 002 SYNC
Package: it.geovision.keybox (aggiornamento diretto di KEYBOX 001, stessa famiglia per preservare archivio e collegamenti).
Firma SHA256: $EXPECTED
Compatibilita: mantiene prefs geovision_keybox_v1 e alias AndroidKeyStore GeoVisionKeyBoxMasterV1.
Nuovo stato globale: activeIndex 0..2 + activeGeneration.
EXPORT_KEYS restituisce anche activeIndex e activeGeneration, oltre alle 5 chiavi e count.
Azione sync: it.geovision.keybox.SET_ACTIVE_INDEX, protetta dalla permission signature it.geovision.permission.KEYBOX_IMPORT.
NOTA: le app GeoVision esistenti continuano a importare normalmente le chiavi. Per sincronizzare automaticamente lo switch attivo devono ricevere la piccola integrazione client KeyBox Sync nelle future LAB/CAND/MADRE.
EOF
zip -j GeoVision_KEYBOX_002_SYNC.zip GeoVision_KEYBOX_002_SYNC.apk README_KEYBOX_002_SYNC.txt
sha256sum GeoVision_KEYBOX_002_SYNC.apk GeoVision_KEYBOX_002_SYNC.zip
