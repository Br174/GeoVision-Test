from pathlib import Path

p = Path('/tmp/GeoVision_MADRE_001_SOURCE.html')
s = p.read_text(encoding='utf-8')

anchor = """catch { }
function setGoogleKeyState(state)"""
insert = r"""catch { }

// GeoVision LAB: failover automatico fra 3 chiavi Google.
// La chiave attiva resta stabile finche funziona; si cambia solo su errori quota/autorizzazione.
const GV_GOOGLE_KEY_FAILOVER_COOLDOWN = 60 * 60 * 1000;
let gvGoogleKeys = [], gvGoogleActiveKeyIndex = -1, gvGoogleKeySwitching = false;
function gvReadGoogleFailures() {
    try { const x = JSON.parse(localStorage.getItem('geovision_google_key_failures') || '{}'); return x && typeof x === 'object' ? x : {}; }
    catch { return {}; }
}
function gvWriteGoogleFailures(x) { try { localStorage.setItem('geovision_google_key_failures', JSON.stringify(x || {})); } catch { } }
function gvGoogleKeyBlocked(i, failures = gvReadGoogleFailures()) {
    const t = Number(failures[String(i)] || 0);
    return !!t && (Date.now() - t) < GV_GOOGLE_KEY_FAILOVER_COOLDOWN;
}
function gvLoadGoogleKeyPool() {
    let stored = [];
    try {
        stored = [1,2,3].map(i => clean(localStorage.getItem('geovision_google_maps_api_key_' + i) || ''));
        if (!stored.some(Boolean)) {
            const arr = JSON.parse(localStorage.getItem('geovision_google_maps_api_keys') || '[]');
            if (Array.isArray(arr)) stored = [0,1,2].map(i => clean(arr[i] || ''));
        }
    } catch { stored = []; }
    if (!stored.some(Boolean) && googleKey) stored = [clean(googleKey), '', ''];
    gvGoogleKeys = [0,1,2].map(i => clean(stored[i] || ''));
    let saved = -1;
    try { saved = Number(localStorage.getItem('geovision_google_active_key_index')); } catch { }
    const failures = gvReadGoogleFailures();
    const validSaved = Number.isInteger(saved) && saved >= 0 && saved < 3 && !!gvGoogleKeys[saved];
    let pick = validSaved && !gvGoogleKeyBlocked(saved, failures) ? saved : gvGoogleKeys.findIndex((k,i) => !!k && !gvGoogleKeyBlocked(i, failures));
    // Se tutte risultano temporaneamente bloccate, ritesta quella gia attiva (o la prima): niente loop automatico.
    if (pick < 0) pick = validSaved ? saved : gvGoogleKeys.findIndex(Boolean);
    if (pick >= 0) {
        gvGoogleActiveKeyIndex = pick;
        googleKey = gvGoogleKeys[pick];
        try {
            localStorage.setItem('geovision_google_active_key_index', String(pick));
            localStorage.setItem('geovision_google_maps_api_key', googleKey);
        } catch { }
    }
}
function gvGoogleErrorText(e) {
    try { return clean([e?.code, e?.status, e?.name, e?.message, String(e || '')].filter(Boolean).join(' | ')); }
    catch { return String(e || ''); }
}
function gvIsGoogleKeyFailure(e) {
    const t = gvGoogleErrorText(e);
    return /RESOURCE_EXHAUSTED|OVER_QUERY_LIMIT|quota exceeded|quota metric|429|REQUEST_DENIED|API.?key.*(?:invalid|not valid|denied)|InvalidKey|ApiNotActivated|BillingNotEnabled|RefererNotAllowed|authentication failure/i.test(t);
}
function gvMarkGoogleKeyHealthy() {
    if (gvGoogleActiveKeyIndex < 0) return;
    const failures = gvReadGoogleFailures();
    if (failures[String(gvGoogleActiveKeyIndex)]) {
        delete failures[String(gvGoogleActiveKeyIndex)];
        gvWriteGoogleFailures(failures);
    }
    try { localStorage.setItem('geovision_google_last_good_key_index', String(gvGoogleActiveKeyIndex)); } catch { }
}
function gvRotateGoogleKey(e) {
    if (gvGoogleKeySwitching || gvGoogleActiveKeyIndex < 0 || !gvIsGoogleKeyFailure(e)) return false;
    const failures = gvReadGoogleFailures();
    failures[String(gvGoogleActiveKeyIndex)] = Date.now();
    gvWriteGoogleFailures(failures);
    let next = -1;
    for (let step = 1; step <= 3; step++) {
        const i = (gvGoogleActiveKeyIndex + step) % 3;
        if (gvGoogleKeys[i] && !gvGoogleKeyBlocked(i, failures)) { next = i; break; }
    }
    if (next < 0) {
        setGoogleKeyState('error');
        try { localStorage.setItem('geovision_google_all_keys_unavailable_at', String(Date.now())); } catch { }
        toast('Le chiavi Google disponibili risultano esaurite. Riprovero una chiave al prossimo utilizzo.');
        return false;
    }
    gvGoogleKeySwitching = true;
    const old = gvGoogleActiveKeyIndex;
    gvGoogleActiveKeyIndex = next;
    googleKey = gvGoogleKeys[next];
    try {
        localStorage.setItem('geovision_google_active_key_index', String(next));
        localStorage.setItem('geovision_google_maps_api_key', googleKey);
        localStorage.setItem('geovision_google_last_switch_reason', gvGoogleErrorText(e).slice(0, 500));
    } catch { }
    setGoogleKeyState('checking');
    toast('Chiave Google ' + (old + 1) + ' non disponibile · passo alla ' + (next + 1));
    setTimeout(() => location.reload(), 450);
    return true;
}
function gvWrapGoogleMethod(obj, name) {
    if (!obj || typeof obj[name] !== 'function' || obj[name].__gvKeyFailoverWrapped) return;
    const original = obj[name];
    const wrapped = async function(...args) {
        try {
            const out = await original.apply(this, args);
            gvMarkGoogleKeyHealthy();
            return out;
        } catch (e) {
            gvRotateGoogleKey(e);
            throw e;
        }
    };
    wrapped.__gvKeyFailoverWrapped = true;
    try { obj[name] = wrapped; } catch { }
    if (obj[name] !== wrapped) {
        try { Object.defineProperty(obj, name, { value: wrapped, configurable: true, writable: true }); } catch { }
    }
}
async function gvInstallGoogleKeyFailoverHooks() {
    try {
        const lib = await google.maps.importLibrary('places');
        const P = lib?.Place;
        gvWrapGoogleMethod(P, 'searchByText');
        gvWrapGoogleMethod(P, 'searchNearby');
        gvWrapGoogleMethod(P?.prototype, 'fetchFields');
    } catch (e) { gvRotateGoogleKey(e); }
}
gvLoadGoogleKeyPool();
window.gm_authFailure = () => gvRotateGoogleKey(new Error('Google Maps authentication failure'));

function setGoogleKeyState(state)"""
if anchor not in s:
    raise SystemExit('initial key anchor missing')
