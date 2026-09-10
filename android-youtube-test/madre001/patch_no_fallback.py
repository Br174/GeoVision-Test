from pathlib import Path
p=Path('/tmp/GeoVision_MADRE_001_SOURCE.html')
s=p.read_text(encoding='utf-8')

old_func="""function fallbackGeoCard(p, photo = '') { return `${photo ? `<img class=\"geo-photo\" src=\"${esc(photo)}\" alt=\"${esc(p.name)}\">` : ''}<div class=\"place-copy\"><div class=\"meta\">Scheda GeoVision</div><h2>${esc(p.name)}</h2><div class=\"meta\">${esc(p.address || p.kind)}</div><div class=\"actions\"><button id=\"openGoogleCard\" class=\"primary\">Apri in Google Maps</button></div></div>`; }
"""
if old_func not in s:
    raise SystemExit('fallbackGeoCard definition not found')
s=s.replace(old_func,'',1)

old_no_place="""} if (!p.placeId) {
    if (cityLocality) {
        host.innerHTML = '<div class=\"loading\">Carico la scheda Google…</div>';
        return;
    }
    const w = await wikiInfo(p);
    host.innerHTML = fallbackGeoCard(p, w.photo || '');
    const b = document.getElementById('openGoogleCard');
    if (b)
        b.onclick = () => openUrl(googlePlaceUrl(p));
    return;
} let extraPhoto = '';"""
new_no_place="""} if (!p.placeId) {
    host.innerHTML = '';
    host.style.display = 'none';
    return;
} let extraPhoto = '';"""
if old_no_place not in s:
    raise SystemExit('no-place fallback block not found')
s=s.replace(old_no_place,new_no_place,1)

old_catch="""catch {
    if (host.querySelector('gmp-place-details'))
        return;
    if (p.placeId) {
        if (!host.querySelector('.geo-photo'))
            host.innerHTML = '<div class=\"loading\">Carico la scheda Google…</div>';
        return;
    }
    host.innerHTML = fallbackGeoCard(p, extraPhoto);
    const b = document.getElementById('openGoogleCard');
    if (b)
        b.onclick = () => openUrl(googlePlaceUrl(p));
} }"""
new_catch="""catch {
    if (host.querySelector('gmp-place-details'))
        return;
    host.innerHTML = '';
    host.style.display = 'none';
    return;
} }"""
if old_catch not in s:
    raise SystemExit('catch fallback block not found')
s=s.replace(old_catch,new_catch,1)

# Safety assertions: no fake card remains; header controls must remain untouched.
assert 'fallbackGeoCard' not in s
assert 'Scheda GeoVision' not in s
assert 'id=\"voice\"' in s
assert 'id=\"sheetVideo\"' in s
assert 'id=\"sheetPhotosVisual\"' in s
assert 'id=\"sheetClose\"' in s
assert 'id=\"audioGuide\"' in s
assert 'gmp-place-details' in s

p.write_text(s,encoding='utf-8')
print('no-fallback patched',p.stat().st_size)
