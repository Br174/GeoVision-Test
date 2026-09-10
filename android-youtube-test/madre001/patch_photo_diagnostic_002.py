from pathlib import Path
p=Path('/tmp/GeoVision_LAB_001_SOURCE.html')
s=p.read_text(encoding='utf-8')
anchor='async function renderOfficialGoogleCard(p) {'
if anchor not in s:
    raise SystemExit('renderOfficialGoogleCard anchor missing')
helper=r'''async function gvPhotoProbe002(p) {
    const d = { name: clean(p?.name || ''), kind: clean(p?.kind || ''), placeId: clean(p?.placeId || ''), googleReady: !!googleReady, zoom: currentZoom(), center: currentCenter(), original: window.gvPhotoDiag || null, direct: null, text: [], strict: [], legacy: [], geocoder: [], errors: [] };
    const count = x => Array.isArray(x?.photos) ? x.photos.length : 0;
    const placeRow = (x, q='') => { if (!x) return null; let lat=null,lng=null,dist=null; try { lat=typeof x.location?.lat==='function'?x.location.lat():Number(x.location?.lat); lng=typeof x.location?.lng==='function'?x.location.lng():Number(x.location?.lng); if(Number.isFinite(lat)&&Number.isFinite(lng)) dist=Math.round(metersBetween(d.center,{lat,lng})); } catch {} return { q, id: clean(x.id || x.place_id || ''), name: clean(x.displayName || x.name || ''), types: Array.from(x.types || []).slice(0,5), photos: count(x), meters: dist }; };
    if (!googleReady) { d.errors.push('googleReady=false'); return d; }
    try {
        const lib = await google.maps.importLibrary('places'), P = lib.Place;
        if (p.placeId) {
            try {
                const pl = new P({ id: p.placeId });
                await pl.fetchFields({ fields: ['displayName','types','photos','googleMapsURI','location'] });
                d.direct = placeRow(pl, 'Place ID diretto');
                if (d.direct) d.direct.maps = clean(pl.googleMapsURI || '');
            } catch(e) { d.errors.push('diretto: ' + clean(e?.code || e?.message || e)); }
        }
        const queries = [clean(p.name || ''), [p.name,p.parent].filter(Boolean).join(', ')].filter((v,i,a)=>v && a.indexOf(v)===i);
        for (const q of queries) {
            try {
                const r = await P.searchByText({ textQuery:q, fields:['id','displayName','types','photos','googleMapsURI','location'], locationBias:d.center, language:'it', region:'IT', maxResultCount:5 });
                for (const x of r.places || []) { const row=placeRow(x,q); if(row) d.text.push(row); }
            } catch(e) { d.errors.push('text '+q+': '+clean(e?.code || e?.message || e)); }
            try {
                const r = await P.searchByText({ textQuery:q, fields:['id','displayName','types','photos','location'], includedType:'locality', useStrictTypeFiltering:true, locationBias:d.center, language:'it', region:'IT', maxResultCount:5 });
                for (const x of r.places || []) { const row=placeRow(x,q); if(row) d.strict.push(row); }
            } catch(e) { d.errors.push('locality '+q+': '+clean(e?.code || e?.message || e)); }
        }
        try {
            const g = new google.maps.Geocoder();
            const rr = await g.geocode({ address: clean(p.name || '') });
            d.geocoder = (rr.results || []).slice(0,4).map(r=>({id:clean(r.place_id||''), name:clean(r.formatted_address||''), types:Array.from(r.types||[]).slice(0,5)}));
        } catch(e) { d.errors.push('geocoder: '+clean(e?.code || e?.message || e)); }
        try {
            const S = google.maps.places?.PlacesService;
            if (S) {
                const svc = new S(googleMap || document.createElement('div'));
                const legacy = await new Promise(resolve => svc.textSearch({ query: clean(p.name || ''), location:new google.maps.LatLng(d.center.lat,d.center.lng), radius:12000 }, (results,status)=>resolve({results:results||[],status:String(status||'')})));
                d.legacyStatus = legacy.status;
                d.legacy = legacy.results.slice(0,5).map(x=>({q:clean(p.name||''), id:clean(x.place_id||''), name:clean(x.name||''), types:Array.from(x.types||[]).slice(0,5), photos:Array.isArray(x.photos)?x.photos.length:0}));
            } else d.errors.push('PlacesService legacy assente');
        } catch(e) { d.errors.push('legacy: '+clean(e?.code || e?.message || e)); }
    } catch(e) { d.errors.push('places: '+clean(e?.code || e?.message || e)); }
    window.gvPhotoProbe002 = d;
    try { console.info('[GeoVisionPhotoProbe002]', JSON.stringify(d)); } catch {}
    return d;
}
function gvPhotoProbeHtml002(d) {
    const shortId = id => { id=clean(id||''); return id ? (id.length>18 ? id.slice(0,8)+'…'+id.slice(-7) : id) : '—'; };
    const row = (label, v) => `<div style="margin-top:4px"><b>${esc(label)}:</b> ${esc(v)}</div>`;
    const list = (arr) => (arr||[]).slice(0,3).map(x => `${x.name||'—'} · foto ${Number(x.photos||0)} · ${shortId(x.id)}${Number.isFinite(x.meters)?' · '+x.meters+' m':''}`).join('<br>') || 'nessun risultato';
    const direct = d.direct ? `${d.direct.name||'—'} · foto ${Number(d.direct.photos||0)} · ${shortId(d.direct.id)}` : 'nessun risultato';
    const orig = d.original ? `URL ${Number(d.original.urls||0)} · candidati ${(d.original.candidates||[]).length} · errori ${(d.original.errors||[]).length}` : 'diagnostica precedente assente';
    const errs = (d.errors||[]).slice(0,4).join(' | ') || 'nessuno';
    return `<div id="gvPhotoDiagBox002" style="padding:11px 14px;background:#fff7ed;border-top:1px solid #fed7aa;border-bottom:1px solid #fed7aa;color:#7c2d12;font:11px/1.38 system-ui;word-break:break-word"><div style="font-size:12px;font-weight:900">DIAGNOSTICA FOTO 002 — zero foto</div>${row('Luogo', `${d.name||'—'} · ${d.kind||'—'} · zoom ${d.zoom}`)}${row('Place ID corrente', shortId(d.placeId))}${row('Tentativo precedente', orig)}${row('Place Details', direct)}${row('Text Search', list(d.text))}${row('Text Search locality', list(d.strict))}${row('Legacy', list(d.legacy))}${row('Errori', errs)}</div>`;
}
'''
s=s.replace(anchor,helper+anchor,1)
old="""if (cityLocality) {
    void googleLocalityPhotos(p).then(urls => { if (current !== p || !photoHost?.isConnected || !urls.length)
        return; photoHost.innerHTML = `<div class=\"google-photo-strip\">${urls.map(u => `<img src=\"${esc(u)}\" alt=\"${esc(p.name)}\">`).join('')}</div>`; });
}"""
new="""if (cityLocality) {
    void googleLocalityPhotos(p).then(async urls => { if (current !== p || !photoHost?.isConnected)
        return; if (urls.length) { photoHost.innerHTML = `<div class=\"google-photo-strip\">${urls.map(u => `<img src=\"${esc(u)}\" alt=\"${esc(p.name)}\">`).join('')}</div>`; return; } const d = await gvPhotoProbe002(p); if (current !== p || !photoHost?.isConnected) return; photoHost.innerHTML = gvPhotoProbeHtml002(d); });
}"""
if old not in s:
    raise SystemExit('photo callback anchor missing')
s=s.replace(old,new,1)
p.write_text(s,encoding='utf-8')
print('Applied photo diagnostic 002:', len(s))