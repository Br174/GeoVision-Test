from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
H1=ROOT/'android-youtube-test/app/src/main/assets/geovision.html'
H2=ROOT/'out/LAB_012_FAILOVER.html'

OLD="""function launchPlatform(p) {
  if(p === 'youtube') gv029ShowReturnBubble();
  gv029ShowReturnBubble(); if (p === 'images')"""
NEW="""function launchPlatform(p) {
  if(p === 'youtube') {
    gv029ShowReturnBubble();
    const yq = query(); if (!yq) return toast('Niente da cercare');
    return openIntent(`intent://www.youtube.com/results?search_query=${encodeURIComponent(yq)}#Intent;scheme=https;package=com.google.android.youtube;end`);
  }
  gv029ShowReturnBubble(); if (p === 'images')"""

def patch(path):
    s=path.read_text(encoding='utf-8')
    assert s.count(OLD)==1, 'LAB037 YouTube launch anchor not found or duplicated'
    s=s.replace(OLD,NEW,1)
    assert 'function openIntent(u) { window.location.href = u; }' in s
    assert 'package=com.google.android.youtube;end' in s
    block=s[s.index("if(p === 'youtube') {"):s.index("gv029ShowReturnBubble(); if (p === 'images')")]
    assert 'browser_fallback_url' not in block
    path.write_text(s,encoding='utf-8')

patch(H1)
if H2.exists():
    patch(H2)
print('LAB042: YouTube search routed directly to installed YouTube app via intent://')
