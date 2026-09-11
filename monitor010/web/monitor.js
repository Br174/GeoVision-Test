(function(){
'use strict';
const state=GVKeyState.create(localStorage),names=GVKeyState.NAMES,labels=['Google 1','Google 2','Google 3','Intelligenza artificiale','YouTube'];
let panel=null,busy=false,reloadScheduled=false,importTimer=0;const results={};
function status(t){const e=document.getElementById('gvMonitorStatus');if(e)e.textContent=t;}
function refresh(){if(!panel)return;const keys=state.read(),idx=Number(localStorage.getItem('geovision_google_active_key_index')||0);names.forEach((n,i)=>{const row=panel.querySelector('[data-name="'+n+'"]'),r=results[n];row.querySelector('.dot').dataset.state=r?(r.ok?'ok':'bad'):keys[n]?'unknown':'bad';row.querySelector('.state').textContent=r?r.text:!keys[n]?'Chiave assente':i<3&&i===idx?'Selezionata · servizio da verificare':'Configurata · servizio da verificare';});panel.querySelector('#gvApplyPending').hidden=!state.pending();}
function scheduleReload(){if(reloadScheduled)return;reloadScheduled=true;setTimeout(()=>location.reload(),150);}
function receive(k){clearTimeout(importTimer);try{const changed=state.stage(k);status(changed?'Chiavi ricevute. Premi Applica per attivarle.':'Chiavi già aggiornate.');refresh();}catch(e){status(e.message);}const b=document.getElementById('gvImport');if(b)b.disabled=false;}
window.gvReceiveKeyBox=receive;
window.gvKeyBoxError=function(t){clearTimeout(importTimer);status(t||'KeyBox non disponibile');const b=document.getElementById('gvImport');if(b)b.disabled=false;};
window.gvMonitorSync=receive;
function close(){if(!panel)return;panel.remove();panel=null;}
function open(){
 close();panel=document.createElement('div');panel.id='gvMonitor';panel.setAttribute('role','dialog');panel.setAttribute('aria-modal','true');panel.setAttribute('aria-label','Monitor API');
 panel.innerHTML='<section class="monitor-card"><header><div><div class="eyebrow">GEOVISION · LAB 010</div><h2>Monitor API</h2></div><button class="close" aria-label="Chiudi">×</button></header><p class="note">Verde: verifica riuscita. Rosso: errore o chiave assente. Grigio: da verificare.</p><div id="gvApiRows"></div><div class="actions"><button id="gvImport">Importa da KeyBox</button><button id="gvTest">Verifica API</button></div><button id="gvSave" class="primary wide">Salva in questa GeoVision</button><label class="sync"><input id="gvAutoSync" type="checkbox">Ricevi aggiornamenti da KeyBox</label><p class="note">Le nuove chiavi si attivano al prossimo avvio o premendo Applica. Le schede aperte continuano a funzionare.</p><button id="gvApplyPending" class="primary wide" hidden>Applica chiavi ricevute e riavvia</button><div id="gvMonitorStatus" role="status" aria-live="polite"></div><button id="gvGoogleDetails" class="wide">Diagnostica schede e foto Google</button><div id="googleDiagRows"></div></section>';
 const keys=state.read();names.forEach((n,i)=>{const row=document.createElement('div');row.className='row';row.dataset.name=n;row.innerHTML='<div class="row-head"><span class="dot"></span><div><label for="gvKey'+i+'"><b>'+labels[i]+'</b></label><div class="state"></div></div></div><input type="password" id="gvKey'+i+'" autocomplete="off" spellcheck="false" aria-label="'+labels[i]+'">';row.querySelector('input').value=keys[n];panel.querySelector('#gvApiRows').appendChild(row);});
 document.body.appendChild(panel);panel.querySelector('.close').onclick=close;panel.onclick=e=>{if(e.target===panel)close();};panel.onkeydown=e=>{if(e.key==='Escape')close();};
 panel.querySelector('#gvSave').onclick=()=>{try{const k={revision:0};names.forEach((n,i)=>k[n]=panel.querySelector('#gvKey'+i).value);const changed=state.apply(k);localStorage.removeItem('geovision_keys_pending_v1');status(changed?'Chiavi salvate. Riavvio…':'Nessuna modifica.');if(changed)scheduleReload();}catch(e){status(e.message);}};
 panel.querySelector('#gvImport').onclick=()=>{const b=panel.querySelector('#gvImport');if(!window.GeoVisionKeyBox?.importKeys)return status('KeyBox disponibile nell’app Android.');b.disabled=true;status('Importazione in corso…');importTimer=setTimeout(()=>window.gvKeyBoxError('KeyBox non risponde. Puoi riprovare.'),10000);try{window.GeoVisionKeyBox.importKeys();}catch{window.gvKeyBoxError('Importazione non disponibile');}};
 const auto=panel.querySelector('#gvAutoSync');auto.checked=localStorage.getItem('geovision_auto_sync')==='1';auto.onchange=()=>{localStorage.setItem('geovision_auto_sync',auto.checked?'1':'0');window.GeoVisionKeyBox?.setSyncEnabled?.(auto.checked);};
 panel.querySelector('#gvApplyPending').onclick=()=>{try{const changed=state.commitPending();if(changed)scheduleReload();else refresh();}catch(e){status(e.message);}};
 panel.querySelector('#gvTest').onclick=test;
 panel.querySelector('#gvGoogleDetails').onclick=async()=>{const b=panel.querySelector('#gvGoogleDetails');b.disabled=true;panel.querySelector('#googleDiagRows').textContent='';try{await window.gvMonitorGoogleDiagnostics();}catch{status('Diagnostica Google non disponibile.');}finally{b.disabled=false;}};
 refresh();panel.querySelector('.close').focus();
}
async function check(name,key){
 if(!key)return {ok:false,text:'Chiave assente'};
 const ctrl=new AbortController(),timer=setTimeout(()=>ctrl.abort(),8000);
 try{
  let url,options={signal:ctrl.signal};
  if(name.startsWith('google')){url='https://places.googleapis.com/v1/places:searchText';options={...options,method:'POST',headers:{'Content-Type':'application/json','X-Goog-Api-Key':key,'X-Goog-FieldMask':'places.id'},body:JSON.stringify({textQuery:'Salerno',pageSize:1})};}
  else if(name==='ai'){url='https://generativelanguage.googleapis.com/v1beta/models';options.headers={'x-goog-api-key':key};}
  else url='https://www.googleapis.com/youtube/v3/videos?part=id&id=S0Q4_88y&key='+encodeURIComponent(key);
  const r=await fetch(url,options);return {ok:r.ok,text:r.ok?(name==='ai'?'Accesso API Gemini verificato':name==='youtube'?'Accesso API YouTube verificato':'Places REST verificata · Maps JS separata'):'Verifica fallita · HTTP '+r.status};
 }catch{return {ok:false,text:'Non verificabile · rete, CORS o timeout'};}finally{clearTimeout(timer);}
}
async function test(){if(busy)return;busy=true;const b=panel?.querySelector('#gvTest');if(b)b.disabled=true;status('Verifico le cinque API…');try{const k=state.read();await Promise.all(names.map(async n=>{results[n]=await check(n,k[n]);}));refresh();status('Verifica terminata. I test non cambiano la chiave selezionata.');}finally{busy=false;if(b)b.disabled=false;}}
window.GVMonitor={open,close,check,receive};
// The bridge is notified only after the actual receiving functions exist.
window.GeoVisionKeyBox?.pageReady?.();
})();
