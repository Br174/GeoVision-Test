from pathlib import Path
import os

mode = os.environ.get('GV_PROBE_MODE','A').strip().upper()
if mode not in {'A','B','C','ISO'}:
    raise SystemExit('Unsupported GV_PROBE_MODE: '+mode)

p = Path('android-youtube-test/app/src/main/assets/geovision.html')
s = p.read_text(encoding='utf-8')
marker='GV_STORAGE_ISOLATION_PROBE_20260910'
if marker in s:
    raise SystemExit('Probe already present')

write_marker = 'true' if mode == 'B' else 'false'
html = f'''
<!-- {marker} -->
<style>
#gvStorageProbe{{position:fixed;z-index:70000;left:12px;right:12px;top:12px;background:#fff;border:2px solid #111827;border-radius:18px;padding:12px 14px;font:13px/1.45 system-ui;color:#111827;box-shadow:0 8px 30px rgba(0,0,0,.18)}}
#gvStorageProbe b{{font-size:16px}}#gvStorageProbe .ok{{color:#16803b;font-weight:800}}#gvStorageProbe .bad{{color:#b42318;font-weight:800}}#gvStorageProbe small{{display:block;color:#667085;margin-top:5px}}
</style>
<div id="gvStorageProbe"><b>TEST ISOLAMENTO ANDROID · {mode}</b><div id="gvStorageProbeState">Avvio…</div><small>Chiave test: gv_storage_isolation_proof_20260910_v1</small></div>
<script>
(function(){{
 const KEY='gv_storage_isolation_proof_20260910_v1';
 const MODE='{mode}';
 const WRITE={write_marker};
 const out=document.getElementById('gvStorageProbeState');
 let before='';
 try{{before=localStorage.getItem(KEY)||'';}}catch(e){{out.innerHTML='<span class="bad">ERRORE localStorage</span><br>'+String(e);return;}}
 if(WRITE){{
   try{{localStorage.setItem(KEY,'CONTAMINATO_DA_B');}}catch(e){{out.innerHTML='<span class="bad">ERRORE SCRITTURA</span><br>'+String(e);return;}}
   out.innerHTML='Prima: '+(before||'PULITO')+'<br><span class="bad">B ha scritto: CONTAMINATO_DA_B</span>';
 }}else{{
   const now=localStorage.getItem(KEY)||'';
   if(now) out.innerHTML='<span class="bad">STATO EREDITATO: '+now+'</span>';
   else out.innerHTML='<span class="ok">AMBIENTE PULITO</span>';
 }}
}})();
</script>
'''
if '</body>' not in s:
    raise SystemExit('Missing </body>')
s=s.replace('</body>',html+'\n</body>',1)
p.write_text(s,encoding='utf-8')
print('Applied storage probe mode',mode,'bytes',len(s.encode('utf-8')))
