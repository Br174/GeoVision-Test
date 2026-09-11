from pathlib import Path
p=Path('/tmp/GeoVision_LAB_001_SOURCE.html')
s=p.read_text(encoding='utf-8')
anchor='async function reverseFallback'
idx=s.find(anchor)
if idx < 0:
    raise SystemExit('reverseFallback anchor not found')
if 'gvPhotoDiagProbe' in s:
    raise SystemExit('diagnostic already present')
insert=r'''async function gvPhotoDiagProbe(p) {
    const d = { place: clean(p?.name || ''), kind: clean(p?.kind || ''), parent: clean(p?.parent || ''), placeId: clean(p?.placeId || ''), googleReady: !!googleReady, directPhotos: null, directName: '', textResults: [], legacyResults: [], errors: [] };
    try {
        const lib = await google.maps.importLibrary('places'), P = lib.Place;
        if (p?.placeId) {
            try {
                const direct = new P({ id: p.placeId });
                await direct.fetchFields({ fields: ['displayName', 'photos'] });
                d.directName = clean(direct.displayName || '');
                d.directPhotos = Array.isArray(direct.photos) ? direct.photos.length : 0;
            } catch (e) { d.errors.push('DETAILS: ' + clean(e?.message || e)); }
        }
        try {
            const q = [p?.name, p?.parent].filter(Boolean).join(', ');
            const res = await P.searchByText({ textQuery: q, fields: ['id', 'displayName', 'location', 'photos'], locationBias: { lat: Number(p?.lat), lng: Number(p?.lon) }, language: 'it', region: 'IT', maxResultCount: 5 });
            d.textResults = (res.places || []).slice(0, 5).map(pl => ({ name: clean(pl.displayName || ''), photos: Array.isArray(pl.photos) ? pl.photos.length : 0, id: clean(pl.id || '') }));
        } catch (e) { d.errors.push('TEXT: ' + clean(e?.message || e)); }
        try {
            const q = [p?.name, p?.parent].filter(Boolean).join(', ');
            const legacy = await legacyGoogleTextPhotos(q, p);
            d.legacyResults = (legacy || []).slice(0, 5).map(pl => ({ name: clean(pl.name || ''), photos: Array.isArray(pl.photos) ? pl.photos.length : 0, id: clean(pl.place_id || '') }));
        } catch (e) { d.errors.push('LEGACY: ' + clean(e?.message || e)); }
    } catch (e) { d.errors.push('PLACES: ' + clean(e?.message || e)); }
    window.gvPhotoDiag = d;
    try { console.info('[GeoVisionPhotoDiag002]', JSON.stringify(d)); } catch { }
    return d;
}
function gvRenderPhotoDiag(d) {
    const host = document.getElementById('googleCityPhotos');
    if (!host || !host.isConnected) return;
    const escv = (v) => esc(clean(v == null ? '' : String(v)));
    const textRows = (d.textResults || []).map((r,i)=>`<div>${i+1}. ${escv(r.name)} · foto=${Number(r.photos)||0}</div>`).join('') || '<div>Text Search: nessun risultato</div>';
    const legacyRows = (d.legacyResults || []).map((r,i)=>`<div>${i+1}. ${escv(r.name)} · foto=${Number(r.photos)||0}</div>`).join('') || '<div>Legacy: nessun risultato</div>';
    const errors = (d.errors || []).map(e=>`<div>⚠ ${escv(e)}</div>`).join('');
    host.innerHTML = `<div id="gvPhotoDiagBox" style="margin:10px 12px;padding:10px 12px;border:1px solid #f59e0b;border-radius:12px;background:#fff7ed;color:#374151;font:12px/1.45 system-ui,sans-serif;text-align:left"><b>DIAGNOSI FOTO 002</b><div>Luogo: ${escv(d.place)} · ${escv(d.kind)}</div><div>Place ID: ${escv(d.placeId || 'assente')}</div><div>Place Details: ${escv(d.directName || '—')} · foto=${d.directPhotos == null ? 'errore/ND' : Number(d.directPhotos)||0}</div><div style="margin-top:6px"><b>Text Search senza filtro locality</b></div>${textRows}<div style="margin-top:6px"><b>Places legacy</b></div>${legacyRows}${errors ? `<div style="margin-top:6px"><b>Errori</b></div>${errors}` : ''}</div>`;
}
const gvOriginalGoogleLocalityPhotos = googleLocalityPhotos;
googleLocalityPhotos = async function(p) {
    const urls = await gvOriginalGoogleLocalityPhotos(p);
    if (Array.isArray(urls) && urls.length) return urls;
    try { gvRenderPhotoDiag(await gvPhotoDiagProbe(p)); } catch (e) { window.gvPhotoDiag = { place: clean(p?.name || ''), errors: ['WRAPPER: ' + clean(e?.message || e)] }; }
    return urls;
};
'''
s=s[:idx]+insert+s[idx:]
p.write_text(s,encoding='utf-8')
print('Applied diagnostic wrapper only. HTML bytes:',len(s))
