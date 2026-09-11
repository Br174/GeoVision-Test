from pathlib import Path
import base64,gzip,hashlib,subprocess,re,shutil
ROOT=Path(__file__).resolve().parents[1]
M=ROOT/'monitor010'; A=ROOT/'android-youtube-test'; P=A/'madre001'
def sha(b):return hashlib.sha256(b).hexdigest()
def once(s,old,new):
 assert s.count(old)==1,('anchor',old[:70],s.count(old))
 return s.replace(old,new,1)
b=b''.join((P/f'parts/{n}.b64').read_bytes() for n in ['part00a','part00b','part01','part02'])
s=gzip.decompress(base64.b64decode(b));assert sha(s)=='68dacd3854ff121bdab368c6f591a52d60a538b2e1a92a5545aadfe90ee45b33'
Path('/tmp/GeoVision_MADRE_001_SOURCE.html').write_bytes(s)
for n in ['patch_key_panel.py','patch_no_fallback.py','patch_keybox_import.py','patch_google_key_failover_004_bootsafe.py']:subprocess.run(['python',str(P/n)],check=True)
s=Path('/tmp/GeoVision_MADRE_001_SOURCE.html').read_bytes();assert sha(s)=='a9968ed9870cdeeb27613b73f4e2ef5446696d3810e302f0282018583c338807'
Path('/tmp/GeoVision_LAB_001_SOURCE.html').write_bytes(s);subprocess.run(['python',str(P/'patch_candidate_photo_001.py')],check=True)
baseline=Path('/tmp/GeoVision_LAB_001_SOURCE.html').read_bytes();assert sha(baseline)=='42aead77c8cac5c36d3eb9ec7cf81b9efb69f8fd5979ebd52a5e4ca01c28cb9b'
(ROOT/'out').mkdir(exist_ok=True);(ROOT/'out/madre2-baseline.html').write_bytes(baseline)
h=baseline.decode()
# Replace only the diagnostics panel preamble; service checks remain explicitly available.
a=h.index('async function runGoogleDiagnostics() {');b=h.index("    const rows = document.getElementById('googleDiagRows');",a)
h=h[:a]+"function runGoogleDiagnostics(){GVMonitor.open();}\nwindow.gvMonitorGoogleDiagnostics=runGoogleServiceDiagnostics;\nasync function runGoogleServiceDiagnostics(){\n"+h[b:]
h=once(h,"    const rows = document.getElementById('googleDiagRows');","    const rows = document.getElementById('googleDiagRows');\n    if(!rows)return;")
# A manual diagnostic reports errors but does not itself rotate keys.
h=once(h,'            gvDiagAdvanceGoogleKey(e);','            // Manual diagnostics do not change the running key.')
# Replace the historical reload-on-every-failover behavior. Normal Places failures are retried in-place.
a=h.index('function gvDiagAdvanceGoogleKey(e) {');b=h.index('\ngvDiagApplySelectedKey();',a)
h=h[:a]+'''let gvRetry011=0;
function gvDiagAdvanceGoogleKey(e){
    const st=GVKeyState.create(localStorage);
    const changed=st.advance(e);
    if(changed){
        const active=st.active();
        if(active.key)googleKey=active.key;
        try{setGoogleKeyState('ok');}catch(_){}
        return true;
    }
    if(gvDiagIsKeyFailure(e)){
        toast('Nessuna chiave Google abilitata e disponibile.');
        if(!gvRetry011)gvRetry011=setTimeout(()=>{gvRetry011=0;},60000);
    }
    return false;
}
window.gm_authFailure=()=>{
    // The Maps JavaScript SDK itself cannot swap credentials in place: only this SDK-auth edge case reloads.
    if(gvDiagAdvanceGoogleKey({code:'REQUEST_DENIED',message:'Maps JavaScript authentication failure'}))setTimeout(()=>location.reload(),450);
};'''+h[b:]
# Existing settings entry points open one unified Monitor.
a=h.index("$('#mapsSetup').onclick =");b=h.index("$('#sheetClose').onclick",a)
h=h[:a]+"$('#mapsSetup').onclick = () => GVMonitor.open();\n$('#mapsSave').onclick = () => GVMonitor.open();\n"+h[b:]
# Keep legacy map-load error reporting but let the bounded state engine decide whether a key error advances.
old="catch {\n    setGoogleKeyState('error');\n    $('#mapsState').textContent = 'Google Maps non disponibile · mappa di riserva attiva';"
new="catch (e) {\n    gvDiagAdvanceGoogleKey(e);\n    setGoogleKeyState('error');\n    $('#mapsState').textContent = 'Google Maps non disponibile · mappa di riserva attiva';"
h=once(h,old,new)
# Snapshot loading happens synchronously before any application initialization.
bootstrap=(M/'web/key-state.js').read_text()+'''\ntry{GVKeyState.create(localStorage).commitPending();}catch(e){window.gvKeyStartupError=e.message;}\n'''
h=once(h,'<head>','<head>\n<script id="gv-key-state-011">'+bootstrap+'</script>\n<style id="gv-monitor-style">'+(M/'web/monitor.css').read_text()+'</style>')
# Install the transparent Places wrapper after the original app has loaded its globals. It never reloads for Places quota/key failures.
places=(M/'web/places-failover.js').read_text()+'''\nwindow.gvGoogleKeyChanged=function(idx,key,reason){try{googleKey=key||googleKey;setGoogleKeyState('ok');}catch(_){} };\n(function(){let n=0;const t=setInterval(()=>{try{if(window.GVPlacesFailover&&GVPlacesFailover.install()){clearInterval(t);return;}}catch(_){}if(++n>80)clearInterval(t);},125);})();\n'''
h=once(h,'</body>','<script id="gv-places-failover-011">'+places+'</script>\n<script id="gv-monitor-011">'+(M/'web/monitor.js').read_text()+'</script>\n</body>')
assets=A/'app/src/main/assets';assets.mkdir(parents=True,exist_ok=True);(assets/'geovision.html').write_text(h);(ROOT/'out/LAB_011_FAILOVER.html').write_text(h)
# Use the exact approved Android host; no mutations of Mother branch.
for p in (M/'host').rglob('*'):
 if p.is_file():dest=A/p.relative_to(M/'host');dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,dest)
