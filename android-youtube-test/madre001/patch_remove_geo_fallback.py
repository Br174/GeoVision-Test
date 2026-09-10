from pathlib import Path

p=Path('/tmp/GeoVision_MADRE_001_SOURCE.html')
s=p.read_text(encoding='utf-8')

old_func = """function fallbackGeoCard(p, photo = '') { return `${photo ? `<img class=\"geo-photo\" src=\"${esc(photo)}\" alt=\"${esc(p.name)}\">` : ''}<div class=\"place-copy\"><div class=\"meta\">Scheda GeoVision</div><h2>${esc(p.name)}</h2><div class=\"meta\">${esc(p.address || p.kind)}</div><div class=\"actions\"><button id=\"openGoogleCard\" class=\"primary\">Apri in Google Maps</button></div></div>`; }\n"""
if old_func not in s:
    raise SystemExit('fallbackGeoCard function not found')
s=s.replace(old_func, '', 1)

old_noid = """} if (!p.placeId) {
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
new_noid = """} if (!p.placeId) {
    if (photoHost?.isConnected)
        photoHost.remove();
    if (host?.isConnected)
        host.remove();
    return;
} let extraPhoto = '';"""
if old_noid not in s:
    raise SystemExit('no-placeId fallback block not found')
s=s.replace(old_noid, new_noid, 1)

old_error = """    details.addEventListener('gmp-error', () => setGoogleKeyState('error'), { once: true });
    host.appendChild(details);"""
new_error = """    details.addEventListener('gmp-error', () => {
        setGoogleKeyState('error');
        if (current === p) {
            if (photoHost?.isConnected)
                photoHost.remove();
            if (host?.isConnected)
                host.remove();
        }
    }, { once: true });
    host.appendChild(details);"""
if old_error not in s:
    raise SystemExit('gmp-error handler not found')
s=s.replace(old_error, new_error, 1)

old_catch = """catch {
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
new_catch = """catch {
    if (host.querySelector('gmp-place-details'))
        return;
    if (photoHost?.isConnected)
        photoHost.remove();
    if (host?.isConnected)
        host.remove();
} }"""
if old_catch not in s:
    raise SystemExit('render catch fallback block not found')
s=s.replace(old_catch, new_catch, 1)

if 'fallbackGeoCard' in s or 'Scheda GeoVision' in s:
    raise SystemExit('fallback graphics still present after patch')

p.write_text(s, encoding='utf-8')
print('NO_FALLBACK_PATCH_OK', p.stat().st_size)
