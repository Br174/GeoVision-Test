/* Transparent Places REST failover. Keeps the loaded Maps JS map alive while retrying Places with another enabled key. */
(function(root){
'use strict';
const ALL='id,displayName,location,formattedAddress,types,photos,rating,userRatingCount,editorialSummary,primaryTypeDisplayName,addressComponents';
function state(){return root.GVKeyState.create(localStorage);}
function errText(e){return [e?.code,e?.status,e?.message,String(e||'')].filter(Boolean).join(' | ');}
function latLng(v){if(!v)return null;const lat=Number(v.latitude??v.lat),lng=Number(v.longitude??v.lng);if(!Number.isFinite(lat)||!Number.isFinite(lng))return null;return {lat:()=>lat,lng:()=>lng,toJSON:()=>({lat,lng})};}
function photo(raw){const name=raw?.name||'';return {name,getURI:(o={})=>{const a=state().active(),w=Math.max(64,Math.min(4800,Number(o.maxWidth||o.maxWidthPx||1200))),h=Math.max(64,Math.min(4800,Number(o.maxHeight||o.maxHeightPx||1200)));return name&&a.key?'https://places.googleapis.com/v1/'+name.replace(/^\//,'')+'/media?maxWidthPx='+w+'&maxHeightPx='+h+'&key='+encodeURIComponent(a.key):'';}};}
function assign(target,r){if(!r)return target;target.id=r.id||target.id||'';target.displayName=typeof r.displayName==='object'?(r.displayName.text||''):(r.displayName||target.displayName||'');target.formattedAddress=r.formattedAddress||target.formattedAddress||'';target.location=latLng(r.location)||target.location;target.types=Array.isArray(r.types)?r.types:target.types||[];target.photos=Array.isArray(r.photos)?r.photos.map(photo):target.photos||[];target.rating=r.rating??target.rating;target.userRatingCount=r.userRatingCount??target.userRatingCount;target.editorialSummary=typeof r.editorialSummary==='object'?(r.editorialSummary.text||''):(r.editorialSummary||target.editorialSummary);target.primaryTypeDisplayName=typeof r.primaryTypeDisplayName==='object'?(r.primaryTypeDisplayName.text||''):(r.primaryTypeDisplayName||target.primaryTypeDisplayName);target.addressComponents=r.addressComponents||target.addressComponents||[];return target;}
function compat(r){const x=assign({},r);x.fetchFields=async()=>{await details(x);return {place:x};};return x;}
function bodyError(status,text){let msg=text;try{const j=JSON.parse(text);msg=j?.error?.message||j?.error?.status||text;}catch{}const e=new Error('HTTP '+status+(msg?' · '+msg:''));e.status=status;if(status===429)e.code='RESOURCE_EXHAUSTED';return e;}
async function request(path,opt={}){
 let last;for(let attempt=0;attempt<3;attempt++){
  const s=state(),a=s.active();if(!a.key)throw new Error('Nessuna chiave Google abilitata');
  const headers={...(opt.headers||{}),'X-Goog-Api-Key':a.key};if(opt.fieldMask)headers['X-Goog-FieldMask']=opt.fieldMask;
  const r=await fetch('https://places.googleapis.com/v1/'+path,{...opt,headers});if(r.ok)return r.status===204?{}:r.json();const text=await r.text();last=bodyError(r.status,text);if(!s.keyFailure(last)||!s.advance(last))throw last;
 }
 throw last||new Error('Places non disponibile');
}
function bias(v){if(!v)return undefined;const c=v.center||v;const lat=Number(c.lat?.()??c.lat),lng=Number(c.lng?.()??c.lng);if(!Number.isFinite(lat)||!Number.isFinite(lng))return undefined;return {circle:{center:{latitude:lat,longitude:lng},radius:Number(v.radius||5000)}};}
async function searchText(o={}){const b={textQuery:o.textQuery||'',pageSize:Math.max(1,Math.min(20,Number(o.maxResultCount||o.pageSize||10))),languageCode:o.language||'it',regionCode:o.region||'IT'};const lb=bias(o.locationBias);if(lb)b.locationBias=lb;if(o.includedType)b.includedType=o.includedType;if(o.useStrictTypeFiltering)b.strictTypeFiltering=true;const j=await request('places:searchText',{method:'POST',headers:{'Content-Type':'application/json'},fieldMask:'places.'+ALL.split(',').join(',places.'),body:JSON.stringify(b)});return {places:(j.places||[]).map(compat)};}
async function searchNearby(o={}){const lr=o.locationRestriction||{},c=lr.center||{};const lat=Number(c.lat?.()??c.lat),lng=Number(c.lng?.()??c.lng);if(!Number.isFinite(lat)||!Number.isFinite(lng))throw new Error('Centro ricerca non valido');const b={locationRestriction:{circle:{center:{latitude:lat,longitude:lng},radius:Number(lr.radius||1000)}},maxResultCount:Math.max(1,Math.min(20,Number(o.maxResultCount||10))),languageCode:o.language||'it',rankPreference:String(o.rankPreference||'POPULARITY').includes('DISTANCE')?'DISTANCE':'POPULARITY'};const j=await request('places:searchNearby',{method:'POST',headers:{'Content-Type':'application/json'},fieldMask:'places.'+ALL.split(',').join(',places.'),body:JSON.stringify(b)});return {places:(j.places||[]).map(compat)};}
async function details(obj){if(!obj?.id)throw new Error('Place ID mancante');const j=await request('places/'+encodeURIComponent(obj.id),{method:'GET',fieldMask:ALL});assign(obj,j);return obj;}
function install(){
 if(!root.google?.maps?.importLibrary||root.google.maps.importLibrary.__gvFailover)return false;const original=root.google.maps.importLibrary.bind(root.google.maps);root.gvMapsBootKey=localStorage.getItem('geovision_google_maps_api_key')||'';
 const wrapped=async function(name){const lib=await original(name);if(name!=='places'||!lib?.Place||lib.Place.__gvFailover)return lib;const P=lib.Place,origSearch=P.searchByText?.bind(P),origNearby=P.searchNearby?.bind(P),origFetch=P.prototype?.fetchFields;
  P.searchByText=async function(o){const a=state().active();if(a.key&&a.key===root.gvMapsBootKey&&a.enabled[a.idx]&&origSearch){try{return await origSearch(o);}catch(e){if(!state().keyFailure(e))throw e;if(!state().advance(e))throw e;}}return searchText(o);};
  P.searchNearby=async function(o){const a=state().active();if(a.key&&a.key===root.gvMapsBootKey&&a.enabled[a.idx]&&origNearby){try{return await origNearby(o);}catch(e){if(!state().keyFailure(e))throw e;if(!state().advance(e))throw e;}}return searchNearby(o);};
  if(origFetch)P.prototype.fetchFields=async function(o){const a=state().active();if(a.key&&a.key===root.gvMapsBootKey&&a.enabled[a.idx]){try{return await origFetch.call(this,o);}catch(e){if(!state().keyFailure(e))throw e;if(!state().advance(e))throw e;}}await details(this);return {place:this};};
  P.__gvFailover=true;return lib;};wrapped.__gvFailover=true;root.google.maps.importLibrary=wrapped;return true;
}
root.GVPlacesFailover={install,request,searchText,searchNearby,details,compat};
})(window);
