from pathlib import Path
p=Path('/tmp/GeoVision_LAB_001_SOURCE.html')
s=p.read_text(encoding='utf-8')

start=s.find('async function googleLocalityAt')
end=s.find('async function googlePoiLocalityAt',start)
if start<0 or end<0: raise SystemExit('googleLocalityAt anchors missing')
s=s[:start]+r'''function gvComp004(r,t){const c=(r?.address_components||[]).find(x=>(x.types||[]).includes(t));return clean(c?.long_name||'');}
function gvGeo004(t){return (t||[]).some(x=>x==='locality'||x==='postal_town'||x==='political'||x==='neighborhood'||x==='sublocality'||String(x).startsWith('sublocality_')||String(x).startsWith('administrative_area_'));}
function gvFineArea004(p){return !!p&&!p.isPoi&&/frazione|quartiere|località/i.test(p.kind||'');}
function gvFineCandidate004(results){
    for(const ty of ['sublocality_level_1','sublocality','neighborhood']){
        for(const r of results||[]){const name=gvComp004(r,ty);if(!name)continue;const vals=[];for(const pt of ['administrative_area_level_3','locality','administrative_area_level_2']){const v=gvComp004(r,pt);if(v&&norm(v)!==norm(name)&&!vals.includes(v))vals.push(v);}return{name,parent:vals.slice(0,2).join(', '),kind:ty==='neighborhood'?'Frazione / Quartiere':'Frazione / Località',r};}
    }
    for(const r of results||[]){const name=gvComp004(r,'locality')||gvComp004(r,'postal_town'),parent=gvComp004(r,'administrative_area_level_3');if(name&&parent&&norm(name)!==norm(parent))return{name,parent:[parent,gvComp004(r,'administrative_area_level_2')].filter(Boolean).join(', '),kind:'Frazione / Località',r};}
    return null;
}
async function gvExactArea004(f,lat,lng){
    if(!f?.name||!googleReady)return null;const q=[f.name,f.parent].filter(Boolean).join(', '),wanted=norm(f.name),origin={lat:Number(lat),lng:Number(lng)};
    try{const g=new google.maps.Geocoder(),rr=await g.geocode({address:q}),rows=(rr.results||[]).filter(r=>r.place_id&&gvGeo004(r.types)).map(r=>{const exact=(r.address_components||[]).some(c=>norm(c.long_name||'')===wanted),loc=r.geometry?.location,la=loc?loc.lat():origin.lat,lo=loc?loc.lng():origin.lng,d=metersBetween(origin,{lat:la,lng:lo});return{r,la,lo,s:(exact?1000:0)+Math.max(0,120-Math.min(120,d/150))};}).sort((a,b)=>b.s-a.s);if(rows[0]?.s>=900){const b=rows[0];return{name:f.name,kind:f.kind,lat:b.la,lon:b.lo,address:clean(b.r.formatted_address||''),parent:f.parent,isPoi:false,source:'Google Maps',placeId:String(b.r.place_id)};}}catch{}
    try{const lib=await google.maps.importLibrary('places'),P=lib.Place,{places}=await P.searchByText({textQuery:q,fields:['id','displayName','location','formattedAddress','types'],locationBias:origin,language:'it',region:'IT',maxResultCount:8}),pl=(places||[]).filter(x=>x.id&&x.location&&gvGeo004(x.types)&&norm(x.displayName||'')===wanted)[0];if(pl){const la=typeof pl.location.lat==='function'?pl.location.lat():Number(pl.location.lat),lo=typeof pl.location.lng==='function'?pl.location.lng():Number(pl.location.lng);return{name:clean(pl.displayName||f.name),kind:f.kind,lat:la,lon:lo,address:clean(pl.formattedAddress||''),parent:f.parent,isPoi:false,source:'Google Places',placeId:String(pl.id)};}}catch{}
    return null;
}
async function googleLocalityAt(lat,lng,preferSpecific=false){if(!googleReady)return null;try{
    const geocoder=new google.maps.Geocoder(),zoom=currentZoom(),rr=await geocoder.geocode({location:{lat,lng}}),results=rr.results||[];
    if(preferSpecific){const f=gvFineCandidate004(results);if(f){const x=await gvExactArea004(f,lat,lng);if(x)return x;const loc=f.r?.geometry?.location;return{name:f.name,kind:f.kind,lat:loc?loc.lat():lat,lon:loc?loc.lng():lng,address:clean(f.r?.formatted_address||''),parent:f.parent,isPoi:false,source:'Google Maps',placeId:''};}}
    const ranked=results.map(r=>({r,s:resultScore(r,zoom)})).filter(x=>x.s>0).sort((a,b)=>b.s-a.s),source=ranked[0]?.r||results[0];if(!source)return null;
    const candidate=componentName(source,zoom),parent=componentParent(source,candidate),query=[candidate,parent].filter(Boolean).join(', ');let r=source;
    if(candidate){try{const fr=await geocoder.geocode({address:query}),cands=(fr.results||[]).map(x=>({x,s:resultScore(x,zoom)+(norm(componentName(x,zoom))===norm(candidate)?55:0)+(norm(x.formatted_address||'').includes(norm(parent.split(',')[0]||''))?12:0)})).sort((a,b)=>b.s-a.s);if(cands[0]?.x)r=cands[0].x;}catch{}}
    const loc=r.geometry?.location,name=componentName(r,zoom)||candidate,parent2=componentParent(r,name)||parent,types=r.types||[],kind=types.includes('locality')||types.includes('postal_town')?'Città / Paese':types.some(x=>x.startsWith('sublocality'))?'Frazione / Località':'Comune / Territorio';
    return{name,kind,lat:loc?loc.lat():lat,lon:loc?loc.lng():lng,address:clean(r.formatted_address||source.formatted_address||''),parent:parent2,isPoi:false,source:'Google Maps',placeId:r.place_id||source.place_id};
}catch{return null;}}
'''+s[end:]

