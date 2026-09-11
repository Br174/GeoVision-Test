/* KeyBox snapshots are applied before GeoVision boot or by explicit Apply only. */
(function(root){
'use strict';
const NAMES=['google1','google2','google3','ai','youtube'];
const SNAP='geovision_keys_snapshot_v1', PENDING='geovision_keys_pending_v1';
function validate(value){
 if(!value || typeof value!=='object' || Array.isArray(value))throw Error('Dati KeyBox non validi');
 const keys={};for(const name of NAMES){if(typeof value[name]!=='string'||value[name].length>512||/[\r\n\x00]/.test(value[name]))throw Error('Formato chiavi non valido');keys[name]=value[name].trim();}
 if(!Object.values(keys).some(Boolean))throw Error('KeyBox vuoto: chiavi locali conservate');
 const revision=value.revision===undefined?0:value.revision;
 if(!Number.isSafeInteger(revision)||revision<0)throw Error('Revisione non valida');
 return {...keys,revision};
}
function create(storage){
 const get=(k)=>storage.getItem(k);const json=(k,f)=>{try{return JSON.parse(get(k))||f;}catch{return f;}};
 function read(){const saved=json(SNAP,null);if(saved)return validate(saved);const pool=json('geovision_google_maps_api_keys',[]);return {google1:get('geovision_google_maps_api_key_1')||pool[0]||get('geovision_google_maps_api_key')||'',google2:get('geovision_google_maps_api_key_2')||pool[1]||'',google3:get('geovision_google_maps_api_key_3')||pool[2]||'',ai:get('geovision_ai_api_key')||'',youtube:get('geovision_youtube_api_key')||'',revision:0};}
 const same=(a,b)=>NAMES.every(n=>a[n]===b[n]);
 function apply(value){
  const k=validate(value),old=read();
  if(k.revision&&old.revision&&k.revision<old.revision)throw Error('Risposta KeyBox precedente ignorata');
  const maps=[k.google1,k.google2,k.google3],current=get('geovision_google_maps_api_key')||'';
  let idx=maps.indexOf(current);if(idx<0||!current)idx=maps.findIndex(Boolean);if(idx<0)idx=0;
  const changes={[SNAP]:JSON.stringify(k),geovision_google_maps_api_keys:JSON.stringify(maps),geovision_google_maps_api_key:maps[idx]||null,geovision_google_active_key_index:String(idx),geovision_ai_api_key:k.ai||null,geovision_youtube_api_key:k.youtube||null};
  maps.forEach((v,i)=>changes['geovision_google_maps_api_key_'+(i+1)]=v||null);
  const before={};Object.keys(changes).forEach(n=>before[n]=get(n));
  try{for(const [n,v]of Object.entries(changes)){v===null?storage.removeItem(n):storage.setItem(n,v);}}
  catch(e){for(const [n,v]of Object.entries(before)){try{v===null?storage.removeItem(n):storage.setItem(n,v);}catch{}}throw Error('Salvataggio non riuscito: riprovare');}
  return !same(old,k);
 }
 function stage(value){const k=validate(value),old=read(),pending=json(PENDING,null);if(k.revision&&Math.max(old.revision||0,pending?.revision||0)>k.revision)return false;if(same(old,k)){if(!pending||pending.revision<=k.revision)storage.removeItem(PENDING);return false;}storage.setItem(PENDING,JSON.stringify(k));return true;}
 function pending(){return json(PENDING,null);}
 function commitPending(){const k=pending();if(!k)return false;const changed=apply(k);storage.removeItem(PENDING);return changed;}
 // Failure records survive reload; duplicate callbacks never skip multiple keys.
 function advance(error,now=Date.now()){
  const text=[error?.code,error?.status,error?.message,String(error||'')].join(' ');
  if(!/RESOURCE_EXHAUSTED|OVER_QUERY_LIMIT|quota exceeded|429|REQUEST_DENIED|API.?key.*(?:invalid|not valid|denied)|InvalidKey|ApiNotActivated|BillingNotEnabled|RefererNotAllowed/i.test(text))return false;
  const k=read(),maps=[k.google1,k.google2,k.google3],idx=Number(get('geovision_google_active_key_index')||0);
  const failures=json('geovision_key_cooldowns_v1',{});if(!maps[idx])return false;
  // Never persist the raw API error, which can contain a credential-bearing URL.
  failures[idx]={until:now+60000};storage.setItem('geovision_key_cooldowns_v1',JSON.stringify(failures));
  for(let step=1;step<=2;step++){const next=(idx+step)%3;if(!maps[next]||maps[next]===maps[idx]||(failures[next]?.until||0)>now)continue;storage.setItem('geovision_google_active_key_index',String(next));storage.setItem('geovision_google_maps_api_key',maps[next]);return true;}
  return false;
 }
 return {read,apply,stage,pending,commitPending,advance};
}
root.GVKeyState={create,validate,NAMES};if(typeof module!=='undefined')module.exports=root.GVKeyState;
})(typeof window!=='undefined'?window:globalThis);
