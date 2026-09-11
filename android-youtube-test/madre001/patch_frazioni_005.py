from pathlib import Path
p=Path('/tmp/GeoVision_LAB_005_SOURCE.html')
s=p.read_text(encoding='utf-8')

start=s.find('async function googleLocalityAt')
end=s.find('async function googlePoiLocalityAt',start)
if start<0 or end<0:
    raise SystemExit('googleLocalityAt anchors missing')

replacement=r'''function gvComp005(r,t){const c=(r?.address_components||[]).find(x=>(x.types||[]).includes(t));return clean(c?.long_name||c?.longText||'');}
function gvGeoType005(types){return (types||[]).some(t=>t==='locality'||t==='postal_town'||t==='neighborhood'||t==='political'||t==='sublocality'||String(t).startsWith('sublocality_')||String(t).startsWith('administrative_area_'));}
function gvFineKind005(types){if((types||[]).includes('neighborhood'))return 'Frazione / Quartiere';if((types||[]).some(t=>String(t).startsWith('sublocality')))return 'Frazione / Località';return 'Località / Territorio';}
function gvFineArea005(p){return !!p&&!p.isPoi&&/frazione|quartiere|località|rione|contrada/i.test(p.kind||'');}
function gvFineCandidate005(results){
  const order=['sublocality_level_1','sublocality_level_2','sublocality','neighborhood','administrative_area_level_4'];
  for(const ty of order){for(const r of results||[]){const name=gvComp005(r,ty);if(!name)continue;const parent=[gvComp005(r,'locality'),gvComp005(r,'administrative_area_level_3'),gvComp005(r,'administrative_area_level_2')].filter((v,i,a)=>v&&norm(v)!==norm(name)&&a.indexOf(v)===i).slice(0,2).join(', ');return{name,parent,kind:ty==='neighborhood'?'Frazione / Quartiere':'Frazione / Località',r};}}
  for(const r of results||[]){const name=gvComp005(r,'locality')||gvComp005(r,'postal_town'),admin3=gvComp005(r,'administrative_area_level_3');if(name&&admin3&&norm(name)!==norm(admin3))return{name,parent:[admin3,gvComp005(r,'administrative_area_level_2')].filter(Boolean).join(', '),kind:'Frazione / Località',r};}
  return null;
}
async function gvExactArea005(f,lat,lng){
  if(!f?.name||!googleReady)return null;const wanted=norm(f.name),origin={lat:Number(lat),lng:Number(lng)},q=[f.name,f.parent].filter(Boolean).join(', ');
  try{const g=new google.maps.Geocoder(),rr=await g.geocode({address:q}),rows=(rr.results||[]).filter(r=>r.place_id&&gvGeoType005(r.types)).map(r=>{const exact=(r.address_components||[]).some(c=>norm(c.long_name||c.longText||'')===wanted)||norm(componentName(r,15))===wanted;const loc=r.geometry?.location,la=loc?loc.lat():origin.lat,lo=loc?loc.lng():origin.lng,d=metersBetween(origin,{lat:la,lng:lo});return{r,la,lo,s:(exact?1200:0)+Math.max(0,160-Math.min(160,d/120))};}).sort((a,b)=>b.s-a.s);if(rows[0]?.s>=1100){const b=rows[0];return{name:f.name,kind:f.kind||gvFineKind005(b.r.types),lat:b.la,lon:b.lo,address:clean(b.r.formatted_address||''),parent:f.parent,isPoi:false,source:'Google Maps',placeId:String(b.r.place_id)};}}catch{}
  try{const lib=await google.maps.importLibrary('places'),P=lib.Place,{places}=await P.searchByText({textQuery:q,fields:['id','displayName','location','formattedAddress','types'],locationBias:origin,language:'it',region:'IT',maxResultCount:10}),rows=(places||[]).filter(pl=>pl.id&&pl.location&&gvGeoType005(pl.types)).map(pl=>{const la=typeof pl.location.lat==='function'?pl.location.lat():Number(pl.location.lat),lo=typeof pl.location.lng==='function'?pl.location.lng():Number(pl.location.lng),nm=norm(pl.displayName||''),d=metersBetween(origin,{lat:la,lng:lo});return{pl,la,lo,s:(nm===wanted?1200:nm.includes(wanted)||wanted.includes(nm)?500:0)+Math.max(0,160-Math.min(160,d/120))};}).sort((a,b)=>b.s-a.s);const b=rows[0];if(b&&b.s>=500)return{name:clean(b.pl.displayName||f.name),kind:f.kind||gvFineKind005(b.pl.types),lat:b.la,lon:b.lo,address:clean(b.pl.formattedAddress||''),parent:f.parent,isPoi:false,source:'Google Places',placeId:String(b.pl.id)};}catch{}
  return null;
}
async function googleLocalityAt(lat,lng,preferSpecific=false){if(!googleReady)return null;try{
  const geocoder=new google.maps.Geocoder(),zoom=currentZoom(),rr=await geocoder.geocode({location:{lat,lng}}),results=rr.results||[];
  if(preferSpecific){const f=gvFineCandidate005(results);if(f){const exact=await gvExactArea005(f,lat,lng);if(exact)return exact;const loc=f.r?.geometry?.location;return{name:f.name,kind:f.kind,lat:loc?loc.lat():lat,lon:loc?loc.lng():lng,address:clean(f.r?.formatted_address||''),parent:f.parent,isPoi:false,source:'Google Maps',placeId:f.r?.place_id||''};}}
  const ranked=results.map(r=>({r,s:resultScore(r,zoom)})).filter(x=>x.s>0).sort((a,b)=>b.s-a.s),source=ranked[0]?.r||results[0];if(!source)return null;
  const candidate=componentName(source,zoom),parent=componentParent(source,candidate),query=[candidate,parent].filter(Boolean).join(', ');let r=source;
  if(candidate){try{const fr=await geocoder.geocode({address:query}),cands=(fr.results||[]).map(x=>({x,s:resultScore(x,zoom)+(norm(componentName(x,zoom))===norm(candidate)?55:0)})).sort((a,b)=>b.s-a.s);if(cands[0]?.x)r=cands[0].x;}catch{}}
  const loc=r.geometry?.location,name=componentName(r,zoom)||candidate,parent2=componentParent(r,name)||parent,types=r.types||[],kind=types.includes('locality')||types.includes('postal_town')?'Città / Paese':types.some(x=>String(x).startsWith('sublocality')||x==='neighborhood')?'Frazione / Località':'Comune / Territorio';
  return{name,kind,lat:loc?loc.lat():lat,lon:loc?loc.lng():lng,address:clean(r.formatted_address||source.formatted_address||''),parent:parent2,isPoi:false,source:'Google Maps',placeId:r.place_id||source.place_id};
}catch{return null;}}
'''
s=s[:start]+replacement+s[end:]

