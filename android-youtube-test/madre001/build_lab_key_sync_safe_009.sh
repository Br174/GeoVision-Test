#!/usr/bin/env bash
set -euo pipefail
ROOT='android-youtube-test'
HOST_SHA='a15e5192709be6dbafb0c5633e4d1ab9dd0cdd6b'
SOURCE_SHA='68dacd3854ff121bdab368c6f591a52d60a538b2e1a92a5545aadfe90ee45b33'
MADRE_HTML_SHA='a9968ed9870cdeeb27613b73f4e2ef5446696d3810e302f0282018583c338807'
MOTHER2_HTML_SHA='42aead77c8cac5c36d3eb9ec7cf81b9efb69f8fd5979ebd52a5e4ca01c28cb9b'
EXPECTED='716c1a8a139ad956ef8a00f85f153eb0028d109c75b1b938bdf3bb3eb23c22b5'

cat "$ROOT/madre001/parts/part00a.b64" "$ROOT/madre001/parts/part00b.b64" "$ROOT/madre001/parts/part01.b64" "$ROOT/madre001/parts/part02.b64" | tr -d '\n\r ' | base64 -d | gzip -d > /tmp/GeoVision_MADRE_001_SOURCE.html
test "$(sha256sum /tmp/GeoVision_MADRE_001_SOURCE.html|awk '{print $1}')" = "$SOURCE_SHA"
python "$ROOT/madre001/patch_key_panel.py"
python "$ROOT/madre001/patch_no_fallback.py"
python "$ROOT/madre001/patch_keybox_import.py"
python "$ROOT/madre001/patch_google_key_failover_004_bootsafe.py"
test "$(sha256sum /tmp/GeoVision_MADRE_001_SOURCE.html|awk '{print $1}')" = "$MADRE_HTML_SHA"
cp /tmp/GeoVision_MADRE_001_SOURCE.html /tmp/GeoVision_LAB_001_SOURCE.html
python "$ROOT/madre001/patch_candidate_photo_001.py"
test "$(sha256sum /tmp/GeoVision_LAB_001_SOURCE.html|awk '{print $1}')" = "$MOTHER2_HTML_SHA"

git show "$HOST_SHA:$ROOT/app/build.gradle" > "$ROOT/app/build.gradle"
git show "$HOST_SHA:$ROOT/app/src/main/AndroidManifest.xml" > "$ROOT/app/src/main/AndroidManifest.xml"
git show "$HOST_SHA:$ROOT/app/src/main/java/it/geovision/test/MainActivity.java" > "$ROOT/app/src/main/java/it/geovision/test/MainActivity.java"
mkdir -p "$ROOT/app/src/main/assets"
cp /tmp/GeoVision_LAB_001_SOURCE.html "$ROOT/app/src/main/assets/geovision.html"
python "$ROOT/madre001/patch_mainactivity_keybox.py"
python "$ROOT/madre001/patch_social_native_links.py"

python - <<'PY'
from pathlib import Path
import re
# Android identity + permission/query only.
root=Path('android-youtube-test')
g=root/'app/build.gradle'; s=g.read_text(); s=re.sub(r"applicationId '[^']+'","applicationId 'it.geovision.lab.keysyncsafe009'",s,1); s=re.sub(r'versionCode\s+\d+','versionCode 2009',s,1); s=re.sub(r"versionName '[^']+'","versionName '1.0-lab-key-sync-safe-009'",s,1); g.write_text(s)
m=root/'app/src/main/AndroidManifest.xml'; x=m.read_text(); needle='    <uses-permission android:name="android.permission.ACCESS_COARSE_LOCATION" />'; extra='''    <uses-permission android:name="android.permission.ACCESS_COARSE_LOCATION" />\n    <uses-permission android:name="it.geovision.permission.KEYBOX_IMPORT" />\n    <queries>\n        <package android:name="it.geovision.keybox" />\n        <package android:name="com.instagram.android" />\n        <package android:name="com.zhiliaoapp.musically" />\n    </queries>'''; x=x.replace(needle,extra,1); x=re.sub(r'android:label="[^"]+"','android:label="LAB 009 KEY SYNC SAFE"',x,1); m.write_text(x)

