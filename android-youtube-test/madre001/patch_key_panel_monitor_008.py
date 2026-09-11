from pathlib import Path

p=Path('/tmp/GeoVision_MADRE_001_SOURCE.html')
s=p.read_text(encoding='utf-8')

marker='''function openKeysDiagnostics(){'''
if marker not in s:
    raise SystemExit('openKeysDiagnostics anchor missing')

# Inject styling helper before diagnostics function. Pure panel/UI + live status tests; no Google card changes.
insert=r'''
function gv008KeyStateRow(label, id, sub){
  return `<div style="display:flex;align-items:center;gap:10px;margin-top:12px"><span id="${id}Dot" style="font-size:24px;line-height:1;color:#ef4444">●</span><div style="flex:1"><div style="font-weight:800;color:#1e293b">${label}</div><div id="${id}Status" style="font-size:12px;color:#64748b;margin-top:2px">${sub||'Da verificare'}</div></div></div>`;
}
function gv008SetStatus(id, ok, text){
  const d=document.getElementById(id+'Dot'), st=document.getElementById(id+'Status');
  if(d) d.style.color=ok?'#22c55e':'#ef4444';
  if(st){st.textContent=text||'';st.style.color=ok?'#166534':'#991b1b';}
}
async function gv008TestGemini(key){
  if(!key){gv008SetStatus('gv008Ai',false,'INATTIVA · chiave assente');return false;}
  gv008SetStatus('gv008Ai',false,'Verifica in corso…');
  try{
    const r=await fetch(`https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=${encodeURIComponent(key)}`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({contents:[{parts:[{text:'Rispondi solo con OK'}]}],generationConfig:{maxOutputTokens:8}})});
    gv008SetStatus('gv008Ai',r.ok,r.ok?'ATTIVA · Gemini operativo':`INATTIVA · errore ${r.status}`);return r.ok;
  }catch(e){gv008SetStatus('gv008Ai',false,'INATTIVA · non raggiungibile');return false;}
}
async function gv008TestYoutube(key){
  if(!key){gv008SetStatus('gv008Yt',false,'INATTIVA · chiave assente');return false;}
  gv008SetStatus('gv008Yt',false,'Verifica in corso…');
  try{
    const r=await fetch(`https://www.googleapis.com/youtube/v3/search?part=snippet&type=video&maxResults=1&q=GeoVision&key=${encodeURIComponent(key)}`);
    gv008SetStatus('gv008Yt',r.ok,r.ok?'ATTIVA · YouTube Data API operativa':`INATTIVA · errore ${r.status}`);return r.ok;
  }catch(e){gv008SetStatus('gv008Yt',false,'INATTIVA · non raggiungibile');return false;}
}
function gv008DecorateKeyPanel(){
  const panel=document.getElementById('keysDiagnosticsPanel') || document.querySelector('[data-role="keys-diagnostics"]');
  const host=panel?.querySelector('.panel-card')||panel?.firstElementChild||panel;
  if(!host || document.getElementById('gv008MonitorBlock')) return;
  host.style.borderRadius='24px';host.style.boxShadow='0 18px 55px #0f172a24';host.style.border='1px solid #e2e8f0';host.style.background='#fff';
  const box=document.createElement('div');box.id='gv008MonitorBlock';box.style.cssText='margin:14px 0;padding:14px;border:1px solid #e2e8f0;border-radius:18px;background:#f8fafc';
  const pool=(typeof gvDiagLoadGoogleKeyPool==='function')?gvDiagLoadGoogleKeyPool():{keys:[localStorage.getItem('geovision_google_maps_api_key_1')||'',localStorage.getItem('geovision_google_maps_api_key_2')||'',localStorage.getItem('geovision_google_maps_api_key_3')||''],idx:parseInt(localStorage.getItem('geovision_google_active_key_index')||'0',10)||0};
  box.innerHTML='<div style="font-size:17px;font-weight:900;color:#0f172a">Monitor chiavi API</div><div style="font-size:12px;color:#64748b;margin-top:3px">Stessa impostazione grafica del KeyBox Monitor; funzioni del pannello GeoVision restano invariate.</div>'+
    gv008KeyStateRow('Google Maps API 1','gv008G1','')+gv008KeyStateRow('Google Maps API 2','gv008G2','')+gv008KeyStateRow('Google Maps API 3','gv008G3','')+gv008KeyStateRow('API Intelligenza Artificiale','gv008Ai','')+gv008KeyStateRow('YouTube Data API','gv008Yt','');
  host.insertBefore(box,host.firstChild);
  for(let i=0;i<3;i++){const has=!!String(pool.keys?.[i]||'').trim(), active=has && i===pool.idx;gv008SetStatus('gv008G'+(i+1),active,active?'ATTIVA ORA · chiave Google selezionata':(has?'INATTIVA · disponibile':'INATTIVA · chiave assente'));}
  const ai=(document.getElementById('geminiKey')?.value||localStorage.getItem('geovision_ai_api_key')||window.geminiKey||'').trim();
  const yt=(document.getElementById('youtubeKey')?.value||localStorage.getItem('geovision_youtube_api_key')||window.youtubeKey||'').trim();
  gv008TestGemini(ai); gv008TestYoutube(yt);
}
'''
s=s.replace(marker,insert+'\n'+marker,1)

# Hook after panel opening without altering its original actions.
needle='''$('#keysDiagnosticsOpen').onclick=openKeysDiagnostics;'''
if needle in s:
    s=s.replace(needle,"$('#keysDiagnosticsOpen').onclick=()=>{openKeysDiagnostics();setTimeout(gv008DecorateKeyPanel,0);};",1)
else:
    # fallback: wrap function itself after definition via observer-free call site search
    s=s.replace('''openKeysDiagnostics();''','''openKeysDiagnostics(); setTimeout(gv008DecorateKeyPanel,0);''',1)

assert 'gv008MonitorBlock' in s
assert 'gv008TestGemini' in s
assert 'gv008TestYoutube' in s
p.write_text(s,encoding='utf-8')
print('LAB008 key panel monitor patched',p.stat().st_size)
