#!/usr/bin/env bash
set -euo pipefail
python monitor010/prepare.py
node --test monitor010/tests/key-state.test.js
python monitor010/tests/static.py
gradle -p android-keybox assembleDebug assembleDebugAndroidTest lintDebug
gradle -p android-youtube-test assembleDebug assembleDebugAndroidTest lintDebug
python - <<'PY'
from pathlib import Path
import zipfile,hashlib,subprocess,os
sdk=Path(os.environ['ANDROID_HOME']);bt=sorted((sdk/'build-tools').iterdir())[-1]
for folder,name,package in [('android-keybox','KEYBOX_007_MONITOR','it.geovision.keybox'),('android-youtube-test','LAB_010_MONITOR_SYNC','it.geovision.lab.monitor010')]:
 p=Path(folder+'/app/build/outputs/apk/debug/app-debug.apk')
 cert=subprocess.check_output([str(bt/'apksigner'),'verify','--print-certs',str(p)],text=True)
 assert '716c1a8a139ad956ef8a00f85f153eb0028d109c75b1b938bdf3bb3eb23c22b5' in cert
 badging=subprocess.check_output([str(bt/'aapt'),'dump','badging',str(p)],text=True)
 assert "package: name='"+package+"'" in badging
 if folder=='android-youtube-test':
  with zipfile.ZipFile(p) as z: assert z.read('assets/geovision.html')==Path('out/LAB_010_MONITOR_SYNC.html').read_bytes()
 Path('out/'+name+'.apk').write_bytes(p.read_bytes())
 print(name,package,hashlib.sha256(p.read_bytes()).hexdigest())
PY