# Safe native KeyBox bridge: broadcast query, never opens an Activity automatically and never reloads the WebView.
j=root/'app/src/main/java/it/geovision/test/MainActivity.java'; s=j.read_text()
s=s.replace('import android.content.ActivityNotFoundException;\nimport android.content.Intent;\n','import android.content.ActivityNotFoundException;\nimport android.content.BroadcastReceiver;\nimport android.content.Context;\nimport android.content.Intent;\nimport android.content.IntentFilter;\n',1)
s=s.replace('import android.os.Bundle;\n','import android.os.Bundle;\nimport android.os.Build;\n',1)
s=s.replace('    private static final int REQ_KEYBOX = 7311;\n','    private static final int REQ_KEYBOX = 7311;\n    private volatile String keyBoxBootstrap = "";\n    private boolean keyBoxReceiverRegistered = false;\n    private boolean pageLoaded = false;\n',1)
old='''    private class KeyBoxBridge {\n        @JavascriptInterface\n        public void importKeys() {\n            main.post(() -> {\n                Intent intent = new Intent("it.geovision.keybox.EXPORT_KEYS");\n                intent.setPackage("it.geovision.keybox");\n                try {\n                    startActivityForResult(intent, REQ_KEYBOX);\n                } catch (ActivityNotFoundException e) {\n                    notifyKeyBoxError("Installa GeoVision KeyBox");\n                } catch (SecurityException e) {\n                    notifyKeyBoxError("KeyBox non autorizzato: verifica la firma GeoVision");\n                }\n            });\n        }\n    }\n'''
new='''    private JSONObject keyBoxPayload(Intent data) throws Exception {\n        JSONObject keys = new JSONObject();\n        keys.put("google1", data.getStringExtra("google1"));\n        keys.put("google2", data.getStringExtra("google2"));\n        keys.put("google3", data.getStringExtra("google3"));\n        keys.put("ai", data.getStringExtra("ai"));\n        keys.put("youtube", data.getStringExtra("youtube"));\n        keys.put("count", data.getIntExtra("count", 0));\n        keys.put("activeIndex", data.getIntExtra("activeIndex", 0));\n        keys.put("activeGeneration", data.getLongExtra("activeGeneration", 0L));\n        keys.put("switchTotalToday", data.getIntExtra("switchTotalToday", 0));\n        keys.put("lastSwitchTime", data.getStringExtra("lastSwitchTime"));\n        return keys;\n    }\n\n    private final BroadcastReceiver keyBoxStateReceiver = new BroadcastReceiver() {\n        @Override public void onReceive(Context context, Intent data) {\n            if (!"it.geovision.keybox.STATE".equals(data.getAction())) return;\n            try {\n                keyBoxBootstrap = keyBoxPayload(data).toString();\n                final String payload = keyBoxBootstrap;\n                main.post(() -> { if (webView != null && pageLoaded) webView.evaluateJavascript("window.gvApplyKeyBoxSafe009&&window.gvApplyKeyBoxSafe009(" + payload + ")", null); });\n            } catch (Exception ignored) { }\n        }\n    };\n\n    private void registerKeyBoxReceiver() {\n        if (keyBoxReceiverRegistered) return;\n        IntentFilter f = new IntentFilter("it.geovision.keybox.STATE");\n        if (Build.VERSION.SDK_INT >= 33) registerReceiver(keyBoxStateReceiver, f, Context.RECEIVER_EXPORTED); else registerReceiver(keyBoxStateReceiver, f);\n        keyBoxReceiverRegistered = true;\n    }\n\n    private void requestKeyBoxState() {\n        try {\n            Intent i = new Intent("it.geovision.keybox.GET_STATE");\n            i.setPackage("it.geovision.keybox");\n            i.putExtra("replyPackage", getPackageName());\n            sendBroadcast(i, "it.geovision.permission.KEYBOX_IMPORT");\n        } catch (Exception ignored) { }\n    }\n\n    private class KeyBoxBridge {\n        @JavascriptInterface public String bootstrapState() { return keyBoxBootstrap == null ? "" : keyBoxBootstrap; }\n        @JavascriptInterface public void syncState() { main.post(() -> requestKeyBoxState()); }\n        @JavascriptInterface public void setActiveIndex(int index) {\n            if (index < 0 || index > 2) return;\n            main.post(() -> { try { Intent i=new Intent("it.geovision.keybox.SET_ACTIVE_INDEX"); i.setPackage("it.geovision.keybox"); i.putExtra("activeIndex",index); sendBroadcast(i,"it.geovision.permission.KEYBOX_IMPORT"); } catch(Exception ignored){} });\n        }\n        @JavascriptInterface public void importKeys() {\n            main.post(() -> { Intent intent=new Intent("it.geovision.keybox.EXPORT_KEYS"); intent.setPackage("it.geovision.keybox"); try { startActivityForResult(intent,REQ_KEYBOX); } catch(ActivityNotFoundException e){ notifyKeyBoxError("Installa GeoVision KeyBox"); } catch(SecurityException e){ notifyKeyBoxError("KeyBox non autorizzato: verifica la firma GeoVision"); } });\n        }\n    }\n'''
if old not in s: raise SystemExit('KeyBoxBridge anchor missing')
s=s.replace(old,new,1)
# Manual import payload includes sync state.
s=s.replace('''            keys.put("count", data.getIntExtra("count", 0));\n            final String payload = keys.toString();''','''            keys.put("count", data.getIntExtra("count", 0));\n            keys.put("activeIndex", data.getIntExtra("activeIndex", 0));\n            keys.put("activeGeneration", data.getLongExtra("activeGeneration", 0L));\n            keys.put("switchTotalToday", data.getIntExtra("switchTotalToday", 0));\n            keys.put("lastSwitchTime", data.getStringExtra("lastSwitchTime"));\n            final String payload = keys.toString();\n            keyBoxBootstrap = payload;''',1)
s=s.replace('''                            "window.gvReceiveKeyBox&&window.gvReceiveKeyBox(" + payload + ")", null);''','''                            "(function(p){if(window.gvApplyKeyBoxSafe009)window.gvApplyKeyBoxSafe009(p);if(window.gvReceiveKeyBox)window.gvReceiveKeyBox(p);})(" + payload + ")", null);''',1)
# Register/query before first page and allow a small passive bootstrap window; no reload.
oldload='''        webView.loadUrl(localPage);'''
newload='''        registerKeyBoxReceiver();\n        requestKeyBoxState();\n        main.postDelayed(() -> { if (webView != null && !pageLoaded) { pageLoaded = true; webView.loadUrl(localPage); } }, 300);'''
s=s.replace(oldload,newload,1)
# onResume passive query only.
anchor='''    @Override\n    public void onBackPressed() {'''
s=s.replace(anchor,'''    @Override\n    protected void onResume() {\n        super.onResume();\n        if (keyBoxReceiverRegistered) requestKeyBoxState();\n    }\n\n    @Override\n    public void onBackPressed() {''',1)
s=s.replace('''        if (webView != null) webView.destroy();\n        super.onDestroy();''','''        if (keyBoxReceiverRegistered) { try { unregisterReceiver(keyBoxStateReceiver); } catch (Exception ignored) {} keyBoxReceiverRegistered=false; }\n        if (webView != null) webView.destroy();\n        super.onDestroy();''',1)
j.write_text(s)

