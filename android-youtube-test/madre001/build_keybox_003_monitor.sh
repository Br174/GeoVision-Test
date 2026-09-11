#!/usr/bin/env bash
set -euo pipefail
ROOT='android-youtube-test'
APP="$ROOT/app"
rm -rf "$APP/src/main/java/it"
mkdir -p "$APP/src/main/java/it/geovision/keybox"
cat > "$APP/build.gradle" <<'EOF'
plugins { id 'com.android.application' }
android {
  namespace 'it.geovision.keybox'
  compileSdk 35
  signingConfigs { stableDebug { storeFile file('../signing/geovision-debug-stable.keystore'); storePassword 'android'; keyAlias 'androiddebugkey'; keyPassword 'android' } }
  defaultConfig { applicationId 'it.geovision.keybox'; minSdk 23; targetSdk 35; versionCode 2003; versionName '3.0-key-monitor' }
  buildTypes { debug { signingConfig signingConfigs.stableDebug } }
}
dependencies { }
EOF
cat > "$APP/src/main/AndroidManifest.xml" <<'EOF'
<manifest xmlns:android="http://schemas.android.com/apk/res/android">
  <permission android:name="it.geovision.permission.KEYBOX_IMPORT" android:protectionLevel="signature" />
  <application android:theme="@style/AppTheme" android:label="KEYBOX 003 MONITOR" android:allowBackup="false">
    <activity android:name=".MainActivity" android:exported="true"><intent-filter><action android:name="android.intent.action.MAIN"/><category android:name="android.intent.category.LAUNCHER"/></intent-filter></activity>
    <activity android:name=".ExportKeysActivity" android:exported="true" android:permission="it.geovision.permission.KEYBOX_IMPORT"><intent-filter><action android:name="it.geovision.keybox.EXPORT_KEYS"/><category android:name="android.intent.category.DEFAULT"/></intent-filter></activity>
    <receiver android:name=".SyncReceiver" android:exported="true" android:permission="it.geovision.permission.KEYBOX_IMPORT"><intent-filter><action android:name="it.geovision.keybox.SET_ACTIVE_INDEX"/></intent-filter></receiver>
  </application>
