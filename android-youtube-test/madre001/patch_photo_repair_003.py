from pathlib import Path
p=Path('/tmp/GeoVision_LAB_001_SOURCE.html')
s=p.read_text(encoding='utf-8')
anchor='function isOfficialCityLocality(p) { return !p.isPoi && /città|paese|comune/i.test(p.kind || \'\'); }'
if anchor not in s:
    raise SystemExit('anchor missing')
helper=r'''function gvPhotoUrl003(ph) {
    try {
        if (typeof ph?.getURI === 'function') return clean(ph.getURI({ maxWidth: 1200, maxHeight: 720 }) || '');
        if (typeof ph?.getUrl === 'function') return clean(ph.getUrl({ maxWidth: 1200, maxHeight: 720 }) || '');
    } catch { }
    return '';
}
function gvGeoType003(types) {
    return (types || []).some(t => t === 'locality' || t === 'postal_town' || t === 'political' || t === 'neighborhood' || t === 'colloquial_area' || t === 'administrative_area_level_1' || t === 'administrative_area_level_2' || t === 'administrative_area_level_3' || t === 'country' || t === 'sublocality' || String(t).startsWith('sublocality_'));
}
function gvCommercialType003(types) {
    return (types || []).some(t => /restaurant|cafe|bar|store|shop|lodging|hotel|supermarket|bakery|pharmacy|bank|gas_station|car_repair|beauty|hair|doctor|dentist|school|hospital/.test(String(t)));
}
async function gvResolveGeoPlace003(p) {
    if (!googleReady || !p || p.isPoi || !p.name || p.placeId) return p;
    const origin = { lat: Number(p.lat), lng: Number(p.lon) };
    try {
        const geocoder = new google.maps.Geocoder(), q = [p.name, p.parent].filter(Boolean).join(', '), rr = await geocoder.geocode({ address: q });
        const wanted = norm(p.name || '');
        const ranked = (rr.results || []).map(r => {
            const types = r.types || [], loc = r.geometry?.location;
            const lat = loc ? loc.lat() : origin.lat, lng = loc ? loc.lng() : origin.lng;
            const d = metersBetween(origin, { lat, lng });
            const n = norm(componentName(r, currentZoom()) || r.formatted_address || '');
            const exact = n === wanted, contains = wanted && (n.includes(wanted) || wanted.includes(n));
            return { r, d, s: (exact ? 520 : contains ? 220 : 0) + (gvGeoType003(types) ? 220 : -320) + Math.max(0, 100 - Math.min(100, d / 180)) };
        }).filter(x => x.r?.place_id && x.d <= 35000).sort((a,b) => b.s-a.s);
        if (ranked[0]) {
            const r = ranked[0].r, loc = r.geometry?.location;
            return { ...p, placeId: r.place_id, lat: loc ? loc.lat() : p.lat, lon: loc ? loc.lng() : p.lon, address: clean(r.formatted_address || p.address), parent: componentParent(r, p.name) || p.parent, source: 'Google Maps' };
        }
    } catch { }
    try {
        const lib = await google.maps.importLibrary('places'), P = lib.Place, q = [p.name, p.parent].filter(Boolean).join(', ');
        const { places } = await P.searchByText({ textQuery: q, fields: ['id', 'displayName', 'location', 'formattedAddress', 'types'], locationBias: origin, language: 'it', region: 'IT', maxResultCount: 8 });
        const wanted = norm(p.name || '');
        const ranked = (places || []).filter(pl => pl.id && pl.location).map(pl => {
            const lat = typeof pl.location.lat === 'function' ? pl.location.lat() : Number(pl.location.lat), lng = typeof pl.location.lng === 'function' ? pl.location.lng() : Number(pl.location.lng), d = metersBetween(origin, { lat, lng }), n = norm(pl.displayName || ''), exact = n === wanted, contains = wanted && (n.includes(wanted) || wanted.includes(n));
            return { pl, lat, lng, d, s: (exact ? 520 : contains ? 220 : 0) + (gvGeoType003(pl.types) ? 220 : -320) + Math.max(0, 100 - Math.min(100, d / 180)) };
        }).filter(x => x.d <= 35000).sort((a,b) => b.s-a.s);
        const best = ranked[0];
        if (best) return { ...p, placeId: String(best.pl.id), lat: best.lat, lon: best.lng, address: clean(best.pl.formattedAddress || p.address), source: 'Google Places' };
    } catch { }
    return p;
}
async function gvTerritoryPhotos003(p) {
    if (!googleReady || !p || p.isPoi || !p.name) return [];
    const urls = [], seen = new Set(), origin = { lat: Number(p.lat), lng: Number(p.lon) };
    const addUrl = u => { u = clean(u || ''); if (u && !u.startsWith('data:') && !seen.has(u) && urls.length < 3) { seen.add(u); urls.push(u); } };
    const addPhotos = photos => { for (const ph of photos || []) { if (urls.length >= 3) break; addUrl(gvPhotoUrl003(ph)); } };
    let rp = await gvResolveGeoPlace003(p);
    if (rp?.placeId && !p.placeId) {
        p.placeId = rp.placeId;
        if (rp.address) p.address = rp.address;
    }
    try {
        const lib = await google.maps.importLibrary('places'), P = lib.Place;
        if (p.placeId) {
            try {
                const direct = new P({ id: p.placeId });
                await direct.fetchFields({ fields: ['displayName', 'types', 'photos'] });
                addPhotos(Array.isArray(direct.photos) ? direct.photos : []);
            } catch { }
        }
        const parentShort = clean(String(p.parent || '').split(',')[0] || '');
        const queries = [
            [p.name, parentShort].filter(Boolean).join(', '),
            clean(p.name || ''),
            `Comune di ${clean(p.name || '')}`,
            `${clean(p.name || '')} Italia`
        ].filter((q,i,a) => q && a.indexOf(q) === i);
        for (const q of queries) {
            if (urls.length >= 3) break;
            try {
                const { places } = await P.searchByText({ textQuery: q, fields: ['id', 'displayName', 'location', 'types', 'photos'], locationBias: origin, language: 'it', region: 'IT', maxResultCount: 10 });
                const wanted = norm(p.name || '');
                const ranked = (places || []).filter(pl => pl.id && pl.location).map(pl => {
                    const lat = typeof pl.location.lat === 'function' ? pl.location.lat() : Number(pl.location.lat), lng = typeof pl.location.lng === 'function' ? pl.location.lng() : Number(pl.location.lng), d = metersBetween(origin, { lat, lng }), n = norm(pl.displayName || ''), exact = n === wanted, contains = wanted && (n.includes(wanted) || wanted.includes(n)), geo = gvGeoType003(pl.types), commercial = gvCommercialType003(pl.types), photos = Array.isArray(pl.photos) ? pl.photos.length : 0;
                    return { pl, d, exact, contains, geo, s: (exact ? 620 : contains ? 260 : 0) + (geo ? 220 : 0) - (commercial && !exact ? 420 : 0) + Math.max(0, 120 - Math.min(120, d / 160)) + photos * 35 };
                }).filter(x => x.d <= 35000 && (x.geo || x.exact || x.contains)).sort((a,b) => b.s-a.s);
                for (const item of ranked.slice(0, 5)) {
                    addPhotos(Array.isArray(item.pl.photos) ? item.pl.photos : []);
                    if (urls.length < 3 && item.pl.id) {
                        try { const detail = new P({ id: String(item.pl.id) }); await detail.fetchFields({ fields: ['photos'] }); addPhotos(Array.isArray(detail.photos) ? detail.photos : []); } catch { }
                    }
                    if (urls.length >= 3) break;
                }
            } catch { }
        }
    } catch { }
    if (!urls.length) {
        const queries = [[p.name, p.parent].filter(Boolean).join(', '), clean(p.name || '')].filter((q,i,a)=>q && a.indexOf(q)===i);
        for (const q of queries) {
            try {
                const rows = await legacyGoogleTextPhotos(q, p), wanted = norm(p.name || '');
                const ranked = (rows || []).map(r => {
                    const loc = r.geometry?.location, lat = loc ? loc.lat() : origin.lat, lng = loc ? loc.lng() : origin.lng, d = metersBetween(origin, { lat, lng }), n = norm(r.name || ''), exact = n === wanted, contains = wanted && (n.includes(wanted) || wanted.includes(n)), geo = gvGeoType003(r.types), commercial = gvCommercialType003(r.types), photos = Array.isArray(r.photos) ? r.photos.length : 0;
                    return { r, d, exact, contains, geo, s: (exact ? 620 : contains ? 260 : 0) + (geo ? 220 : 0) - (commercial && !exact ? 420 : 0) + Math.max(0, 120 - Math.min(120, d / 160)) + photos * 35 };
                }).filter(x => x.d <= 35000 && (x.geo || x.exact || x.contains)).sort((a,b)=>b.s-a.s);
                for (const item of ranked.slice(0,5)) { addPhotos(Array.isArray(item.r.photos) ? item.r.photos : []); if (urls.length >= 3) break; }
            } catch { }
            if (urls.length) break;
        }
    }
    window.gvPhotoRepair003 = { name: clean(p.name || ''), kind: clean(p.kind || ''), placeId: clean(p.placeId || ''), urls: urls.length };
    return urls;
}
'''
s=s.replace(anchor,helper+anchor,1)
old='''async function renderOfficialGoogleCard(p) { const body = $('#sheetBody'); body.innerHTML = '<div id="googleCityPhotos" class="google-city-photos"></div><div id="googleCardHost" class="google-card-host"><div class="loading">Carico la scheda Google…</div></div><div id="audioGuide" class="audio-guide"><div class="loading">Preparo l’audioguida…</div></div>'; $('#sheet').classList.add('show'); const host = $('#googleCardHost'), cityLocality = isOfficialCityLocality(p), photoHost = $('#googleCityPhotos'); if (cityLocality) {
    void googleLocalityPhotos(p).then(urls => { if (current !== p || !photoHost?.isConnected || !urls.length)
        return; photoHost.innerHTML = `<div class="google-photo-strip">${urls.map(u => `<img src="${esc(u)}" alt="${esc(p.name)}">`).join('')}</div>`; });
} if (!p.placeId) {'''
new='''async function renderOfficialGoogleCard(p) { const body = $('#sheetBody'); body.innerHTML = '<div id="googleCityPhotos" class="google-city-photos"></div><div id="googleCardHost" class="google-card-host"><div class="loading">Carico la scheda Google…</div></div><div id="audioGuide" class="audio-guide"><div class="loading">Preparo l’audioguida…</div></div>'; $('#sheet').classList.add('show'); const host = $('#googleCardHost'), cityLocality = isOfficialCityLocality(p), photoHost = $('#googleCityPhotos'); if (!p.isPoi) {
    void (async () => { let urls = cityLocality ? await googleLocalityPhotos(p) : []; if (!urls.length) urls = await gvTerritoryPhotos003(p); if (current !== p || !photoHost?.isConnected || !urls.length)
        return; photoHost.innerHTML = `<div class="google-photo-strip">${urls.map(u => `<img src="${esc(u)}" alt="${esc(p.name)}">`).join('')}</div>`; })();
    if (!p.placeId) { const resolved = await gvResolveGeoPlace003(p); if (resolved?.placeId) { p.placeId = resolved.placeId; p.address = resolved.address || p.address; p.parent = resolved.parent || p.parent; } }
} if (!p.placeId) {'''
if old not in s:
    raise SystemExit('render anchor missing')
s=s.replace(old,new,1)
p.write_text(s,encoding='utf-8')
print('Applied LAB 003 photo repair:',len(s))
