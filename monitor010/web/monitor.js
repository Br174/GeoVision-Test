(function(){
'use strict';
const state=GVKeyState.create(localStorage),names=GVKeyState.NAMES,labels=['Google 1','Google 2','Google 3','Intelligenza artificiale','YouTube'];
const GOOGLE_RUNTIME='geovision_google_runtime_status_v2';
let panel=null,busy=false,importTimer=0;const results={};
function status(t){const e=document.getElementById('gvMonitorStatus');if(e)e.textContent=t;}
function runtime(){try{return JSON.parse(localStorage.getItem(GOOGLE_RUNTIME)||'{}')||{};}catch{return {};}}
function googleRuntime(i){const r=runtime()[String(i)];return r&&typeof r==='object'?r:null;}
function refresh(){
 if(!panel)return;
 const keys=state.read(),a=state.active(),en=state.enabled();
 names.forEach((n,i)=>{
  const row=panel.querySelector('[data-name="'+n+'"]');if(!row)return;
  const off=i<3&&!en[i],missing=!keys[n];let r=null,text='',dot='unknown';
  if(i<3){
   r=googleRuntime(i);
   if(off){text='OFF manuale · esclusa da uso e failover';dot='unknown';}
   else if(missing){text='Chiave assente';dot='bad';}
   else if(r){dot=r.ok?'ok':'bad';text=(i===a.idx?'ATTIVA · ':'')+(r.text||'Stato Google aggiornato durante l’uso');}
   else{text=i===a.idx?'ATTIVA · attende uso reale':'ON · disponibile · attende uso reale';dot='unknown';}
  }else{
   r=results[n];
   if(missing){text='Chiave assente';dot='bad';}
   else if(r){text=r.text;dot=r.ok?'ok':'bad';}
   else{text='Configurata · da verificare';dot='unknown';}
  }
  row.querySelector('.dot').dataset.state=dot;row.querySelector('.state').textContent=text;
  const sw=row.querySelector('.gv-key-toggle');if(sw)sw.checked=en[i];
 });
 panel.querySelector('#gvApplyPending').hidden=!state.pending();
}
function receive(k){clearTimeout(importTimer);try{const changed=state.stage(k);status(changed?'Chiavi ricevute. Premi Applica per attivarle.':'Chiavi già aggiornate.');refresh();}catch(e){status(e.message);}const b=document.getElementById('gvImport');if(b)b.disabled=false;}
window.gvReceiveKeyBox=receive;
window.gvKeyBoxError=function(t){clearTimeout(importTimer);status(t||'KeyBox non disponibile');const b=document.getElementById('gvImport');if(b)b.disabled=false;};
window.gvMonitorSync=receive;
function close(){if(!panel)return;panel.remove();panel=null;}
function open(){
 close();panel=document.createElement('div');panel.id='gvMonitor';panel.setAttribute('role','dialog');panel.setAttribute('aria-modal','true');panel.setAttribute('aria-label','Monitor API');
 panel.innerHTML='<section class="monitor-card"><header><div><div class="eyebrow">GEOVISION · LAB 012</div><h2>Monitor API</h2></div><button class="close" aria-label="Chiudi">×</button></header><p class="note">Google viene verificato durante l’uso reale di schede, ricerca e foto. Verde: ultima richiesta riuscita. Rosso: ultimo errore reale. Grigio: non ancora verificata o OFF. Gli interruttori Google hanno priorità assoluta.</p><div id="gvApiRows"></div><div class="actions"><button id="gvImport">Importa da KeyBox</button><button id="gvTest">Verifica AI / YouTube</button></div><button id="gvSave" class="primary wide">Salva in questa GeoVision</button><label class="sync"><input id="gvAutoSync" type="checkbox">Ricevi aggiornamenti da KeyBox</label><button id="gvApplyPending" class="primary wide" hidden>Applica chiavi ricevute</button><div id="gvMonitorStatus" role="status" aria-live="polite"></div></section>';
 const keys=state.read(),en=state.enabled();
 names.forEach((n,i)=>{const row=document.createElement('div');row.className='row';row.dataset.name=n;const toggle=i<3?'<label class="key-switch"><input class="gv-key-toggle" type="checkbox" aria-label="'+labels[i]+' attiva"><span>ON</span></label>':'';row.innerHTML='<div class="row-head"><span class="dot"></span><div class="row-title"><label for="gvKey'+i+'"><b>'+labels[i]+'</b></label><div class="state"></div></div>'+toggle+'</div><input type="password" id="gvKey'+i+'" autocomplete="off" spellcheck="false" aria-label="'+labels[i]+'">';row.querySelector('input[type=password]').value=keys[n];if(i<3){const sw=row.querySelector('.gv-key-toggle');sw.checked=en[i];sw.onchange=()=>{state.setEnabled(i,sw.checked);status(labels[i]+' '+(sw.checked?'ON':'OFF')+'.');window.GeoVisionKeyBox?.setGoogleEnabled?.(i,sw.checked);refresh();};}panel.querySelector('#gvApiRows').appendChild(row);});
 document.body.appendChild(panel);panel.querySelector('.close').onclick=close;panel.onclick=e=>{if(e.target===panel)close();};panel.onkeydown=e=>{if(e.key==='Escape')close();};
 panel.querySelector('#gvSave').onclick=()=>{try{const k={revision:0,googleEnabled:state.enabled()};names.forEach((n,i)=>k[n]=panel.querySelector('#gvKey'+i).value);const changed=state.apply(k);localStorage.removeItem('geovision_keys_pending_v1');status(changed?'Chiavi salvate.':'Nessuna modifica.');refresh();}catch(e){status(e.message);}};
 panel.querySelector('#gvImport').onclick=()=>{const b=panel.querySelector('#gvImport');if(!window.GeoVisionKeyBox?.importKeys)return status('KeyBox disponibile nell’app Android.');b.disabled=true;status('Importazione in corso…');importTimer=setTimeout(()=>window.gvKeyBoxError('KeyBox non risponde. Puoi riprovare.'),10000);try{window.GeoVisionKeyBox.importKeys();}catch{window.gvKeyBoxError('Importazione non disponibile');}};
 const auto=panel.querySelector('#gvAutoSync');auto.checked=localStorage.getItem('geovision_auto_sync')==='1';auto.onchange=()=>{localStorage.setItem('geovision_auto_sync',auto.checked?'1':'0');window.GeoVisionKeyBox?.setSyncEnabled?.(auto.checked);};
 panel.querySelector('#gvApplyPending').onclick=()=>{try{state.commitPending();refresh();status('Chiavi KeyBox applicate.');}catch(e){status(e.message);}};
 panel.querySelector('#gvTest').onclick=test;
 refresh();panel.querySelector('.close').focus();
}
async function check(name,key){
 if(!key)return {ok:false,text:'Chiave assente'};
 const ctrl=new AbortController(),timer=setTimeout(()=>ctrl.abort(),8000);
 try{let url,options={signal:ctrl.signal};if(name==='ai'){url='https://generativelanguage.googleapis.com/v1beta/models';options.headers={'x-goog-api-key':key};}else if(name==='youtube'){url='https://www.googleapis.com/youtube/v3/videos?part=id&id=S0Q4_88y&key='+encodeURIComponent(key);}else return {ok:false,text:'Google: verifica durante uso reale'};const r=await fetch(url,options);let detail='';if(!r.ok){try{const j=await r.clone().json();detail=j?.error?.status||j?.error?.message||'';}catch{}}return {ok:r.ok,text:r.ok?(name==='ai'?'Accesso API Gemini verificato':'Accesso API YouTube verificato'):'Verifica fallita · HTTP '+r.status+(detail?' · '+detail:'')};}catch{return {ok:false,text:'Non verificabile · rete, CORS o timeout'};}finally{clearTimeout(timer);}
}
async function test(){if(busy)return;busy=true;const b=panel?.querySelector('#gvTest');if(b)b.disabled=true;status('Verifico AI e YouTube…');try{const k=state.read();results.ai=await check('ai',k.ai);results.youtube=await check('youtube',k.youtube);refresh();status('AI e YouTube verificati. Google si aggiorna durante l’uso reale.');}finally{busy=false;if(b)b.disabled=false;}}
window.addEventListener('gv-google-runtime',()=>refresh());
window.GVMonitor={open,close,check,receive,refresh};window.GeoVisionKeyBox?.pageReady?.();
})();
