from pathlib import Path
import re,hashlib,subprocess,xml.etree.ElementTree as ET
R=Path(__file__).resolve().parents[2];base=(R/'out/madre2-baseline.html').read_text();new=(R/'out/LAB_012_FAILOVER.html').read_text()
assert hashlib.sha256(base.encode()).hexdigest()=='42aead77c8cac5c36d3eb9ec7cf81b9efb69f8fd5979ebd52a5e4ca01c28cb9b'
def normalize(s):
 s=re.sub(r'<script id="gv-key-state-012">[\s\S]*?</script>\s*','',s)
 s=re.sub(r'<style id="gv-monitor-style">[\s\S]*?</style>','',s)
 s=re.sub(r'<script id="gv-places-failover-012">[\s\S]*?</script>\s*','',s)
 s=re.sub(r'<script id="gv-monitor-012">[\s\S]*?</script>\s*','',s)
 s=re.sub(r'(?:let gvRetry012=0;\n)?function gvDiagAdvanceGoogleKey\(e\)[\s\S]*?(?=\ngvDiagApplySelectedKey\(\);)','KEY_FAILOVER',s)
 s=re.sub(r'(?:async )?function runGoogleDiagnostics\(\)[\s\S]*?(?=const esc =)','KEY_PANEL',s)
 s=re.sub(r"\$\('#mapsSetup'\).onclick =[\s\S]*?(?=\$\('#sheetClose'\).onclick)",'KEY_SETTINGS',s)
 s=s.replace("catch (e) {\n    gvDiagAdvanceGoogleKey(e);\n    setGoogleKeyState('error');", "catch {\n    setGoogleKeyState('error');")
 return re.sub(r'<head>\s*','<head>',s)
assert normalize(base)==normalize(new),'Unexpected change outside KeyBox/diagnostics/failover'
for i,b in enumerate(re.findall(r'<script\b[^>]*>([\s\S]*?)</script>',new)):
 p=R/f'out/check-{i}.mjs';p.write_text(b);subprocess.run(['node','--check',str(p)],check=True)
for name in ['renderOfficialGoogleCard','gvTerritoryPhotos003','speak','openUrl','scheduleLiveLocality']:
 assert name in base and name in new,name
assert 'gvReceiveKeyBox = function' not in new,'old duplicate import handler'
assert new.count('window.gvReceiveKeyBox=receive')==1
assert 'GVPlacesFailover.install()' in new and 'places:searchText' in new
assert '.gv-key-toggle' in new and 'OFF manuale' in new
places=(R/'monitor010/web/places-failover.js').read_text();assert 'location.reload' not in places
assert 'geovision_google_runtime_status_v2' in places and "mark(a.idx,true,'Places operativo')" in places and 'Quota Google esaurita' in places
monitor=(R/'monitor010/web/monitor.js').read_text();assert 'gvGoogleDetails' not in monitor and 'googleDiagRows' not in monitor
assert 'Verifica AI / YouTube' in monitor and 'Google si aggiorna durante l’uso reale' in monitor
# Synthetic Google verification is forbidden: Google health must be driven by actual GeoVision Places traffic.
assert "places.googleapis.com/v1/places:searchText" not in monitor
kstate=(R/'monitor010/web/key-state.js').read_text();assert 'geovision_google_enabled_v1' in kstate and 'setEnabled' in kstate
j=(R/'monitor010/native/KeyBoxClient.java').read_text()
assert 'registerReceiver(activity,receiver,f,PERMISSION,handler,androidx.core.content.ContextCompat.RECEIVER_EXPORTED)' in j
assert 'nonce.equals(i.getStringExtra("nonce"))' in j
assert j.count('startActivityForResult')==1 and '.reload(' not in j and 'loadUrl' not in j
assert 'setGoogleEnabled(int index,boolean enabled)' in j and 'googleEnabled' in j
assert 'handler.removeCallbacksAndMessages(null)' in j
for folder,app_id in [('android-keybox','it.geovision.keybox'),('android-youtube-test','it.geovision.lab.failover012')]:
 assert "applicationId '"+app_id+"'" in (R/f'{folder}/app/build.gradle').read_text()
 ET.parse(R/f'{folder}/app/src/main/AndroidManifest.xml')
kg=(R/'android-keybox/app/build.gradle').read_text();assert 'versionCode 2008' in kg and "versionName '8.0-monitor-switch'" in kg
manifest=(R/'android-keybox/app/src/main/AndroidManifest.xml').read_text();assert 'KEYBOX 008 MONITOR' in manifest and 'SET_GOOGLE_ENABLED_V1' in manifest
k=(R/'android-keybox/app/src/main/java/it/geovision/keybox/KeyVault.java').read_text()
assert 'geovision_keybox_v1' in k and 'GeoVisionKeyBoxMasterV1' in k and 'google1_enabled_v1' in k
print('PASS LAB 012: Mother hash; isolated modifications; JS syntax; real-use Google status; no synthetic Google probe; in-place failover; manual switches; secure sync; package/version IDs')
