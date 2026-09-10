from pathlib import Path

p = Path('/tmp/GeoVision_MADRE_001_SOURCE.html')
s = p.read_text(encoding='utf-8')

anchor = """catch { }
function setGoogleKeyState(state)"""
insert = r"""catch { }

// GeoVision LAB SAFE: failover 3 chiavi Google senza wrapper globali sui metodi Google.
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
function gvRotateGoogleKeySafe(e) {
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
        toast('Tutte le chiavi Google disponibili risultano temporaneamente non utilizzabili.');
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
    toast('Chiave Google ' + (old + 1) + ' esaurita · passo alla ' + (next + 1));
    setTimeout(() => location.reload(), 800);
    return true;
}
gvLoadGoogleKeyPool();

function setGoogleKeyState(state)"""
if anchor not in s:
    raise SystemExit('initial key anchor missing')
s = s.replace(anchor, insert, 1)

old = """        catch (e) {
            bad++;
            add('Ricerca Places', 'bad', clean(e?.message || 'Ricerca fallita'));
        }"""
new = """        catch (e) {
            if (gvRotateGoogleKeySafe(e)) {
                add('Ricerca Places', 'warn', 'Quota chiave esaurita: passo automaticamente alla chiave successiva…');
                return;
            }
            bad++;
            add('Ricerca Places', 'bad', clean(e?.message || 'Ricerca fallita'));
        }"""
if old not in s:
    raise SystemExit('diagnostic search catch anchor missing')
s = s.replace(old, new, 1)

old2 = """    add('Chiave API', googleKey ? 'ok' : 'bad', googleKey ? 'Chiave presente' : 'Chiave non configurata');"""
new2 = """    add('Chiave API', googleKey ? 'ok' : 'bad', googleKey ? ('Chiave presente · Google ' + (gvGoogleActiveKeyIndex + 1) + ' / 3 attiva') : 'Chiave non configurata');"""
if old2 not in s:
    raise SystemExit('diagnostic key row anchor missing')
s = s.replace(old2, new2, 1)

assert 'gvRotateGoogleKeySafe' in s
assert 'RESOURCE_EXHAUSTED' in s
assert 'googleDiagPanel' in s
assert "keyStatusEl.onclick" in s
assert "Google ' + (gvGoogleActiveKeyIndex + 1) + ' / 3 attiva" in s
assert 'gvInstallGoogleKeyFailoverHooks' not in s
assert 'gm_authFailure' not in s
p.write_text(s, encoding='utf-8')
print('google key failover SAFE patched', p.stat().st_size)
