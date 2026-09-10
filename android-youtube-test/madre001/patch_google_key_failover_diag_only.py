from pathlib import Path

p=Path('/tmp/GeoVision_MADRE_001_SOURCE.html')
s=p.read_text(encoding='utf-8')

anchor="""catch { }
function setGoogleKeyState(state)"""
insert=r"""catch { }

// LAB 003 CLEAN: selezione minima della chiave Google attiva.
// Nessun hook globale, nessuna modifica ai listener o ai pulsanti.
function gvDiagLoadGoogleKeyPool() {
    let keys=[];
    try {
        keys=[1,2,3].map(i => clean(localStorage.getItem('geovision_google_maps_api_key_' + i) || ''));
        if (!keys.some(Boolean)) {
            const arr=JSON.parse(localStorage.getItem('geovision_google_maps_api_keys') || '[]');
            if (Array.isArray(arr)) keys=[0,1,2].map(i => clean(arr[i] || ''));
        }
    } catch { keys=[]; }
    if (!keys.some(Boolean) && googleKey) keys=[clean(googleKey),'',''];
    let idx=0;
    try { idx=parseInt(localStorage.getItem('geovision_google_active_key_index') || '0',10); } catch { idx=0; }
    if (!Number.isInteger(idx) || idx<0 || idx>2 || !keys[idx]) idx=keys.findIndex(Boolean);
    if (idx<0) idx=0;
    const chosen=keys[idx] || '';
    if (chosen) {
        googleKey=chosen;
        try {
            localStorage.setItem('geovision_google_active_key_index', String(idx));
            localStorage.setItem('geovision_google_maps_api_key', chosen);
        } catch { }
    }
    return {keys, idx};
}
function gvDiagIsKeyFailure(e) {
    const t=clean([e?.code,e?.status,e?.name,e?.message,String(e||'')].filter(Boolean).join(' | '));
    return /RESOURCE_EXHAUSTED|OVER_QUERY_LIMIT|quota exceeded|quota metric|429|REQUEST_DENIED|API.?key.*(?:invalid|not valid|denied)|InvalidKey|ApiNotActivated|BillingNotEnabled|RefererNotAllowed|authentication failure/i.test(t);
}
function gvDiagAdvanceGoogleKey(e) {
    if (!gvDiagIsKeyFailure(e)) return false;
    const pool=gvDiagLoadGoogleKeyPool();
    for (let step=1; step<=2; step++) {
        const next=(pool.idx+step)%3;
        if (!pool.keys[next]) continue;
        try {
            localStorage.setItem('geovision_google_active_key_index', String(next));
            localStorage.setItem('geovision_google_maps_api_key', pool.keys[next]);
            localStorage.setItem('geovision_google_last_switch_reason', clean(e?.message || String(e || '')).slice(0,500));
        } catch { }
        toast('Chiave Google ' + (pool.idx+1) + ' esaurita · passo alla ' + (next+1));
        setTimeout(() => location.reload(), 500);
        return true;
    }
    toast('Nessun altra chiave Google disponibile');
    return false;
}
gvDiagLoadGoogleKeyPool();

function setGoogleKeyState(state)"""
if anchor not in s:
    raise SystemExit('startup anchor missing')
s=s.replace(anchor,insert,1)

old="""        catch (e) {
            bad++;
            add('Ricerca Places', 'bad', clean(e?.message || 'Ricerca fallita'));
        }
    }
    if (found?.id && lib) {"""
new="""        catch (e) {
            bad++;
            add('Ricerca Places', 'bad', clean(e?.message || 'Ricerca fallita'));
            gvDiagAdvanceGoogleKey(e);
        }
    }
    if (found?.id && lib) {"""
if old not in s:
    raise SystemExit('diagnostic search catch anchor missing')
s=s.replace(old,new,1)

old2="""    add('Chiave API', googleKey ? 'ok' : 'bad', googleKey ? 'Chiave presente' : 'Chiave non configurata');"""
new2="""    const gvPool = gvDiagLoadGoogleKeyPool();
    add('Chiave API', googleKey ? 'ok' : 'bad', googleKey ? ('Chiave presente · Google ' + (gvPool.idx + 1) + ' / 3 attiva') : 'Chiave non configurata');"""
if old2 not in s:
    raise SystemExit('diagnostic key row anchor missing')
s=s.replace(old2,new2,1)

assert 'gvDiagAdvanceGoogleKey' in s
assert 'gvDiagIsKeyFailure' in s
assert 'RESOURCE_EXHAUSTED' in s
assert 'gvInstallGoogleKeyFailoverHooks' not in s
assert 'gm_authFailure' not in s

p.write_text(s,encoding='utf-8')
print('diagnostic-only failover patched',p.stat().st_size)