# HTML: bootstrap state before app logic, safe apply function, failover report, and Monitor-style internal panel.
p=root/'app/src/main/assets/geovision.html'; h=p.read_text()
bootstrap=r'''<script id="gv-key-sync-safe-009-bootstrap">\n(function(){\n function apply(k){try{if(!k)return;const maps=[1,2,3].map(i=>String(k['google'+i]||'').trim());let idx=parseInt(k.activeIndex,10);if(!Number.isInteger(idx)||idx<0||idx>2||!maps[idx]){const f=maps.findIndex(Boolean);idx=f>=0?f:0;}maps.forEach((v,i)=>{const n='geovision_google_maps_api_key_'+(i+1);if(v)localStorage.setItem(n,v);else localStorage.removeItem(n);});localStorage.setItem('geovision_google_maps_api_keys',JSON.stringify(maps.filter(Boolean)));if(maps[idx])localStorage.setItem('geovision_google_maps_api_key',maps[idx]);localStorage.setItem('geovision_google_active_key_index',String(idx));if(k.ai)localStorage.setItem('geovision_ai_api_key',String(k.ai).trim());if(k.youtube)localStorage.setItem('geovision_youtube_api_key',String(k.youtube).trim());localStorage.setItem('geovision_keybox_active_generation',String(k.activeGeneration||0));localStorage.setItem('geovision_keybox_switch_total_today',String(k.switchTotalToday||0));}catch(e){}}\n window.gvApplyKeyBoxSafe009=function(k){apply(k);try{if(typeof gvDiagApplySelectedKey==='function')gvDiagApplySelectedKey();}catch(e){}};\n try{const raw=window.GeoVisionKeyBox&&window.GeoVisionKeyBox.bootstrapState&&window.GeoVisionKeyBox.bootstrapState();if(raw)apply(JSON.parse(raw));}catch(e){}\n})();\n</script>'''
h=h.replace('<head>','<head>'+bootstrap,1)
needle="localStorage.setItem('geovision_google_active_key_index', String(next));"
if needle not in h: raise SystemExit('failover anchor missing')
h=h.replace(needle,needle+"\n            try { window.GeoVisionKeyBox&&window.GeoVisionKeyBox.setActiveIndex&&window.GeoVisionKeyBox.setActiveIndex(next); } catch {}",1)
marker='function openKeysDiagnostics(){'
if marker not in h: raise SystemExit('diagnostics anchor missing')
ui=r'''function gv009Row(label,id){return `<div style="display:flex;align-items:center;gap:10px;margin-top:11px"><span id="${id}Dot" style="font-size:23px;color:#ef4444">●</span><div><b>${label}</b><div id="${id}Status" style="font-size:12px;color:#64748b">Da verificare</div></div></div>`;}\nfunction gv009Set(id,ok,t){const d=document.getElementById(id+'Dot'),s=document.getElementById(id+'Status');if(d)d.style.color=ok?'#22c55e':'#ef4444';if(s)s.textContent=t;}\nasync function gv009Live(){const ai=(document.getElementById('geminiKey')?.value||localStorage.getItem('geovision_ai_api_key')||'').trim(),yt=(document.getElementById('youtubeKey')?.value||localStorage.getItem('geovision_youtube_api_key')||'').trim();try{if(ai){const r=await fetch(`https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=${encodeURIComponent(ai)}`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({contents:[{parts:[{text:'Rispondi solo con OK'}]}],generationConfig:{maxOutputTokens:8}})});gv009Set('gv009Ai',r.ok,r.ok?'ATTIVA · Gemini operativo':`INATTIVA · errore ${r.status}`);}else gv009Set('gv009Ai',false,'INATTIVA · chiave assente');}catch{gv009Set('gv009Ai',false,'INATTIVA · non raggiungibile');}try{if(yt){const r=await fetch(`https://www.googleapis.com/youtube/v3/search?part=snippet&type=video&maxResults=1&q=GeoVision&key=${encodeURIComponent(yt)}`);gv009Set('gv009Yt',r.ok,r.ok?'ATTIVA · YouTube operativo':`INATTIVA · errore ${r.status}`);}else gv009Set('gv009Yt',false,'INATTIVA · chiave assente');}catch{gv009Set('gv009Yt',false,'INATTIVA · non raggiungibile');}}\nfunction gv009Decorate(){const panel=document.getElementById('keysDiagnosticsPanel')||document.querySelector('[data-role="keys-diagnostics"]'),host=panel?.querySelector('.panel-card')||panel?.firstElementChild||panel;if(!host||document.getElementById('gv009Monitor'))return;host.style.borderRadius='24px';host.style.border='1px solid #e2e8f0';host.style.background='#fff';const b=document.createElement('div');b.id='gv009Monitor';b.style.cssText='margin:14px 0;padding:14px;border:1px solid #e2e8f0;border-radius:18px;background:#f8fafc';b.innerHTML='<div style="font-size:17px;font-weight:900">Monitor chiavi API</div><div style="font-size:12px;color:#64748b">Pannello GeoVision: grafica aggiornata, funzioni app preservate.</div>'+gv009Row('Google Maps API 1','gv009G1')+gv009Row('Google Maps API 2','gv009G2')+gv009Row('Google Maps API 3','gv009G3')+gv009Row('API Intelligenza Artificiale','gv009Ai')+gv009Row('YouTube Data API','gv009Yt');host.insertBefore(b,host.firstChild);const p=(typeof gvDiagLoadGoogleKeyPool==='function')?gvDiagLoadGoogleKeyPool():{keys:[1,2,3].map(i=>localStorage.getItem('geovision_google_maps_api_key_'+i)||''),idx:parseInt(localStorage.getItem('geovision_google_active_key_index')||'0',10)||0};for(let i=0;i<3;i++){const has=!!String(p.keys[i]||'').trim(),act=has&&i===p.idx;gv009Set('gv009G'+(i+1),act,act?'ATTIVA ORA · selezionata':(has?'INATTIVA · disponibile':'INATTIVA · assente'));}gv009Live();}\n'''
h=h.replace(marker,ui+'\n'+marker,1)
if "$('#keysDiagnosticsOpen').onclick=openKeysDiagnostics;" in h:h=h.replace("$('#keysDiagnosticsOpen').onclick=openKeysDiagnostics;","$('#keysDiagnosticsOpen').onclick=()=>{openKeysDiagnostics();setTimeout(gv009Decorate,0);};",1)
p.write_text(h)
PY

