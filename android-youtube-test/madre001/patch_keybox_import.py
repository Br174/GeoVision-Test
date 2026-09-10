from pathlib import Path

p = Path('/tmp/GeoVision_MADRE_001_SOURCE.html')
s = p.read_text(encoding='utf-8')

needle = """        catch { }
        location.reload(); };
    panel.onclick = e => { if (e.target === panel)
        panel.remove(); };"""

insert = """        catch { }
        location.reload(); };

    const keyBoxButton = document.createElement('button');
    keyBoxButton.id = 'googleDiagImportKeyBox';
    keyBoxButton.type = 'button';
    keyBoxButton.textContent = 'Importa tutte da KeyBox';
    keyBoxButton.style.cssText = 'width:100%;margin-top:10px;border:1px solid #bfdbfe;border-radius:12px;padding:12px;background:#eff6ff;color:#1d4ed8;font-weight:800';
    const keyBoxState = document.createElement('div');
    keyBoxState.id = 'googleDiagImportState';
    keyBoxState.style.cssText = 'margin-top:7px;color:#64748b;font-size:12px';
    keyBoxState.textContent = 'Importa 3 Google Maps + 1 AI + 1 YouTube con un solo tocco.';
    if (diagSaveButton?.parentElement) {
        diagSaveButton.parentElement.appendChild(keyBoxButton);
        diagSaveButton.parentElement.appendChild(keyBoxState);
    }

    window.gvKeyBoxError = function(message) {
        const st = document.getElementById('googleDiagImportState');
        const bt = document.getElementById('googleDiagImportKeyBox');
        if (st) { st.textContent = message || 'KeyBox non disponibile'; st.style.color = '#dc2626'; }
        if (bt) { bt.disabled = false; bt.textContent = 'Importa tutte da KeyBox'; }
    };

    window.gvReceiveKeyBox = function(keys) {
        const st = document.getElementById('googleDiagImportState');
        const bt = document.getElementById('googleDiagImportKeyBox');
        try {
            const g1 = String(keys?.google1 || '').trim();
            const g2 = String(keys?.google2 || '').trim();
            const g3 = String(keys?.google3 || '').trim();
            const ai = String(keys?.ai || '').trim();
            const yt = String(keys?.youtube || '').trim();
            const maps = [g1, g2, g3];
            const primary = maps.find(Boolean) || '';
            if (primary) localStorage.setItem('geovision_google_maps_api_key', primary);
            maps.forEach((v, i) => {
                const name = 'geovision_google_maps_api_key_' + (i + 1);
                if (v) localStorage.setItem(name, v); else localStorage.removeItem(name);
            });
            localStorage.setItem('geovision_google_maps_api_keys', JSON.stringify(maps.filter(Boolean)));
            if (ai) localStorage.setItem('geovision_ai_api_key', ai); else localStorage.removeItem('geovision_ai_api_key');
            if (yt) localStorage.setItem('geovision_youtube_api_key', yt); else localStorage.removeItem('geovision_youtube_api_key');
            const count = maps.filter(Boolean).length + (ai ? 1 : 0) + (yt ? 1 : 0);
            if (st) { st.textContent = 'Importate ' + count + ' / 5 chiavi. Riavvio GeoVision…'; st.style.color = count === 5 ? '#16a34a' : '#d97706'; }
            if (bt) { bt.disabled = true; bt.textContent = 'Chiavi importate'; }
            setTimeout(() => location.reload(), 550);
        } catch (e) {
            window.gvKeyBoxError('Errore durante l’importazione delle chiavi');
        }
    };

    keyBoxButton.onclick = () => {
        const bridge = window.GeoVisionKeyBox;
        if (!bridge || typeof bridge.importKeys !== 'function') {
            return window.gvKeyBoxError('Installa o aggiorna GeoVision KeyBox');
        }
        keyBoxButton.disabled = true;
        keyBoxButton.textContent = 'Importo…';
        keyBoxState.textContent = 'Leggo le chiavi dal KeyBox…';
        keyBoxState.style.color = '#64748b';
        bridge.importKeys();
    };

    panel.onclick = e => { if (e.target === panel)
        panel.remove(); };"""

if needle not in s:
    raise SystemExit('key-panel handler anchor not found')

s = s.replace(needle, insert, 1)

assert 'googleDiagImportKeyBox' in s
assert 'GeoVisionKeyBox' in s
assert 'geovision_google_maps_api_key_' in s
assert 'geovision_google_maps_api_keys' in s
assert 'geovision_ai_api_key' in s
assert 'geovision_youtube_api_key' in s

p.write_text(s, encoding='utf-8')
print('keybox-import html patched', p.stat().st_size)
