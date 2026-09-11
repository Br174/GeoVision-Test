#!/usr/bin/env bash
set -euo pipefail
python monitor010/prepare.py
node --test monitor010/tests/key-state.test.js
python monitor010/tests/static.py
gradle -p android-keybox assembleDebug assembleDebugAndroidTest lintDebug
gradle -p android-youtube-test assembleDebug assembleDebugAndroidTest lintDebug
python - <<'PY'
from pathlib import Path
import zipfile,hashlib,subprocess,os,re
sdk=Path(os.environ['ANDROID_HOME']);bt=sorted((sdk/'build-tools').iterdir())[-1]
items=[
 ('android-keybox','KEYBOX_008_MONITOR','it.geovision.keybox','2008','KEYBOX 008 MONITOR',None),
 ('android-youtube-test','LAB_011_FAILOVER','it.geovision.lab.failover011','2011','LAB 011 FAILOVER','out/LAB_011_FAILOVER.html')
]
for folder,name,package,version,label,html in items:
 p=Path(folder+'/app/build/outputs/apk/debug/app-debug.apk');assert p.is_file(),p
 cert=subprocess.check_output([str(bt/'apksigner'),'verify','--print-certs',str(p)],text=True)
 assert '716c1a8a139ad956ef8a00f85f153eb0028d109c75b1b938bdf3bb3eb23c22b5' in cert
 badging=subprocess.check_output([str(bt/'aapt'),'dump','badging',str(p)],text=True)
 assert "package: name='"+package+"'" in badging,badging[:500]
 assert "versionCode='"+version+"'" in badging,badging[:500]
 assert "application-label:'"+label+"'" in badging,badging[:1000]
 if html:
  with zipfile.ZipFile(p) as z: assert z.read('assets/geovision.html')==Path(html).read_bytes()
 Path('out/'+name+'.apk').write_bytes(p.read_bytes())
 print(name,package,version,hashlib.sha256(p.read_bytes()).hexdigest())
PY
