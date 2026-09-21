from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
H1=ROOT/'android-youtube-test/app/src/main/assets/geovision.html'
H2=ROOT/'out/LAB_012_FAILOVER.html'


def patch_html(path):
    s=path.read_text(encoding='utf-8')

    # Start from the proven LAB037 behavior and change ONLY YouTube opening:
    # use Android intent:// with the explicit YouTube package and no browser fallback.
    old="""function launchPlatform(p) {\n  if(p === 'youtube') gv029ShowReturnBubble();\n  gv029ShowReturnBubble(); if (p === 'images')"""
    new="""function launchPlatform(p) {\n  if(p === 'youtube') {\n    gv029ShowReturnBubble();\n    const yq = query(); if (!yq) return toast('Niente da cercare');\n    return openIntent(`intent://www.youtube.com/results?search_query=${encodeURIComponent(yq)}#Intent;scheme=https;package=com.google.android.youtube;end`);\n  }\n  gv029ShowReturnBubble(); if (p === 'images')"""

    assert s.count(old)==1, 'LAB037 launchPlatform anchor not found exactly once'
    s=s.replace(old,new,1)

    # The proven Android host already knows how to handle intent:// deep links.
    assert 'function openIntent(u) { window.location.href = u; }' in s
    assert 'package=com.google.android.youtube;end' in s
    youtube=s[s.index("if(p === 'youtube') {"):s.index("if(p === 'youtube') {")+650]
    assert 'browser_fallback_url' not in youtube

    path.write_text(s,encoding='utf-8')


patch_html(H1)
if H2.exists():
    patch_html(H2)
print('LAB041: YouTube opens directly in com.google.android.youtube from proven LAB037 base')