old="""async function canonicalGeoPlace(p) { if (!googleReady || !p.name)
    return p; try {"""
new="""async function canonicalGeoPlace(p) { if (!googleReady || !p.name)
    return p; if (gvFineArea004(p)) {
    const x=await gvExactArea004({name:p.name,parent:p.parent,kind:p.kind},p.lat,p.lon);
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
    if (gvFineArea004(p)) {
        const x=await gvExactArea004({name:p.name,parent:p.parent,kind:p.kind},origin.lat,origin.lng);
        return x?{...p,...x,isPoi:false}:p;
    }"""
if old not in s: raise SystemExit('gvResolveGeoPlace003 anchor missing')
s=s.replace(old,new,1)

old="""async function resolveLocality(lat, lng) { toast('Identifico città o paese…'); const found = await googleLocalityAt(lat, lng) || await reverseFallback(lat, lng), canonical = await canonicalGeoPlace(found), p = await richLocalityPlace(canonical); return openPlace(p); }"""
new="""async function resolveLocality(lat, lng) { toast('Identifico città, paese o frazione…'); const found = await googleLocalityAt(lat, lng, true) || await reverseFallback(lat, lng), canonical = await canonicalGeoPlace(found), p = await richLocalityPlace(canonical); return openPlace(p); }"""
if old not in s: raise SystemExit('resolveLocality anchor missing')
s=s.replace(old,new,1)

start=s.find('async function search()')
end=s.find("$('#search').onclick = search;",start)
if start<0 or end<0: raise SystemExit('search anchors missing')
s=s[:start]+r'''async function search() { const q = clean(document.getElementById('manual').value); if (!q)
    return toast('Scriva una località'); if (googleReady) {
    try {
        const geocoder=new google.maps.Geocoder(),rr=await geocoder.geocode({address:q}),fine=gvFineCandidate004(rr.results||[]);
        if(fine&&norm(q).includes(norm(fine.name))){const x=await gvExactArea004(fine,fine.r?.geometry?.location?.lat?.()||0,fine.r?.geometry?.location?.lng?.()||0),base=x||{name:fine.name,kind:fine.kind,lat:fine.r.geometry.location.lat(),lon:fine.r.geometry.location.lng(),address:clean(fine.r.formatted_address||''),parent:fine.parent,isPoi:false,source:'Google Maps',placeId:''};googleMap.setCenter({lat:base.lat,lng:base.lon});googleMap.setZoom(15);return openPlace(base);}
        const r=(rr.results||[]).map(x=>({x,s:resultScore(x)})).sort((a,b)=>b.s-a.s)[0]?.x||rr.results?.[0];
        if(!r)return toast('Località non trovata');const loc=r.geometry.location,base={name:componentName(r),kind:'Città / Paese',lat:loc.lat(),lon:loc.lng(),address:clean(r.formatted_address||''),parent:componentParent(r,componentName(r)),isPoi:false,source:'Google Maps',placeId:r.place_id};
        googleMap.setCenter({lat:base.lat,lng:base.lon});googleMap.setZoom(13);const p=await richLocalityPlace(base);return openPlace(p);
    } catch { }
} try {
    const j = await getJson(`https://nominatim.openstreetmap.org/search?format=jsonv2&limit=1&addressdetails=1&accept-language=it&q=${encodeURIComponent(q)}`);
    if (!j.length)
        return toast('Località non trovata');
    const r = j[0];
    map.setView([+r.lat, +r.lon], 13);
    return resolveLocality(+r.lat, +r.lon);
}
catch {
    toast('Ricerca temporaneamente non disponibile');
} }
'''+s[end:]

p.write_text(s,encoding='utf-8')
print('Applied LAB 004 fraction/locality precision:',len(s))