old="""async function canonicalGeoPlace(p) { if (!googleReady || !p.name)
    return p; try {"""
new="""async function canonicalGeoPlace(p) { if (!googleReady || !p.name)
    return p; if (gvFineArea005(p)) {
    const x=await gvExactArea005({name:p.name,parent:p.parent,kind:p.kind},p.lat,p.lon);
    return x?{...p,...x,isPoi:false}:p;
} try {"""
if old not in s: raise SystemExit('canonicalGeoPlace anchor missing')
s=s.replace(old,new,1)

old="""async function gvResolveGeoPlace003(p) {
    if (!googleReady || !p || p.isPoi || !p.name || p.placeId) return p;
    const origin = { lat: Number(p.lat), lng: Number(p.lon) };"""
new="""async function gvResolveGeoPlace003(p) {
    if (!googleReady || !p || p.isPoi || !p.name || p.placeId) return p;
    const origin = { lat: Number(p.lat), lng: Number(p.lon) };
    if (gvFineArea005(p)) {
        const x=await gvExactArea005({name:p.name,parent:p.parent,kind:p.kind},origin.lat,origin.lng);
        return x?{...p,...x,isPoi:false}:p;
    }"""
if old not in s: raise SystemExit('photo resolver anchor missing')
s=s.replace(old,new,1)

old="""async function resolveLocality(lat, lng) { toast('Identifico città o paese…'); const found = await googleLocalityAt(lat, lng) || await reverseFallback(lat, lng), canonical = await canonicalGeoPlace(found), p = await richLocalityPlace(canonical); return openPlace(p); }"""
new="""async function resolveLocality(lat, lng) { toast('Identifico città, paese o frazione…'); const found = await googleLocalityAt(lat, lng, true) || await reverseFallback(lat, lng), canonical = await canonicalGeoPlace(found), p = gvFineArea005(canonical) ? canonical : await richLocalityPlace(canonical); return openPlace(p); }"""
if old not in s: raise SystemExit('resolveLocality anchor missing')
s=s.replace(old,new,1)

old="""} window.setTimeout(async () => { const near = await nearbyGooglePoi(pos); if (near)
        return openPlace(near); closeNativeAudio(); return resolveLocality(pos.lat, pos.lng); }, 40); });"""
new="""} window.setTimeout(async () => { const z=Number(googleMap?.getZoom?.()||currentZoom()||12); if(z>=16){const near = await nearbyGooglePoi(pos); if (near) return openPlace(near);} closeNativeAudio(); return resolveLocality(pos.lat, pos.lng); }, 40); });"""
if old not in s: raise SystemExit('google click anchor missing')
s=s.replace(old,new,1)

assert 'gvFineCandidate005' in s
assert 'gvExactArea005' in s
assert 'z>=16' in s
assert 'gvLocalityPrecision004' not in s
p.write_text(s,encoding='utf-8')
print('Applied LAB 005 FRAZIONI:',len(s))
