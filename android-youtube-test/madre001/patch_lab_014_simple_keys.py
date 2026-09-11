from pathlib import Path
p=Path('android-youtube-test/app/src/main/assets/geovision.html')
s=p.read_text(encoding='utf-8')
js=r'''
<script id="gv-simple-keys-014">
(function(){
'use strict';
const ITEMS=[
 ['google1','Google 1','geovision_google_maps_api_key_1'],
 ['google2','Google 2','geovision_google_maps_api_key_2'],
 ['google3','Google 3','geovision_google_maps_api_key_3'],
 ['ai','Intelligenza artificiale','geovision_ai_api_key'],
 ['youtube','YouTube','geovision_youtube_api_key']
];
const K=n=>'gv_simple_014_'+n;
const E=n=>'gv_simple_014_enabled_'+n;
let panel=null;
function saved(n,legacy){return localStorage.getItem(K(n)) ?? localStorage.getItem(legacy) ?? '';}
function enabled(n){const v=localStorage.getItem(E(n));return v===null?true:v==='1';}
function setEnabled(n,v){localStorage.setItem(E(n),v?'1':'0');}
function apply(){
 const vals={}; ITEMS.forEach(([n,l,k])=>vals[n]=saved(n,k));
 for(let i=0;i<3;i++){const n='google'+(i+1),k='geovision_google_maps_api_key_'+(i+1);if(enabled(n)&&vals[n])localStorage.setItem(k,vals[n]);else localStorage.removeItem(k);}
 const pool=[];let active=-1;
 for(let i=0;i<3;i++){const n='google'+(i+1);if(enabled(n)&&vals[n]){pool.push(vals[n]);if(active<0)active=i;}}
 localStorage.setItem('geovision_google_maps_api_keys',JSON.stringify(pool));
 if(active>=0){localStorage.setItem('geovision_google_active_key_index',String(active));localStorage.setItem('geovision_google_maps_api_key',vals['google'+(active+1)]);}else{localStorage.removeItem('geovision_google_maps_api_key');}
 for(const n of ['ai','youtube']){const k=n==='ai'?'geovision_ai_api_key':'geovision_youtube_api_key';if(enabled(n)&&vals[n])localStorage.setItem(k,vals[n]);else localStorage.removeItem(k);}
}
async function verify(n,key){
 if(!key)return false;
 const c=new AbortController(),t=setTimeout(()=>c.abort(),6000);
 try{
  let r;
  if(n.startsWith('google')) r=await fetch('https://places.googleapis.com/v1/places:searchText',{method:'POST',signal:c.signal,headers:{'Content-Type':'application/json','X-Goog-Api-Key':key,'X-Goog-FieldMask':'places.id'},body:JSON.stringify({textQuery:'Salerno',pageSize:1})});
  else if(n==='ai') r=await fetch('https://generativelanguage.googleapis.com/v1beta/models',{signal:c.signal,headers:{'x-goog-api-key':key}});
  else r=await fetch('https://www.googleapis.com/youtube/v3/videos?part=id&id=S0Q4_88y&key='+encodeURIComponent(key),{signal:c.signal});
  return !!r.ok;
 }catch(e){return false;}finally{clearTimeout(t);}
}
function updateActive(){if(!panel)return;let a=-1;for(let i=0;i<3;i++){const n='google'+(i+1);if(enabled(n)&&saved(n,'geovision_google_maps_api_key_'+(i+1))){a=i;break;}}
 panel.querySelectorAll('[data-n^="google"] .sub').forEach((e,i)=>{e.textContent=enabled('google'+(i+1))?(i===a?'ON · ATTIVA':'ON'):'OFF';});
}
async function verifyAll(){if(!panel)return;for(const [n,l,k] of ITEMS){const row=panel.querySelector('[data-n="'+n+'"]'),dot=row?.querySelector('.dot'),sub=row?.querySelector('.sub');if(!dot)continue;dot.className='dot wait';const ok=await verify(n,saved(n,k));if(!panel)return;dot.className='dot '+(ok?'ok':'bad');if(n.startsWith('google'))sub.textContent=(enabled(n)?'ON':'OFF')+' · '+(ok?'funziona':'non disponibile');else sub.textContent=(enabled(n)?'ON':'OFF')+' · '+(ok?'funziona':'non disponibile');}updateActive();}
function close(){if(panel){panel.remove();panel=null;}}
function open(){close();panel=document.createElement('div');panel.id='gvSimple014';panel.innerHTML=`<div class="box"><div class="head"><b>Chiavi API</b><button id="skClose">×</button></div><div class="hint">KeyBox serve solo per importare. Nessuno switch automatico.</div><div id="skRows"></div><button id="skImport" class="wide">Importa da KeyBox</button><button id="skVerify" class="wide">Verifica chiavi</button><button id="skSave" class="wide primary">Salva e applica</button><div id="skState"></div></div>`;
 const css=document.createElement('style');css.textContent=`#gvSimple014{position:fixed;inset:0;z-index:2147483647;background:#0007;display:flex;align-items:center;justify-content:center;padding:14px;font-family:Arial,sans-serif}#gvSimple014 .box{width:min(430px,100%);max-height:90vh;overflow:auto;background:#fff;border-radius:18px;padding:16px;box-shadow:0 14px 44px #0004}#gvSimple014 .head{display:flex;justify-content:space-between;align-items:center;font-size:22px}#gvSimple014 .head button{border:0;background:#eef2f7;border-radius:50%;width:34px;height:34px;font-size:23px}#gvSimple014 .hint{font-size:12px;color:#64748b;margin:6px 0 12px}.skrow{border:1px solid #dbe3ee;border-radius:13px;padding:10px;margin:8px 0}.skline{display:flex;align-items:center;gap:9px}.dot{width:13px;height:13px;border-radius:50%;background:#94a3b8;flex:none}.dot.ok{background:#16a34a}.dot.bad{background:#dc2626}.dot.wait{background:#94a3b8}.title{font-weight:800;flex:1}.sub{font-size:11px;color:#64748b;margin-top:2px}.sw{display:flex;align-items:center;gap:5px;font-weight:700;font-size:12px}.skrow input[type=password]{box-sizing:border-box;width:100%;margin-top:8px;padding:10px;border:1px solid #cbd5e1;border-radius:9px}.wide{width:100%;padding:11px;margin-top:8px;border:1px solid #cbd5e1;border-radius:11px;background:#f8fafc;font-weight:800}.primary{background:#2563eb;color:#fff;border-color:#2563eb}#skState{font-size:12px;color:#475569;margin-top:8px}`;panel.appendChild(css);
 const rows=panel.querySelector('#skRows');ITEMS.forEach(([n,l,k])=>{const r=document.createElement('div');r.className='skrow';r.dataset.n=n;r.innerHTML=`<div class="skline"><span class="dot wait"></span><div class="title">${l}<div class="sub">${enabled(n)?'ON':'OFF'}</div></div><label class="sw"><input type="checkbox" ${enabled(n)?'checked':''}> ON</label></div><input type="password" autocomplete="off">`;r.querySelector('input[type=password]').value=saved(n,k);r.querySelector('input[type=checkbox]').onchange=e=>{setEnabled(n,e.target.checked);updateActive();};rows.appendChild(r);});
 document.body.appendChild(panel);panel.querySelector('#skClose').onclick=close;panel.onclick=e=>{if(e.target===panel)close();};panel.querySelector('#skImport').onclick=()=>{const st=panel.querySelector('#skState');if(!window.GeoVisionKeyBox?.importKeys){st.textContent='KeyBox non disponibile';return;}st.textContent='Importazione…';window.GeoVisionKeyBox.importKeys();};panel.querySelector('#skVerify').onclick=verifyAll;panel.querySelector('#skSave').onclick=()=>{ITEMS.forEach(([n,l,k])=>{const row=panel.querySelector('[data-n="'+n+'"]');localStorage.setItem(K(n),row.querySelector('input[type=password]').value.trim());setEnabled(n,row.querySelector('input[type=checkbox]').checked);});apply();panel.querySelector('#skState').textContent='Salvato. Applico…';setTimeout(()=>location.reload(),250);};updateActive();verifyAll();}
window.gvKeyBoxError=function(m){if(panel)panel.querySelector('#skState').textContent=m||'KeyBox non disponibile';};
window.gvReceiveKeyBox=function(keys){try{ITEMS.forEach(([n,l,k])=>{const v=String(keys?.[n]||'').trim();localStorage.setItem(K(n),v);if(localStorage.getItem(E(n))===null)setEnabled(n,true);});apply();if(panel){ITEMS.forEach(([n,l,k])=>{panel.querySelector('[data-n="'+n+'"] input[type=password]').value=saved(n,k);});panel.querySelector('#skState').textContent='Chiavi importate';verifyAll();}}catch(e){window.gvKeyBoxError('Errore importazione');}};
window.gvSimpleKeyPanelOpen=open;
try{window.gvDiagAdvanceGoogleKey=function(){return false;};window.gm_authFailure=function(){try{setGoogleKeyState('error');}catch(e){}};}catch(e){}
function hook(){for(const id of ['keyStatus','mapsSetup','mapsSave']){const e=document.getElementById(id);if(e)e.onclick=open;}}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',hook);else hook();
apply();
})();
</script>
'''
s=s.replace('</body>',js+'\n</body>',1)
p.write_text(s,encoding='utf-8')
