from pathlib import Path
p=Path('/tmp/GeoVision_LAB_001_SOURCE.html')
s=p.read_text(encoding='utf-8')

helper=r'''async function googleGeoPhotoFallback002(p) {
    if (!googleReady || !p || p.isPoi) return [];
    const urls = [], diag = { name: clean(p.name || ''), kind: clean(p.kind || ''), placeId: clean(p.placeId || ''), candidates: [], errors: [] };
    const add = photos => { for (const ph of photos || []) { if (urls.length >= 3) break; try { const u = typeof ph?.getURI === 'function' ? clean(ph.getURI({ maxWidth: 1200, maxHeight: 720 }) || '') : typeof ph?.getUrl === 'function' ? clean(ph.getUrl({ maxWidth: 1200, maxHeight: 720 }) || '') : ''; if (u && !u.startsWith('data:') && !urls.includes(u)) urls.push(u); } catch {} } };
    const geo = types => (types || []).some(t => t === 'locality' || t === 'postal_town' || t === 'political' || t === 'neighborhood' || t === 'colloquial_area' || t.startsWith('sublocality') || t.startsWith('administrative_area_'));
    const origin = { lat: Number(p.lat), lng: Number(p.lon) };
    try {
        const lib = await google.maps.importLibrary('places'), P = lib.Place;
        const queries = [clean(p.name || ''), [p.name, p.parent].filter(Boolean).join(', ')].filter((q, i, a) => q && a.indexOf(q) === i);
        for (const q of queries) {
            if (urls.length >= 3) break;
            try {
                const { places } = await P.searchByText({ textQuery: q, fields: ['id', 'displayName', 'location', 'photos', 'types'], locationBias: origin, language: 'it', region: 'IT', maxResultCount: 8 });
                const wanted = norm(p.name || '');
                const ranked = (places || []).filter(pl => pl.id && pl.location).map(pl => {
                    const lat = typeof pl.location.lat === 'function' ? pl.location.lat() : Number(pl.location.lat), lng = typeof pl.location.lng === 'function' ? pl.location.lng() : Number(pl.location.lng), d = metersBetween(origin, { lat, lng }), display = norm(pl.displayName || ''), exact = display === wanted, contains = wanted && (display.includes(wanted) || wanted.includes(display)), isGeo = geo(pl.types), photos = Array.isArray(pl.photos) ? pl.photos.length : 0;
                    return { pl, d, score: (exact ? 600 : contains ? 180 : 0) + (isGeo ? 220 : -500) + Math.max(0, 120 - Math.min(120, d / 120)) + photos * 24 };
                }).filter(x => x.d <= 30000).sort((a,b) => b.score-a.score);
                for (const item of ranked.slice(0, 3)) {
                    diag.candidates.push({ q, name: clean(item.pl.displayName || ''), id: String(item.pl.id || ''), photos: Array.isArray(item.pl.photos) ? item.pl.photos.length : 0, meters: Math.round(item.d) });
                    add(Array.isArray(item.pl.photos) ? item.pl.photos : []);
                    if (!urls.length && item.pl.id) {
                        try { const detail = new P({ id: String(item.pl.id) }); await detail.fetchFields({ fields: ['photos'] }); add(Array.isArray(detail.photos) ? detail.photos : []); } catch {}
                    }
                    if (urls.length >= 3) break;
                }
            } catch (e) { diag.errors.push('text:' + clean(e?.message || e)); }
        }
        if (!urls.length) {
            for (const q of queries) {
                try {
                    for (const r of await legacyGoogleTextPhotos(q, p)) {
                        const loc = r.geometry?.location;
                        if (!loc) continue;
                        const d = metersBetween(origin, { lat: loc.lat(), lng: loc.lng() });
                        if (d > 30000) continue;
                        const exact = norm(r.name || '') === norm(p.name || ''), isGeo = geo(r.types);
                        if (!exact && !isGeo) continue;
                        diag.candidates.push({ q: q + ' [legacy]', name: clean(r.name || ''), id: clean(r.place_id || ''), photos: Array.isArray(r.photos) ? r.photos.length : 0, meters: Math.round(d) });
                        add(Array.isArray(r.photos) ? r.photos : []);
                        if (urls.length >= 3) break;
                    }
                } catch (e) { diag.errors.push('legacy:' + clean(e?.message || e)); }
                if (urls.length) break;
            }
        }
    } catch (e) { diag.errors.push('places:' + clean(e?.message || e)); }
    diag.urls = urls.length;
    window.gvPhotoSafeDiag002 = diag;
    try { console.info('[GeoVisionPhotoSafe002]', JSON.stringify(diag)); } catch {}
    return urls;
}
'''

anchor="function isOfficialCityLocality(p) { return !p.isPoi && /città|paese|comune/i.test(p.kind || ''); }"
if anchor not in s:
    raise SystemExit('original locality classifier missing')
s=s.replace(anchor,helper+anchor,1)

old_city='''if (cityLocality) {
    void googleLocalityPhotos(p).then(urls => { if (current !== p || !photoHost?.isConnected || !urls.length)
        return; photoHost.innerHTML = `<div class="google-photo-strip">${urls.map(u => `<img src="${esc(u)}" alt="${esc(p.name)}">`).join('')}</div>`; });
}'''
new_city='''if (cityLocality) {
    void (async () => { let urls = await googleLocalityPhotos(p); if (!urls.length) urls = await googleGeoPhotoFallback002(p); if (current !== p || !photoHost?.isConnected || !urls.length)
        return; photoHost.innerHTML = `<div class="google-photo-strip">${urls.map(u => `<img src="${esc(u)}" alt="${esc(p.name)}">`).join('')}</div>`; })();
}'''
if old_city not in s:
    raise SystemExit('city photo path anchor missing')
s=s.replace(old_city,new_city,1)

old_extra='''let extraPhoto = ''; if (!p.isPoi && !cityLocality) {
    extraPhoto = p.photo || await googlePhotoForPlaceId(p.placeId);
    if (!extraPhoto) {
        const w = await wikiInfo(p);
        extraPhoto = w.photo || '';
    }
}'''
new_extra='''let extraPhoto = ''; if (!p.isPoi && !cityLocality) {
    extraPhoto = p.photo || await googlePhotoForPlaceId(p.placeId);
    if (!extraPhoto) {
        const urls = await googleGeoPhotoFallback002(p);
        extraPhoto = urls[0] || '';
    }
    if (!extraPhoto) {
        const w = await wikiInfo(p);
        extraPhoto = w.photo || '';
    }
}'''
if old_extra not in s:
    raise SystemExit('non-city photo path anchor missing')
s=s.replace(old_extra,new_extra,1)

p.write_text(s,encoding='utf-8')
print('Applied regression-safe photo fallback 002:', len(s))