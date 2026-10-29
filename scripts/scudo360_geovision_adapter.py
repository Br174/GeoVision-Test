#!/usr/bin/env python3
"""Execute existing GeoVision regression checks and emit truthful JUnit proof."""
import re
import subprocess
import sys
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parents[1]
out = ROOT / '.motorlab' / 'scudo360-test-results'
out.mkdir(parents=True, exist_ok=True)
proc = subprocess.run([sys.executable, 'tests/test_geovision.py'], cwd=ROOT,
                      capture_output=True, text=True, timeout=90, check=False)
combined = proc.stdout + '\n' + proc.stderr
matches = re.findall(r'^(PASS|FAIL)  (.+)$', proc.stdout, flags=re.MULTILINE)
checks = {name:status for status,name in matches}
required = ('doctype HTML','nessun ID DOM duplicato','controlli UI essenziali',
            'nessuna chiave Google incorporata','nessuna chiave Gemini incorporata',
            'sintassi JavaScript')
missing = [name for name in required if checks.get(name) != 'PASS']
valid = proc.returncode == 0 and len(matches) >= 25 and not missing and all(st=='PASS' for st,_ in matches)
errors = 0 if valid else 1
detail = escape(combined[-1800:])
xml = ('<?xml version="1.0" encoding="UTF-8"?>\n'
       '<testsuite name="geo.GeovisionStatic" tests="%d" failures="%d" errors="0" skipped="0">'
       '<testcase classname="geo.GeovisionStatic" name="complete-static-verification">%s</testcase>'
       '</testsuite>\n') % (
           max(len(matches),1),errors,('<failure message="Static tests failed">' + detail + '</failure>') if errors else '')
(out/'TEST-geo.GeovisionStatic.xml').write_text(xml,encoding='utf-8')
print(combined[-5000:])
print('SCUDO_GEO_STATIC_PASSED',valid,'executed',len(matches),'missing',missing)
sys.exit(0 if valid else 1)
