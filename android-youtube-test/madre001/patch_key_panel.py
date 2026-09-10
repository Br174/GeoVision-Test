from pathlib import Path
p=Path('/tmp/GeoVision_MADRE_001_SOURCE.html')
s=p.read_text(encoding='utf-8')
old="""panel.innerHTML = '<div style=\"width:min(430px,94vw);max-height:84vh;overflow:auto;background:#fff;border-radius:22px;box-shadow:0 20px 60px rgba(0,0,0,.3);padding:20px;font:14px/1.45 system-ui;color:#0f172a\"><div style=\"display:flex;align-items:center;justify-content:space-between;gap:12px\"><div><b style=\"font-size:20px\">Diagnostica Google</b><div style=\"color:#64748b;margin-top:2px\">Maps · Places · Schede · Foto</div></div><button id=\"googleDiagClose\" type=\"button\" style=\"border:0;border-radius:50%;width:42px;height:42px;background:#0f172a;color:#fff;font-size:24px\">×</button></div><div id=\"googleDiagRows\" style=\"display:grid;gap:10px;margin-top:18px\"></div></div>';"""
new="""panel.innerHTML = '<div style=\"width:min(430px,94vw);max-height:84vh;overflow:auto;background:#fff;border-radius:22px;box-shadow:0 20px 60px rgba(0,0,0,.3);padding:20px;font:14px/1.45 system-ui;color:#0f172a\"><div style=\"display:flex;align-items:center;justify-content:space-between;gap:12px\"><div><b style=\"font-size:20px\">Diagnostica Google</b><div style=\"color:#64748b;margin-top:2px\">Maps · Places · Schede · Foto</div></div><button id=\"googleDiagClose\" type=\"button\" style=\"border:0;border-radius:50%;width:42px;height:42px;background:#0f172a;color:#fff;font-size:24px\">×</button></div><div style=\"margin-top:18px;padding:14px;border:1px solid #e2e8f0;border-radius:16px;background:#f8fafc\"><label for=\"googleDiagKey\" style=\"display:block;font-weight:800;margin-bottom:8px\">Chiave API Google</label><input id=\"googleDiagKey\" type=\"password\" autocomplete=\"off\" placeholder=\"Incolla qui la chiave Google Maps\" style=\"width:100%;border:1px solid #cbd5e1;border-radius:12px;padding:12px;background:#fff;color:#0f172a;outline:none\"><button id=\"googleDiagSave\" type=\"button\" style=\"width:100%;margin-top:10px;border:0;border-radius:12px;padding:12px;background:#2f7de1;color:#fff;font-weight:800\">Salva e attiva</button><div style=\"margin-top:7px;color:#64748b;font-size:12px\">La chiave viene salvata solo in questa app isolata.</div></div><div id=\"googleDiagRows\" style=\"display:grid;gap:10px;margin-top:18px\"></div></div>';"""
if old not in s:
    raise SystemExit('target panel HTML not found')
s=s.replace(old,new,1)
old2="""document.getElementById('googleDiagClose').onclick = () => panel.remove();
    panel.onclick = e => { if (e.target === panel)
        panel.remove(); };"""
new2="""document.getElementById('googleDiagClose').onclick = () => panel.remove();
    const diagKeyInput = document.getElementById('googleDiagKey');
    const diagSaveButton = document.getElementById('googleDiagSave');
    if (diagKeyInput)
        diagKeyInput.value = googleKey || '';
    if (diagSaveButton)
        diagSaveButton.onclick = () => { const v = (diagKeyInput?.value || '').trim(); try {
            if (v)
                localStorage.setItem('geovision_google_maps_api_key', v);
            else
                localStorage.removeItem('geovision_google_maps_api_key');
        }
        catch { }
        location.reload(); };
    panel.onclick = e => { if (e.target === panel)
        panel.remove(); };"""
if old2 not in s:
    raise SystemExit('target handlers not found')
s=s.replace(old2,new2,1)
p.write_text(s,encoding='utf-8')
print('patched',p.stat().st_size)
