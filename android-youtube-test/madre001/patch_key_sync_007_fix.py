from pathlib import Path

html = Path('android-youtube-test/app/src/main/assets/geovision.html')
s = html.read_text(encoding='utf-8')

# Patch only the failover write point. No automatic sync pull, no page reload loop,
# no override of gvReceiveKeyBox: this keeps panels/cards behavior untouched.
needle = "localStorage.setItem('geovision_google_active_key_index', String(next));"
if needle not in s:
    raise SystemExit('failover active-index anchor missing')
if 'gvReportGlobalKey007' not in s:
    s = s.replace(needle, needle + "\n            try { window.gvReportGlobalKey007 && window.gvReportGlobalKey007(next); } catch { }", 1)

marker = '</body>'
if marker not in s:
    raise SystemExit('body marker missing')

script = r'''
<script id="gv-key-sync-007-fix">
(() => {
  window.gvReportGlobalKey007 = function(idx) {
    try {
      const bridge = window.GeoVisionKeyBox;
      if (!bridge || typeof bridge.setActiveIndex !== 'function') return;
      const n = Number.parseInt(idx, 10);
      if (!Number.isInteger(n) || n < 0 || n > 2) return;
      bridge.setActiveIndex(n);
    } catch {}
  };

  window.gvApplyKeyBoxState007 = function(keys) {
    try {
      const maps = [1,2,3].map(i => String(keys?.['google'+i] || '').trim());
      const ai = String(keys?.ai || '').trim();
      const yt = String(keys?.youtube || '').trim();
      let idx = Number.parseInt(keys?.activeIndex, 10);
      if (!Number.isInteger(idx) || idx < 0 || idx > 2 || !maps[idx]) {
        const first = maps.findIndex(Boolean);
        idx = first >= 0 ? first : 0;
      }
      maps.forEach((v, i) => {
        const k = 'geovision_google_maps_api_key_' + (i + 1);
        if (v) localStorage.setItem(k, v); else localStorage.removeItem(k);
      });
      localStorage.setItem('geovision_google_maps_api_keys', JSON.stringify(maps.filter(Boolean)));
      if (ai) localStorage.setItem('geovision_ai_api_key', ai);
      if (yt) localStorage.setItem('geovision_youtube_api_key', yt);
      localStorage.setItem('geovision_google_active_key_index', String(idx));
      localStorage.setItem('geovision_keybox_active_generation', String(keys?.activeGeneration ?? 0));
      localStorage.setItem('geovision_keybox_switch_total_today', String(keys?.switchTotalToday ?? 0));
      if (maps[idx]) localStorage.setItem('geovision_google_maps_api_key', maps[idx]);
    } catch (e) {
      console.warn('KEY SYNC 007 apply failed', e);
    }
  };
})();
</script>
'''
s = s.replace(marker, script + '\n' + marker, 1)

html.write_text(s, encoding='utf-8')
print('KEY SYNC 007 FIX patched', html.stat().st_size)
