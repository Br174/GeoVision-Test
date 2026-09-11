from pathlib import Path
import re,hashlib,subprocess,xml.etree.ElementTree as ET
R=Path(__file__).resolve().parents[2];base=(R/'out/madre2-baseline.html').read_text();new=(R/'out/LAB_010_MONITOR_SYNC.html').read_text()
assert hashlib.sha256(base.encode()).hexdigest()=='42aead77c8cac5c36d3eb9ec7cf81b9efb69f8fd5979ebd52a5e4ca01c28cb9b'
# Compare every byte outside the two intentionally changed key/diagnostics functions and added assets.
def normalize(s):
 s=re.sub(r'<script id="gv-key-state-010">[\s\S]*?</script>\s*','',s)
 s=re.sub(r'<style id="gv-monitor-style">[\s\S]*?</style>','',s)
 s=re.sub(r'<script id="gv-monitor-010">[\s\S]*?</script>\s*','',s)
 s=re.sub(r'(?:let gvSwitchPending010=false,gvRetry010=0;\n)?function gvDiagAdvanceGoogleKey\(e\)[\s\S]*?(?=\ngvDiagApplySelectedKey\(\);)','KEY_FAILOVER',s)
 s=re.sub(r'(?:async )?function runGoogleDiagnostics\(\)[\s\S]*?(?=const esc =)','KEY_PANEL',s)
 s=re.sub(r"\$\('#mapsSetup'\).onclick =[\s\S]*?(?=\$\('#sheetClose'\).onclick)",'KEY_SETTINGS',s)
 s=s.replace("catch (e) {\n    gvDiagAdvanceGoogleKey(e);\n    setGoogleKeyState('error');", "catch {\n    setGoogleKeyState('error');")
 s=s.replace('gvPlacesSearch010(P,', 'P.searchByText(')
 return re.sub(r'<head>\s*','<head>',s)
assert normalize(base)==normalize(new),'Unexpected change outside KeyBox/diagnostics'
for i,b in enumerate(re.findall(r'<script\b[^>]*>([\s\S]*?)</script>',new)):
 p=R/f'out/check-{i}.mjs';p.write_text(b);subprocess.run(['node','--check',str(p)],check=True)
for name in ['renderOfficialGoogleCard','gvTerritoryPhotos003','speak','openUrl','scheduleLiveLocality']:
 assert name in base and name in new,name
assert 'gvReceiveKeyBox = function' not in new,'old duplicate import handler'
assert new.count('window.gvReceiveKeyBox=receive')==1
assert 'window.gvMonitorGoogleDiagnostics=runGoogleServiceDiagnostics' in new
j=(R/'monitor010/native/KeyBoxClient.java').read_text()
assert 'registerReceiver(activity,receiver,f,PERMISSION,handler,androidx.core.content.ContextCompat.RECEIVER_EXPORTED)' in j
assert 'nonce.equals(i.getStringExtra("nonce"))' in j
assert j.count('startActivityForResult')==1 and '.reload(' not in j and 'loadUrl' not in j
assert 'handler.removeCallbacksAndMessages(null)' in j
for folder,app_id in [('android-keybox','it.geovision.keybox'),('android-youtube-test','it.geovision.lab.monitor010')]:
 assert "applicationId '"+app_id+"'" in (R/f'{folder}/app/build.gradle').read_text()
 ET.parse(R/f'{folder}/app/src/main/AndroidManifest.xml')
k=(R/'android-keybox/app/src/main/java/it/geovision/keybox/KeyVault.java').read_text()
assert 'geovision_keybox_v1' in k and 'GeoVisionKeyBoxMasterV1' in k
print('PASS: exact Madre hash; all code outside key subsystem identical; JavaScript syntax; single handler; receiver security/lifecycle; IDs; vault compatibility')

assert new.count('gvPlacesSearch010(P,')==7
assert new.count('P.searchByText(')==2 # helper plus observational diagnostic
