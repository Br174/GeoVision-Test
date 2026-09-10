from pathlib import Path
p=Path('/tmp/GeoVision_LAB_001_SOURCE.html')
s=p.read_text(encoding='utf-8')
old="function isOfficialCityLocality(p) { return !p.isPoi && /città|paese|comune/i.test(p.kind || ''); }"
new="function isOfficialCityLocality(p) { return !p.isPoi && /città|paese|comune|frazione|località|quartiere|territorio/i.test(p.kind || ''); }"
if old not in s:
    raise SystemExit('isOfficialCityLocality anchor not found')
s=s.replace(old,new,1)
start=s.find('async function googleLocalityPhotos(p) {')
if start < 0:
    raise SystemExit('googleLocalityPhotos start not found')
end=s.find('async function reverseFallback', start)
if end < 0:
    raise SystemExit('googleLocalityPhotos end anchor not found')
oldfn=s[start:end]
newfn=r'''async function googleLocalityPhotos(p) { if (!googleReady || !isOfficialCityLocality(p))
    return []; const urls = [], diag = { place: clean(p.name || ''), kind: clean(p.kind || ''), placeId: clean(p.placeId || ''), queries: [], candidates: [], errors: [] }; const addUrl = (u) => { u = clean(u || ''); if (u && !u.startsWith('data:') && !urls.includes(u) && urls.length < 3) urls.push(u); }; const add = (photos, source = '') => { for (const ph of photos || []) { if (urls.length >= 3) break; try { const u = typeof ph?.getURI === 'function' ? ph.getURI({ maxWidth: 1200, maxHeight: 720 }) || '' : typeof ph?.getUrl === 'function' ? ph.getUrl({ maxWidth: 1200, maxHeight: 720 }) || '' : ''; addUrl(u); } catch (e) { diag.errors.push(source + ':uri'); } } }; const geoTypes = (types) => (types || []).some(t => t === 'locality' || t === 'postal_town' || t === 'political' || t === 'neighborhood' || t === 'colloquial_area' || t.startsWith('sublocality') || t.startsWith('administrative_area_')); let anchor = { lat: Number(p.lat), lng: Number(p.lon) }; try { const c = currentCenter(); if (Number.isFinite(c?.lat) && Number.isFinite(c?.lng) && metersBetween(anchor, c) < 15000) anchor = { lat: c.lat, lng: c.lng }; } catch { } diag.anchor = anchor; try {
    const lib = await google.maps.importLibrary('places'), P = lib.Place;
    if (p.placeId) {
        try { const direct = new P({ id: p.placeId }); await direct.fetchFields({ fields: ['displayName', 'location', 'types', 'photos'] }); diag.candidates.push({ q: 'placeId', name: clean(direct.displayName || ''), types: direct.types || [], photos: Array.isArray(direct.photos) ? direct.photos.length : 0 }); add(Array.isArray(direct.photos) ? direct.photos : [], 'placeId'); } catch (e) { diag.errors.push('placeId:' + clean(e?.message || e)); }
    }
    if (urls.length < 3) {
        try {
            const q = [p.name, p.parent].filter(Boolean).join(', '); diag.queries.push(q + ' [locality]');
            const res = await P.searchByText({ textQuery: q, fields: ['id', 'displayName', 'location', 'photos', 'types'], includedType: 'locality', useStrictTypeFiltering: true, locationBias: anchor, language: 'it', region: 'IT', maxResultCount: 5 });
            const ranked = (res.places || []).filter(x => x.location).map(x => { const lat = typeof x.location.lat === 'function' ? x.location.lat() : Number(x.location.lat), lng = typeof x.location.lng === 'function' ? x.location.lng() : Number(x.location.lng), d = metersBetween(anchor, { lat, lng }); return { x, d, s: (norm(x.displayName || '') === norm(p.name) ? 220 : 0) + Math.max(0, 100 - Math.min(100, d / 120)) + (Array.isArray(x.photos) ? x.photos.length * 10 : 0) }; }).sort((a,b)=>b.s-a.s);
            for (const item of ranked) { diag.candidates.push({ q, name: clean(item.x.displayName || ''), types: item.x.types || [], photos: Array.isArray(item.x.photos) ? item.x.photos.length : 0, meters: Math.round(item.d) }); add(Array.isArray(item.x.photos) ? item.x.photos : [], 'locality'); if (urls.length >= 3) break; }
        } catch (e) { diag.errors.push('locality:' + clean(e?.message || e)); }
    }
    if (urls.length < 3) {
        const hints = [];
        try {
            const geocoder = new google.maps.Geocoder(), rr = await geocoder.geocode({ location: anchor });
            for (const r of rr.results || []) {
                for (const c of r.address_components || []) {
                    const ts = c.types || []; if (!ts.some(t => t === 'locality' || t === 'postal_town' || t === 'neighborhood' || t === 'colloquial_area' || t.startsWith('sublocality') || t === 'administrative_area_level_3')) continue;
                    const n = clean(c.long_name || c.short_name || ''); if (!n || norm(n) === norm(p.name) || norm(n) === norm(p.parent) || hints.some(h => norm(h) === norm(n))) continue; hints.push(n);
                }
            }
        } catch (e) { diag.errors.push('reverse:' + clean(e?.message || e)); }
        for (const hint of hints.slice(0, 4)) {
            if (urls.length >= 3) break;
            const q = [hint, p.name, p.parent].filter(Boolean).join(', '); diag.queries.push(q);
            try {
                const res = await P.searchByText({ textQuery: q, fields: ['id', 'displayName', 'location', 'photos', 'types'], locationBias: anchor, language: 'it', region: 'IT', maxResultCount: 8 });
                const ranked = (res.places || []).filter(x => x.location && geoTypes(x.types)).map(x => { const lat = typeof x.location.lat === 'function' ? x.location.lat() : Number(x.location.lat), lng = typeof x.location.lng === 'function' ? x.location.lng() : Number(x.location.lng), d = metersBetween(anchor, { lat, lng }), dn = norm(x.displayName || ''), hn = norm(hint), named = dn === hn || dn.includes(hn) || hn.includes(dn); return { x, d, named, s: (named ? 260 : 0) + Math.max(0, 120 - Math.min(120, d / 80)) + (Array.isArray(x.photos) ? x.photos.length * 12 : 0) }; }).filter(a => a.d <= 12000 && (a.named || a.d <= 3500)).sort((a,b)=>b.s-a.s);
                for (const item of ranked) { diag.candidates.push({ q, name: clean(item.x.displayName || ''), types: item.x.types || [], photos: Array.isArray(item.x.photos) ? item.x.photos.length : 0, meters: Math.round(item.d) }); add(Array.isArray(item.x.photos) ? item.x.photos : [], 'hint'); if (urls.length >= 3) break; }
            } catch (e) { diag.errors.push('hint:' + hint + ':' + clean(e?.message || e)); }
            if (urls.length < 3) {
                try { const legacy = await legacyGoogleTextPhotos(q, { ...p, lat: anchor.lat, lon: anchor.lng }); for (const r of legacy) { const loc = r.geometry?.location; if (!loc) continue; const d = metersBetween(anchor, { lat: loc.lat(), lng: loc.lng() }); if (d > 12000) continue; diag.candidates.push({ q: q + ' [legacy]', name: clean(r.name || ''), types: r.types || [], photos: Array.isArray(r.photos) ? r.photos.length : 0, meters: Math.round(d) }); if (geoTypes(r.types) || d <= 2500) add(Array.isArray(r.photos) ? r.photos : [], 'legacy'); if (urls.length >= 3) break; } } catch (e) { diag.errors.push('legacy:' + hint + ':' + clean(e?.message || e)); }
            }
        }
    }
} catch (e) { diag.errors.push('places:' + clean(e?.message || e)); } diag.urls = urls.length; window.gvPhotoDiag = diag; try { console.info('[GeoVisionPhoto]', JSON.stringify(diag)); } catch { } if (p.placeId && urls.length) googlePhotoCache.set(p.placeId, urls.slice()); return urls; }'''
s=s[:start]+newfn+s[end:]
p.write_text(s,encoding='utf-8')
print('Applied photo territory LAB patch:', len(oldfn), '->', len(newfn), 'bytes:', len(s))
