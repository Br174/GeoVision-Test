/* GeoVision key state: snapshots, manual Google ON/OFF, bounded failover. */
(function(root){
'use strict';
const NAMES=['google1','google2','google3','ai','youtube'];
const SNAP='geovision_keys_snapshot_v1',PENDING='geovision_keys_pending_v1',ENABLED='geovision_google_enabled_v1';
function bool3(v){const a=Array.isArray(v)?v:[true,true,true];return [0,1,2].map(i=>a[i]!==false);}
function validate(value){
 if(!value||typeof value!=='object'||Array.isArray(value))throw Error('Dati KeyBox non validi');
 const keys={};for(const n of NAMES){if(typeof value[n]!=='string'||value[n].length>512||/[\r\n\x00]/.test(value[n]))throw Error('Formato chiavi non valido');keys[n]=value[n].trim();}
 if(!Object.values(keys).some(Boolean))throw Error('KeyBox vuoto: chiavi locali conservate');
 const revision=value.revision===undefined?0:value.revision;if(!Number.isSafeInteger(revision)||revision<0)throw Error('Revisione non valida');
 const enabled=bool3(value.googleEnabled!==undefined?value.googleEnabled:[value.google1Enabled,value.google2Enabled,value.google3Enabled]);
 return {...keys,revision,googleEnabled:enabled};
}
function create(storage){
 const get=k=>storage.getItem(k),json=(k,f)=>{try{const v=JSON.parse(get(k));return v==null?f:v;}catch{return f;}};
 function read(){
  const saved=json(SNAP,null);if(saved){const v=validate(saved);v.googleEnabled=bool3(json(ENABLED,v.googleEnabled));return v;}
  const pool=json('geovision_google_maps_api_keys',[]),enabled=bool3(json(ENABLED,[true,true,true]));
  return {google1:get('geovision_google_maps_api_key_1')||pool[0]||get('geovision_google_maps_api_key')||'',google2:get('geovision_google_maps_api_key_2')||pool[1]||'',google3:get('geovision_google_maps_api_key_3')||pool[2]||'',ai:get('geovision_ai_api_key')||'',youtube:get('geovision_youtube_api_key')||'',revision:0,googleEnabled:enabled};
 }
 const same=(a,b)=>NAMES.every(n=>a[n]===b[n])&&bool3(a.googleEnabled).every((x,i)=>x===bool3(b.googleEnabled)[i]);
 function choose(maps,enabled,current){let idx=maps.indexOf(current);if(idx>=0&&maps[idx]&&enabled[idx])return idx;idx=maps.findIndex((v,i)=>v&&enabled[i]);return idx>=0?idx:0;}
 function apply(value){
  const k=validate(value),old=read();if(k.revision&&old.revision&&k.revision<old.revision)throw Error('Risposta KeyBox precedente ignorata');
  const maps=[k.google1,k.google2,k.google3],enabled=bool3(k.googleEnabled),idx=choose(maps,enabled,get('geovision_google_maps_api_key')||'');
  const changes={[SNAP]:JSON.stringify(k),[ENABLED]:JSON.stringify(enabled),geovision_google_maps_api_keys:JSON.stringify(maps),geovision_google_maps_api_key:(maps[idx]&&enabled[idx])?maps[idx]:null,geovision_google_active_key_index:String(idx),geovision_ai_api_key:k.ai||null,geovision_youtube_api_key:k.youtube||null};
  maps.forEach((v,i)=>changes['geovision_google_maps_api_key_'+(i+1)]=v||null);if(['google1','google2','google3'].some(n=>old[n]!==k[n]))changes.geovision_key_cooldowns_v1=null;
  const before={};Object.keys(changes).forEach(n=>before[n]=get(n));try{for(const [n,v]of Object.entries(changes))v===null?storage.removeItem(n):storage.setItem(n,v);}catch(e){for(const [n,v]of Object.entries(before)){try{v===null?storage.removeItem(n):storage.setItem(n,v);}catch{}}throw Error('Salvataggio non riuscito: riprovare');}
  return !same(old,k);
 }
 function stage(value){const k=validate(value),old=read(),pending=json(PENDING,null),seen=Number(get('geovision_keybox_seen_revision_v1')||0);if(k.revision&&Math.max(old.revision||0,pending?.revision||0,seen)>k.revision)return false;if(k.revision)storage.setItem('geovision_keybox_seen_revision_v1',String(k.revision));if(same(old,k)){if(!pending||pending.revision<=k.revision)storage.removeItem(PENDING);return false;}storage.setItem(PENDING,JSON.stringify(k));return true;}
 function pending(){return json(PENDING,null);} function commitPending(){const k=pending();if(!k)return false;const c=apply(k);storage.removeItem(PENDING);return c;}
 function enabled(){return bool3(json(ENABLED,read().googleEnabled));}
 function setEnabled(index,on){if(index<0||index>2)return false;const k=read(),e=enabled();e[index]=!!on;k.googleEnabled=e;storage.setItem(ENABLED,JSON.stringify(e));storage.setItem(SNAP,JSON.stringify(k));const maps=[k.google1,k.google2,k.google3],idx=Number(get('geovision_google_active_key_index')||0);if((!e[idx]||!maps[idx])&&maps.some((v,i)=>v&&e[i])){const n=maps.findIndex((v,i)=>v&&e[i]);storage.setItem('geovision_google_active_key_index',String(n));storage.setItem('geovision_google_maps_api_key',maps[n]);root.gvGoogleKeyChanged?.(n,maps[n],'manual');}if(!maps.some((v,i)=>v&&e[i]))storage.removeItem('geovision_google_maps_api_key');return true;}
 function keyFailure(error){const t=[error?.code,error?.status,error?.message,String(error||'')].join(' ');return /RESOURCE_EXHAUSTED|OVER_QUERY_LIMIT|quota exceeded|quota metric|429|REQUEST_DENIED|API.?key.*(?:invalid|not valid|denied)|InvalidKey|ApiNotActivated|BillingNotEnabled|RefererNotAllowed|authentication failure/i.test(t);}
 function advance(error,now=Date.now()){
  if(!keyFailure(error))return false;const k=read(),maps=[k.google1,k.google2,k.google3],en=enabled(),idx=Number(get('geovision_google_active_key_index')||0),fail=json('geovision_key_cooldowns_v1',{});if(!maps[idx])return false;
  fail[idx]={until:now+60000};storage.setItem('geovision_key_cooldowns_v1',JSON.stringify(fail));for(let step=1;step<=3;step++){const n=(idx+step)%3;if(n===idx||!maps[n]||!en[n]||maps[n]===maps[idx]||(fail[n]?.until||0)>now)continue;storage.setItem('geovision_google_active_key_index',String(n));storage.setItem('geovision_google_maps_api_key',maps[n]);root.gvGoogleKeyChanged?.(n,maps[n],'failover');return true;}return false;
 }
 function active(){const k=read(),maps=[k.google1,k.google2,k.google3],en=enabled();let idx=Number(get('geovision_google_active_key_index')||0);if(!maps[idx]||!en[idx]){idx=maps.findIndex((v,i)=>v&&en[i]);if(idx<0)return {idx:-1,key:'',enabled:en};storage.setItem('geovision_google_active_key_index',String(idx));storage.setItem('geovision_google_maps_api_key',maps[idx]);}return {idx,key:maps[idx],enabled:en};}
 return {read,apply,stage,pending,commitPending,advance,active,enabled,setEnabled,keyFailure};
}
root.GVKeyState={create,validate,NAMES};if(typeof module!=='undefined')module.exports=root.GVKeyState;
})(typeof window!=='undefined'?window:globalThis);
