from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PATHS=[ROOT/'android-youtube-test/app/src/main/assets/geovision.html',ROOT/'out/LAB_012_FAILOVER.html']

DRAWER_OLD='<button class="platform" data-p="youtube"><strong>▶</strong>YouTube</button>'
DRAWER_NEW=DRAWER_OLD+'<button class="platform" data-p="shorts"><strong>▸</strong>Shorts</button>'
PICKER_OLD='<button data-vp="youtube">▶ YouTube</button>'
PICKER_NEW=PICKER_OLD+'<button data-vp="shorts">▸ Shorts</button>'

CSS_ANCHOR='.video-picker button[data-vp="youtube"]::after{content:\'YouTube\'}'
CSS_SHORTS='''.video-picker button[data-vp="shorts"]::before{background-color:#fff5f5;background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'%3E%3Cpath d='M9 3.5c1.1-.7 2.5-.5 3.4.4l2 2c.8.8 2 .9 3 .3l.4-.2c1.3-.8 3 .1 3 1.7 0 .8-.4 1.5-1.1 1.9l-2 1.2c-.8.5-.8 1.7 0 2.2l2 1.2c.7.4 1.1 1.1 1.1 1.9 0 1.6-1.7 2.5-3 1.7l-.4-.2c-1-.6-2.2-.5-3 .3l-2 2c-.9.9-2.3 1.1-3.4.4l-4.7-2.9C3.5 17 3 16.1 3 15.1V8.9c0-1 .5-1.9 1.3-2.4L9 3.5z' fill='%23ff0033'/%3E%3Cpath d='m10 9 5 3-5 3z' fill='white'/%3E%3C/svg%3E")}.video-picker button[data-vp="shorts"]::after{content:'Shorts'}'''

LAUNCH_ANCHOR="""function launchPlatform(p) {
  if(p === 'youtube') {"""
LAUNCH_NEW="""function launchPlatform(p) {
  if(p === 'shorts') {
    gv029ShowReturnBubble();
    const sq = platformQuery043(); if (!sq) return toast('Niente da cercare');
    return openIntent(`intent://www.youtube.com/results?search_query=${encodeURIComponent(sq)}&sp=EgIQCQ%253D%253D#Intent;scheme=https;package=com.google.android.youtube;end`);
  }
  if(p === 'youtube') {"""

def patch(path):
    s=path.read_text(encoding='utf-8')
    assert s.count(DRAWER_OLD)==1, 'drawer YouTube anchor missing/duplicated'
    assert s.count(PICKER_OLD)==1, 'picker YouTube anchor missing/duplicated'
    assert s.count(CSS_ANCHOR)==1, 'YouTube picker CSS anchor missing/duplicated'
    assert s.count(LAUNCH_ANCHOR)==1, 'launchPlatform YouTube anchor missing/duplicated'
    assert 'data-p="shorts"' not in s and 'data-vp="shorts"' not in s
    s=s.replace(DRAWER_OLD,DRAWER_NEW,1)
    s=s.replace(PICKER_OLD,PICKER_NEW,1)
    s=s.replace(CSS_ANCHOR,CSS_ANCHOR+'\n'+CSS_SHORTS,1)
    s=s.replace(LAUNCH_ANCHOR,LAUNCH_NEW,1)
    assert s.count('data-p="shorts"')==1
    assert s.count('<button data-vp="shorts">')==1
    assert s.count("if(p === 'shorts')")==1
    assert 'sp=EgIQCQ%253D%253D' in s
    assert 'package=com.google.android.youtube;end' in s
    path.write_text(s,encoding='utf-8')

for p in PATHS:
    if p.exists(): patch(p)
print('LAB044: Shorts added to menus and routed directly to YouTube Shorts-filtered search')
