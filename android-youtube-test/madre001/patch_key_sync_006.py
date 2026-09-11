from pathlib import Path

html = Path('android-youtube-test/app/src/main/assets/geovision.html')
s = html.read_text(encoding='utf-8')

marker = '</body>'
if marker not in s:
    raise SystemExit('body marker missing')

script = r'''
<script id="gv-key-sync-006">
(() => {
  let gvKeySyncBusy006 = false;
  let gvKeySyncLastPull006 = 0;

  function gvNormKeys006(keys) {
    return [1,2,3].map(i => String(keys?.['google'+i] || '').trim());
  }

  function gvApplyGlobalKey006(keys) {
    try {
      const maps = gvNormKeys006(keys);
      const ai = String(keys?.ai || '').trim();
      const yt = String(keys?.youtube || '').trim();
      let idx = Number.parseInt(keys?.activeIndex, 10);
      if (!Number.isInteger(idx) || idx < 0 || idx > 2) idx = 0;
      if (!maps[idx]) {
        const first = maps.findIndex(Boolean);
        if (first >= 0) idx = first;
      }

      const oldIdx = Number.parseInt(localStorage.getItem('geovision_google_active_key_index') || '0', 10);
      const oldKey = String(localStorage.getItem('geovision_google_maps_api_key') || '').trim();
      const selected = maps[idx] || '';

      maps.forEach((v, i) => {
        const name = 'geovision_google_maps_api_key_' + (i + 1);
        if (v) localStorage.setItem(name, v); else localStorage.removeItem(name);
      });
      localStorage.setItem('geovision_google_maps_api_keys', JSON.stringify(maps.filter(Boolean)));
      if (ai) localStorage.setItem('geovision_ai_api_key', ai);
      if (yt) localStorage.setItem('geovision_youtube_api_key', yt);
      localStorage.setItem('geovision_google_active_key_index', String(idx));
      localStorage.setItem('geovision_keybox_active_generation', String(keys?.activeGeneration ?? 0));
      localStorage.setItem('geovision_keybox_switch_total_today', String(keys?.switchTotalToday ?? 0));
      if (selected) localStorage.setItem('geovision_google_maps_api_key', selected);

      const mustReload = !!selected && !!oldKey && (oldIdx !== idx || oldKey !== selected);
      if (mustReload) setTimeout(() => location.reload(), 250);
    } catch (e) {
      console.warn('KEY SYNC 006 apply failed', e);
    } finally {
      gvKeySyncBusy006 = false;
    }
  }

  const oldReceive = window.gvReceiveKeyBox;
  window.gvReceiveKeyBox = function(keys) {
    try { gvApplyGlobalKey006(keys); } catch {}
    if (typeof oldReceive === 'function') {
      try { oldReceive(keys); } catch {}
    }
  };
  window.gvReceiveKeyBoxSync = gvApplyGlobalKey006;

  window.gvPullGlobalKey006 = function(force=false) {
    const now = Date.now();
    if (!force && (gvKeySyncBusy006 || now - gvKeySyncLastPull006 < 2500)) return;
    const bridge = window.GeoVisionKeyBox;
    if (!bridge || typeof bridge.syncState !== 'function') return;
    gvKeySyncBusy006 = true;
    gvKeySyncLastPull006 = now;
    try { bridge.syncState(); } catch { gvKeySyncBusy006 = false; }
  };

  window.gvReportGlobalKey006 = function(idx) {
    const bridge = window.GeoVisionKeyBox;
    if (!bridge || typeof bridge.setActiveIndex !== 'function') return;
    const n = Number.parseInt(idx, 10);
    if (!Number.isInteger(n) || n < 0 || n > 2) return;
    try { bridge.setActiveIndex(n); } catch {}
  };

  document.addEventListener('visibilitychange', () => {
    if (!document.hidden) setTimeout(() => window.gvPullGlobalKey006(false), 350);
  });
  window.addEventListener('focus', () => setTimeout(() => window.gvPullGlobalKey006(false), 350));
  setTimeout(() => window.gvPullGlobalKey006(true), 900);
})();
</script>
'''
s = s.replace(marker, script + '\n' + marker, 1)

needle = "localStorage.setItem('geovision_google_active_key_index', String(next));"
if needle not in s:
    raise SystemExit('failover active-index anchor missing')
s = s.replace(needle, needle + "\n            try { window.gvReportGlobalKey006 && window.gvReportGlobalKey006(next); } catch { }", 1)

html.write_text(s, encoding='utf-8')
print('KEY SYNC 006 HTML patched', html.stat().st_size)
