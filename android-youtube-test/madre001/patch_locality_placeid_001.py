from pathlib import Path

p = Path('/tmp/GeoVision_MADRE_001_SOURCE.html')
s = p.read_text(encoding='utf-8')

start = s.find('async function richLocalityPlace(p)')
end = s.find('async function resolveLocality(lat, lng)', start)
if start < 0 or end < 0:
    raise SystemExit('richLocalityPlace block not found')

old = s[start:end]
if "includedType: 'locality'" not in old or 'useStrictTypeFiltering: true' not in old:
    raise SystemExit('expected strict locality resolver not found')

new = r'''// LAB LOCALITY PLACEID 001: resolve municipalities/cities to the exact Google entity,
// without forcing the result to the narrower `locality` type. This is intentionally
// isolated from the official Google card rendering.
async function richLocalityPlace(p) {
    const z = currentZoom(), cityLike = /città|paese|comune/i.test(p.kind || '');
    if (!googleReady || !p.name || z >= 15 || !cityLike) return p;

    const ck = norm([p.name, p.parent].filter(Boolean).join('|'));
    const cached = richLocalityCache.get(ck);
    if (cached) return cached;

    try {
        const lib = await google.maps.importLibrary('places'), P = lib.Place;
        const { places } = await P.searchByText({
            textQuery: [p.name, p.parent].filter(Boolean).join(', '),
            fields: ['id', 'displayName', 'location', 'formattedAddress', 'types', 'photos'],
            locationBias: { lat: p.lat, lng: p.lon },
            language: 'it',
            region: 'IT',
            maxResultCount: 8
        });

        const wanted = norm(p.name);
        const parentHead = norm((p.parent || '').split(',')[0] || '');
        const rows = (places || []).filter(pl => pl.id && pl.location).map(pl => {
            const lat = typeof pl.location.lat === 'function' ? pl.location.lat() : Number(pl.location.lat);
            const lng = typeof pl.location.lng === 'function' ? pl.location.lng() : Number(pl.location.lng);
            const display = norm(pl.displayName || '');
            const types = Array.isArray(pl.types) ? pl.types : [];
            const geo = types.some(t =>
                t === 'locality' || t === 'postal_town' || t === 'political' ||
                t === 'neighborhood' || t.startsWith('administrative_area_') ||
                t.startsWith('sublocality')
            );
            const exact = display === wanted;
            const contains = wanted && display.includes(wanted);
            const addr = norm(pl.formattedAddress || '');
            const parentMatch = parentHead && addr.includes(parentHead) ? 70 : 0;
            const near = Math.max(0, 90 - Math.min(90,
                metersBetween({ lat: p.lat, lng: p.lon }, { lat, lng }) / 650));
            const photoScore = Array.isArray(pl.photos) ? Math.min(90, pl.photos.length * 18) : 0;
            const score = (exact ? 520 : contains ? 90 : 0) +
                (geo ? 160 : -600) + parentMatch + near + photoScore;
            return { pl, lat, lng, geo, exact, score };
        });

        // Prefer geographical/administrative entities. Only fall back to a non-geographic
        // item when its display name is an exact match, preventing businesses with the same
        // locality text from replacing the town/municipality.
        const geoRows = rows.filter(x => x.geo);
        const ranked = (geoRows.length ? geoRows : rows.filter(x => x.exact))
            .sort((a, b) => b.score - a.score);
        const best = ranked[0];
        if (!best) return p;

        const rich = {
            ...p,
            name: clean(best.pl.displayName || p.name),
            lat: best.lat,
            lon: best.lng,
            address: clean(best.pl.formattedAddress || p.address),
            placeId: String(best.pl.id),
            isPoi: false,
            source: 'Google Places'
        };
        richLocalityCache.set(ck, rich);
        return rich;
    } catch {
        return p;
    }
}
'''

s = s[:start] + new + s[end:]
assert 'LAB LOCALITY PLACEID 001' in s
p.write_text(s, encoding='utf-8')
print('locality Place ID resolver patched')
