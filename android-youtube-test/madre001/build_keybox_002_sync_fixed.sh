#!/usr/bin/env bash
set -euo pipefail
SCRIPT='android-youtube-test/madre001/build_keybox_002_sync.sh'
python - <<'PY'
from pathlib import Path
p=Path('android-youtube-test/madre001/build_keybox_002_sync.sh')
s=p.read_text()
s=s.replace('rm -rf "$APP/src/main/java/it/geovision/keybox"\nmkdir -p "$APP/src/main/java/it/geovision/keybox"','rm -rf "$APP/src/main/java/it"\nmkdir -p "$APP/src/main/java/it/geovision/keybox"',1)
p.write_text(s)
PY
bash "$SCRIPT"