# Guards: no old intrusive sync loop.
grep -q 'gv-key-sync-safe-009-bootstrap' "$ROOT/app/src/main/assets/geovision.html"
grep -q 'gv009Monitor' "$ROOT/app/src/main/assets/geovision.html"
grep -q 'GET_STATE' "$ROOT/app/src/main/java/it/geovision/test/MainActivity.java"
grep -q 'bootstrapState' "$ROOT/app/src/main/java/it/geovision/test/MainActivity.java"
! grep -q 'gvPullGlobalKey006' "$ROOT/app/src/main/assets/geovision.html"
! grep -q 'setTimeout(() => location.reload(), 250)' "$ROOT/app/src/main/assets/geovision.html"
grep -q 'renderOfficialGoogleCard' "$ROOT/app/src/main/assets/geovision.html"
grep -q 'gvTerritoryPhotos003' "$ROOT/app/src/main/assets/geovision.html"
python - <<'PY'
from pathlib import Path
import re
s=Path('android-youtube-test/app/src/main/assets/geovision.html').read_text(); blocks=re.findall(r'<script(?:\s+type="module")?[^>]*>([\s\S]*?)</script>',s); Path('/tmp/gv009.js').write_text('\n'.join(blocks))
PY
node --check /tmp/gv009.js
(cd "$ROOT"; gradle clean assembleDebug)
APK="$ROOT/app/build/outputs/apk/debug/app-debug.apk"; APKSIGNER=$(find "$ANDROID_HOME/build-tools" -type f -name apksigner|sort -V|tail -1); AAPT=$(find "$ANDROID_HOME/build-tools" -type f -name aapt|sort -V|tail -1)
"$APKSIGNER" verify --print-certs "$APK"|tee /tmp/lab009cert.txt; ACT=$(grep -i 'certificate SHA-256 digest:' /tmp/lab009cert.txt|head -1|awk '{print $NF}'|tr '[:upper:]' '[:lower:]'|tr -d ':'); test "$ACT" = "$EXPECTED"
"$AAPT" dump badging "$APK"|tee /tmp/lab009badging.txt; grep -q "package: name='it.geovision.lab.keysyncsafe009'" /tmp/lab009badging.txt; grep -q "application-label:'LAB 009 KEY SYNC SAFE'" /tmp/lab009badging.txt
cp "$APK" LAB_009_KEY_SYNC_SAFE.apk; cp "$ROOT/app/src/main/assets/geovision.html" LAB_009_KEY_SYNC_SAFE.html
cat > MANIFEST_LAB_009_KEY_SYNC_SAFE.txt <<EOF
LAB 009 KEY SYNC SAFE
Base funzionale: MADRE ORIGINALE 2.
Package isolato: it.geovision.lab.keysyncsafe009
Sync: broadcast passivo firmato GET_STATE/STATE + report SET_ACTIVE_INDEX.
Bootstrap: attesa massima 300 ms prima del primo load, nessun reload sync, nessuna Activity automatica.
Pannello chiavi interno: nuova grafica Monitor + test reali Gemini/YouTube; funzioni app preservate.
Scheda Google e metodo foto Mother2 preservati.
Firma: $EXPECTED
EOF
zip -j LAB_009_KEY_SYNC_SAFE.zip LAB_009_KEY_SYNC_SAFE.apk LAB_009_KEY_SYNC_SAFE.html MANIFEST_LAB_009_KEY_SYNC_SAFE.txt
sha256sum LAB_009_KEY_SYNC_SAFE.apk LAB_009_KEY_SYNC_SAFE.zip