</manifest>
EOF
cat > "$APP/src/main/java/it/geovision/keybox/KeyVault.java" <<'EOF'
package it.geovision.keybox;
import android.content.*; import android.security.keystore.*; import android.util.Base64; import java.nio.charset.StandardCharsets; import java.security.*; import javax.crypto.*; import javax.crypto.spec.GCMParameterSpec; import java.text.SimpleDateFormat; import java.util.*;
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
 static String day(){return new SimpleDateFormat("yyyyMMdd",Locale.US).format(new Date());}
 static void ensureDay(Context c){SharedPreferences p=prefs(c);String d=day();if(!d.equals(p.getString("stats_day",""))){p.edit().putString("stats_day",d).putInt("switch_total_day",0).putInt("switch_key_0_day",0).putInt("switch_key_1_day",0).putInt("switch_key_2_day",0).apply();}}
 static int totalToday(Context c){ensureDay(c);return prefs(c).getInt("switch_total_day",0);}
 static int keyToday(Context c,int i){ensureDay(c);return prefs(c).getInt("switch_key_"+i+"_day",0);}
 static long lastSwitchAt(Context c){return prefs(c).getLong("last_switch_at",0L);}
 static boolean setActive(Context c,int i){if(i<0||i>2)return false;ensureDay(c);SharedPreferences p=prefs(c);int old=active(c);if(old==i)return false;long gen=p.getLong("active_generation",0L)+1L;int total=p.getInt("switch_total_day",0)+1;int per=p.getInt("switch_key_"+i+"_day",0)+1;p.edit().putInt("active_index",i).putLong("active_generation",gen).putInt("switch_total_day",total).putInt("switch_key_"+i+"_day",per).putLong("last_switch_at",System.currentTimeMillis()).apply();return true;}
}
EOF
cat > "$APP/src/main/java/it/geovision/keybox/ExportKeysActivity.java" <<'EOF'
package it.geovision.keybox;
import android.app.*; import android.content.*; import android.os.Bundle;
public class ExportKeysActivity extends Activity { @Override public void onCreate(Bundle b){super.onCreate(b);Intent out=new Intent();String[] n={"google1","google2","google3","ai","youtube"};int count=0;for(String k:n){String v=KeyVault.get(this,k);out.putExtra(k,v);if(!v.isEmpty())count++;}out.putExtra("count",count);out.putExtra("activeIndex",KeyVault.active(this));out.putExtra("activeGeneration",KeyVault.generation(this));out.putExtra("switchTotalToday",KeyVault.totalToday(this));for(int i=0;i<3;i++)out.putExtra("switchKey"+(i+1)+"Today",KeyVault.keyToday(this,i));setResult(RESULT_OK,out);finish();} }
EOF
cat > "$APP/src/main/java/it/geovision/keybox/SyncReceiver.java" <<'EOF'
package it.geovision.keybox;
import android.content.*;
public class SyncReceiver extends BroadcastReceiver { public void onReceive(Context c,Intent i){int x=i.getIntExtra("activeIndex",-1);if(x>=0&&x<=2){KeyVault.setActive(c,x);Intent b=new Intent("it.geovision.keybox.ACTIVE_INDEX_CHANGED");b.putExtra("activeIndex",KeyVault.active(c));b.putExtra("activeGeneration",KeyVault.generation(c));b.putExtra("switchTotalToday",KeyVault.totalToday(c));b.setPackage(i.getStringExtra("targetPackage"));c.sendBroadcast(b,"it.geovision.permission.KEYBOX_IMPORT");}} }
EOF
cat > "$APP/src/main/java/it/geovision/keybox/MainActivity.java" <<'EOF'
package it.geovision.keybox;
import android.app.*;import android.os.*;import android.graphics.Color;import android.graphics.Typeface;import android.text.InputType;import android.view.*;import android.widget.*;import java.util.*;import java.text.SimpleDateFormat;
public class MainActivity extends Activity {
 final LinkedHashMap<String,EditText> f=new LinkedHashMap<>(); final TextView[] dots=new TextView[3]; final TextView[] stats=new TextView[3]; TextView status;
 int dp(int x){return Math.round(x*getResources().getDisplayMetrics().density);} TextView t(String s,int z,boolean b){TextView v=new TextView(this);v.setText(s);v.setTextSize(z);v.setTextColor(Color.rgb(30,41,59));if(b)v.setTypeface(Typeface.DEFAULT_BOLD);v.setPadding(0,dp(6),0,dp(6));return v;}
 @Override public void onCreate(Bundle b){super.onCreate(b);ScrollView sc=new ScrollView(this);LinearLayout l=new LinearLayout(this);l.setOrientation(LinearLayout.VERTICAL);l.setPadding(dp(22),dp(24),dp(22),dp(28));sc.addView(l);l.addView(t("GeoVision KeyBox 003",26,true));l.addView(t("Chiavi condivise + stato attivo + contatore switch giornaliero",15,false));String[][] rows={{"google1","Google Maps API 1"},{"google2","Google Maps API 2"},{"google3","Google Maps API 3"},{"ai","API Intelligenza Artificiale"},{"youtube","YouTube Data API"}};int gi=0;for(String[] r:rows){if(gi<3){LinearLayout head=new LinearLayout(this);head.setOrientation(LinearLayout.HORIZONTAL);head.setGravity(Gravity.CENTER_VERTICAL);TextView d=t("●",25,true);d.setPadding(0,0,dp(10),0);dots[gi]=d;head.addView(d);TextView lab=t(r[1],14,true);head.addView(lab);l.addView(head);TextView st=t("",12,false);stats[gi]=st;l.addView(st);}else l.addView(t(r[1],14,true));EditText e=new EditText(this);e.setSingleLine(true);e.setInputType(InputType.TYPE_CLASS_TEXT|InputType.TYPE_TEXT_VARIATION_PASSWORD);e.setText(KeyVault.get(this,r[0]));l.addView(e);f.put(r[0],e);gi++;}Button save=new Button(this);save.setText("SALVA LE 5 CHIAVI");save.setOnClickListener(v->save());l.addView(save);status=t("",15,true);l.addView(status);setContentView(sc);update();}
 @Override protected void onResume(){super.onResume();update();}
 void save(){try{for(Map.Entry<String,EditText> e:f.entrySet())KeyVault.put(this,e.getKey(),e.getValue().getText().toString());Toast.makeText(this,"Chiavi salvate",Toast.LENGTH_SHORT).show();update();}catch(Exception e){Toast.makeText(this,"Errore nel salvataggio",Toast.LENGTH_LONG).show();}}
 void update(){KeyVault.ensureDay(this);int c=0;for(String k:f.keySet())if(!KeyVault.get(this,k).isEmpty())c++;int a=KeyVault.active(this);for(int i=0;i<3;i++){boolean on=i==a;dots[i].setTextColor(on?Color.rgb(22,163,74):Color.rgb(220,38,38));stats[i].setText((on?"ATTIVA ORA":"INATTIVA")+"  •  Switch oggi: "+KeyVault.keyToday(this,i));stats[i].setTextColor(on?Color.rgb(22,101,52):Color.rgb(127,29,29));}long ls=KeyVault.lastSwitchAt(this);String when=ls>0?new SimpleDateFormat("HH:mm",Locale.getDefault()).format(new Date(ls)):"nessuno";status.setText("Chiavi configurate: "+c+" / 5\nChiave Google attiva globale: "+(a+1)+"\nSwitch totali oggi: "+KeyVault.totalToday(this)+"\nUltimo switch: "+when+"\nGenerazione sync: "+KeyVault.generation(this));}
}
EOF
(
 cd "$ROOT"; gradle clean assembleDebug
)
APK="$APP/build/outputs/apk/debug/app-debug.apk"
APKSIGNER=$(find "$ANDROID_HOME/build-tools" -type f -name apksigner | sort -V | tail -1)
AAPT=$(find "$ANDROID_HOME/build-tools" -type f -name aapt | sort -V | tail -1)
EXPECTED='716c1a8a139ad956ef8a00f85f153eb0028d109c75b1b938bdf3bb3eb23c22b5'
"$APKSIGNER" verify --print-certs "$APK" | tee /tmp/kb3cert.txt
ACT=$(grep -i 'certificate SHA-256 digest:' /tmp/kb3cert.txt|head -1|awk '{print $NF}'|tr '[:upper:]' '[:lower:]'|tr -d ':'); test "$ACT" = "$EXPECTED"
"$AAPT" dump badging "$APK" | tee /tmp/kb3badging.txt
grep -q "package: name='it.geovision.keybox'" /tmp/kb3badging.txt
grep -q "application-label:'KEYBOX 003 MONITOR'" /tmp/kb3badging.txt
cp "$APK" GeoVision_KEYBOX_003_MONITOR.apk
cat > README_KEYBOX_003_MONITOR.txt <<EOF
GeoVision KEYBOX 003 MONITOR
Package: it.geovision.keybox (aggiornamento diretto di KEYBOX 002; stessa famiglia per preservare chiavi e stato).
Firma SHA256: $EXPECTED
Mantiene prefs geovision_keybox_v1 e alias AndroidKeyStore GeoVisionKeyBoxMasterV1.
Indicatori: verde = chiave Google attiva globale; rosso = chiave non attiva.
Statistiche giornaliere: switch per singola chiave (conteggiato quando quella chiave DIVENTA attiva) + switch totali del giorno.
I contatori giornalieri si azzerano automaticamente al cambio data locale.
Ripetere lo stesso activeIndex non incrementa il contatore: conta solo un vero cambio 1->2, 2->3, ecc.
EXPORT_KEYS include activeIndex, activeGeneration e contatori giornalieri.
Nota: per sincronizzazione automatica effettiva tra MADRE/LAB/CAND le app GeoVision devono usare il client KeyBox Sync nelle prossime build.
EOF
zip -j GeoVision_KEYBOX_003_MONITOR.zip GeoVision_KEYBOX_003_MONITOR.apk README_KEYBOX_003_MONITOR.txt
sha256sum GeoVision_KEYBOX_003_MONITOR.apk GeoVision_KEYBOX_003_MONITOR.zip