s = s.replace(anchor, insert, 1)

anchor2 = """    await loadGoogleMaps();
    const c = map.getCenter();"""
replace2 = """    await loadGoogleMaps();
    await gvInstallGoogleKeyFailoverHooks();
    const c = map.getCenter();"""
if anchor2 not in s:
    raise SystemExit('initGoogleMaps anchor missing')
s = s.replace(anchor2, replace2, 1)

old = """    add('Chiave API', googleKey ? 'ok' : 'bad', googleKey ? 'Chiave presente' : 'Chiave non configurata');"""
new = """    add('Chiave API', googleKey ? 'ok' : 'bad', googleKey ? ('Chiave presente · Google ' + (gvGoogleActiveKeyIndex + 1) + ' / 3 attiva') : 'Chiave non configurata');"""
if old not in s:
    raise SystemExit('diagnostic key row anchor missing')
s = s.replace(old, new, 1)

assert 'gvRotateGoogleKey' in s
assert 'gvInstallGoogleKeyFailoverHooks' in s
assert 'RESOURCE_EXHAUSTED' in s
assert 'geovision_google_active_key_index' in s
assert "Google ' + (gvGoogleActiveKeyIndex + 1) + ' / 3 attiva" in s
p.write_text(s, encoding='utf-8')
print('google key failover patched', p.stat().st_size)