for n in ['patch_mainactivity_keybox.py','patch_social_native_links.py']:subprocess.run(['python',str(P/n)],cwd=ROOT,check=True)
j=A/'app/src/main/java/it/geovision/test/MainActivity.java';s=j.read_text()
s=once(s,'    private static final int REQ_KEYBOX = 7311;','    private KeyBoxClient keyBoxClient;')
s=once(s,'        webView.addJavascriptInterface(new KeyBoxBridge(), "GeoVisionKeyBox");','        keyBoxClient=new KeyBoxClient(this,webView);\n        webView.addJavascriptInterface(keyBoxClient, "GeoVisionKeyBox");')
a=s.index('    private void notifyKeyBoxError(');b=s.index('    private class NativeTtsBridge',a);s=s[:a]+s[b:]
a=s.index('    @Override\n    protected void onActivityResult(');b=s.index('    @Override\n    public void onBackPressed()',a)
s=s[:a]+'''    @Override protected void onActivityResult(int requestCode,int resultCode,Intent data){
        super.onActivityResult(requestCode,resultCode,data);
        if(requestCode==KeyBoxClient.REQUEST)keyBoxClient.result(resultCode,data);
    }
    @Override protected void onResume(){super.onResume();if(keyBoxClient!=null)keyBoxClient.resume();}
'''+s[b:]
s=once(s,'        if (webView != null) webView.destroy();','        if(keyBoxClient!=null)keyBoxClient.destroy();\n        if (webView != null) webView.destroy();')
j.write_text(s);shutil.copyfile(M/'native/KeyBoxClient.java',j.parent/'KeyBoxClient.java')
g=A/'app/build.gradle';s=g.read_text();s=re.sub(r"applicationId '[^']+'","applicationId 'it.geovision.lab.failover011'",s,count=1);s=re.sub(r'versionCode\s+\d+','versionCode 2011',s,count=1);s=re.sub(r"versionName '[^']+'","versionName '1.0-failover-011'",s,count=1);s=s.replace("versionCode 2011","testInstrumentationRunner 'androidx.test.runner.AndroidJUnitRunner'\n        versionCode 2011")
s+='\ndependencies { implementation "androidx.core:core:1.13.1"; androidTestImplementation "androidx.test:runner:1.6.2"; androidTestImplementation "androidx.test.ext:junit:1.2.1" }\n'
g.write_text(s)
t=A/'app/src/androidTest/java/it/geovision/test';t.mkdir(parents=True,exist_ok=True);shutil.copyfile(M/'android-tests/BridgeTest.java',t/'BridgeTest.java')
x=A/'app/src/main/AndroidManifest.xml';s=x.read_text();s=s.replace('<application','<uses-permission android:name="it.geovision.permission.KEYBOX_IMPORT"/>\n    <queries><package android:name="it.geovision.keybox"/><package android:name="com.instagram.android"/><package android:name="com.zhiliaoapp.musically"/></queries>\n    <application',1);s=re.sub(r'android:label="[^"]+"','android:label="LAB 011 FAILOVER"',s,count=1);x.write_text(s)
# Reconstruct validated launcher PNG; remove the historical mislabeled placeholder.
for p in (A/'app/src/main/res').rglob('ic_launcher.png'):p.unlink()
icon=base64.b64decode((A/'icon/geovision_icon.png.b64').read_bytes());assert icon[:8]==b'\x89PNG\r\n\x1a\n'
p=A/'app/src/main/res/drawable-nodpi/ic_launcher.png';p.parent.mkdir(exist_ok=True);p.write_bytes(icon)
p=A/'signing/geovision-debug-stable.keystore';p.write_bytes(base64.b64decode(p.with_suffix('.keystore.b64').read_bytes()));p.chmod(0o600)
print('Prepared KEYBOX 008 and LAB 011; Mother 2 SHA256 verified:',sha(baseline))
