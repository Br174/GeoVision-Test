from pathlib import Path
p=Path('/tmp/GeoVision_LAB_005_SOURCE.html')
s=p.read_text(encoding='utf-8')
anchor='async function renderOfficialGoogleCard(p) {'
if anchor not in s:
    raise SystemExit('render anchor missing')
helper=r'''function gvPhoto005Record(context, e) {
    const msg = clean([e?.code, e?.status, e?.name, e?.message, String(e || '')].filter(Boolean).join(' | '));
    const pool = typeof gvDiagLoadGoogleKeyPool === 'function' ? gvDiagLoadGoogleKeyPool() : { idx: 0 };
    window.gvPhotoStability005 = { context, message: msg, activeKey: Number(pool.idx || 0) + 1, at: Date.now() };
    try { localStorage.setItem('geovision_photo005_last_error', JSON.stringify(window.gvPhotoStability005)); } catch { }
    return msg;
}
async function gvPhotoRecover005(p) {
    if (!googleReady || !p || p.isPoi || !p.name) return { urls: [] };
    const origin = { lat: Number(p.lat), lng: Number(p.lon) };
    const query = [clean(p.name || ''), clean(String(p.parent || '').split(',')[0] || '')].filter(Boolean).join(', ');
    const run = async () => {
        const lib = await google.maps.importLibrary('places'), P = lib.Place;
        const { places } = await P.searchByText({ textQuery: query || clean(p.name || ''), fields: ['id', 'displayName', 'location', 'formattedAddress', 'types', 'photos'], locationBias: origin, language: 'it', region: 'IT', maxResultCount: 10 });
        const wanted = norm(p.name || '');
        const ranked = (places || []).filter(pl => pl.id && pl.location).map(pl => {
            const lat = typeof pl.location.lat === 'function' ? pl.location.lat() : Number(pl.location.lat), lng = typeof pl.location.lng === 'function' ? pl.location.lng() : Number(pl.location.lng), d = metersBetween(origin, { lat, lng }), n = norm(pl.displayName || ''), exact = n === wanted, contains = wanted && (n.includes(wanted) || wanted.includes(n)), geo = gvGeoType003(pl.types || []), commercial = gvCommercialType003(pl.types || []), photos = Array.isArray(pl.photos) ? pl.photos.length : 0;
            return { pl, lat, lng, d, exact, contains, geo, s: (exact ? 700 : contains ? 300 : 0) + (geo ? 240 : 0) - (commercial && !exact ? 450 : 0) + Math.max(0, 120 - Math.min(120, d / 160)) + photos * 35 };
        }).filter(x => x.d <= 35000 && (x.geo || x.exact || x.contains)).sort((a,b) => b.s-a.s);
        const best = ranked[0];
        if (!best) return { urls: [] };
        const urls = [], seen = new Set();
        const addPhotos = photos => { for (const ph of photos || []) { if (urls.length >= 3) break; const u = clean(gvPhotoUrl003(ph) || ''); if (u && !seen.has(u)) { seen.add(u); urls.push(u); } } };
        addPhotos(Array.isArray(best.pl.photos) ? best.pl.photos : []);
        if (urls.length < 3) {
            const detail = new P({ id: String(best.pl.id) });
            await detail.fetchFields({ fields: ['photos'] });
            addPhotos(Array.isArray(detail.photos) ? detail.photos : []);
        }
        window.gvPhotoStability005 = { context: 'ok', message: '', activeKey: (typeof gvDiagLoadGoogleKeyPool === 'function' ? gvDiagLoadGoogleKeyPool().idx : 0) + 1, at: Date.now(), placeId: String(best.pl.id), urls: urls.length };
        return { placeId: String(best.pl.id), lat: best.lat, lon: best.lng, address: clean(best.pl.formattedAddress || p.address), urls };
    };
    for (let attempt = 0; attempt < 2; attempt++) {
        try {
            const out = await run();
            if (out?.placeId || out?.urls?.length) return out;
        } catch (e) {
            gvPhoto005Record('places-' + (attempt + 1), e);
            if (typeof gvDiagAdvanceGoogleKey === 'function' && gvDiagAdvanceGoogleKey(e)) return { urls: [], switching: true };
        }
        if (!attempt) await new Promise(r => setTimeout(r, 450));
    }
    return { urls: [] };
}
'''
s=s.replace(anchor,helper+anchor,1)
old='''async function renderOfficialGoogleCard(p) { const body = $('#sheetBody'); body.innerHTML = '<div id="googleCityPhotos" class="google-city-photos"></div><div id="googleCardHost" class="google-card-host"><div class="loading">Carico la scheda Google…</div></div><div id="audioGuide" class="audio-guide"><div class="loading">Preparo l’audioguida…</div></div>'; $('#sheet').classList.add('show'); const host = $('#googleCardHost'), cityLocality = isOfficialCityLocality(p), photoHost = $('#googleCityPhotos'); if (!p.isPoi) {
    void (async () => { let urls = cityLocality ? await googleLocalityPhotos(p) : []; if (!urls.length) urls = await gvTerritoryPhotos003(p); if (current !== p || !photoHost?.isConnected || !urls.length)
        return; photoHost.innerHTML = `<div class="google-photo-strip">${urls.map(u => `<img src="${esc(u)}" alt="${esc(p.name)}">`).join('')}</div>`; })();
    if (!p.placeId) { const resolved = await gvResolveGeoPlace003(p); if (resolved?.placeId) { p.placeId = resolved.placeId; p.address = resolved.address || p.address; p.parent = resolved.parent || p.parent; } }
} if (!p.placeId) {'''
new='''async function renderOfficialGoogleCard(p) { const body = $('#sheetBody'); body.innerHTML = '<div id="googleCityPhotos" class="google-city-photos"></div><div id="googleCardHost" class="google-card-host"><div class="loading">Carico la scheda Google…</div></div><div id="audioGuide" class="audio-guide"><div class="loading">Preparo l’audioguida…</div></div>'; $('#sheet').classList.add('show'); const host = $('#googleCardHost'), cityLocality = isOfficialCityLocality(p), photoHost = $('#googleCityPhotos'); if (!p.isPoi) {
    let gvRecoverPromise005 = null; const gvRecover005 = () => gvRecoverPromise005 || (gvRecoverPromise005 = gvPhotoRecover005(p));
    void (async () => { let urls = cityLocality ? await googleLocalityPhotos(p) : []; if (!urls.length) urls = await gvTerritoryPhotos003(p); if (!urls.length) { const rr = await gvRecover005(); urls = rr?.urls || []; } if (current !== p || !photoHost?.isConnected || !urls.length)
        return; photoHost.innerHTML = `<div class="google-photo-strip">${urls.map(u => `<img src="${esc(u)}" alt="${esc(p.name)}">`).join('')}</div>`; })();
    if (!p.placeId) { const rr = await gvRecover005(); if (rr?.placeId) { p.placeId = rr.placeId; p.address = rr.address || p.address; p.lat = Number.isFinite(rr.lat) ? rr.lat : p.lat; p.lon = Number.isFinite(rr.lon) ? rr.lon : p.lon; } else { const resolved = await gvResolveGeoPlace003(p); if (resolved?.placeId) { p.placeId = resolved.placeId; p.address = resolved.address || p.address; p.parent = resolved.parent || p.parent; } } }
} if (!p.placeId) {'''
if old not in s:
    raise SystemExit('render block anchor missing')
s=s.replace(old,new,1)
p.write_text(s,encoding='utf-8')
print('Applied LAB 005 photo stability:',len(s))
