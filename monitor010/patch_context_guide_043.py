from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]
PATHS=[ROOT/'android-youtube-test/app/src/main/assets/geovision.html',ROOT/'out/LAB_012_FAILOVER.html']

def patch(path):
    s=path.read_text(encoding='utf-8')
    assert s.count('function launchPlatform(p) {')==1

    # Keep the proven LAB042 native/social launch code untouched.
    # Only normalize the text returned by query() at launch time.
    helper=r'''
function gv043CleanPart(v){ return String(v||'').replace(/\s+/g,' ').trim(); }
function gv043SearchPair(){
  try{
    const manual=gv043CleanPart(document.querySelector('#manualPhrase')?.value||'');
    if(manual) return manual;
  }catch(_){}
  const raw=gv043CleanPart(query());
  if(!raw) return raw;
  const parts=raw.split(/\s*[,·|]+\s*/).map(gv043CleanPart).filter(Boolean);
  if(parts.length<=2) return parts.join(' ');
  // GeoVision order is locality -> comune/citta -> provincia -> regione.
  // For frazione/rione keep locality+comune. For comune/citta skip province and use region.
  const first=(parts[0]||'').toLowerCase();
  const localHint=/\b(frazione|rione|quartiere|contrada|localita|borgata)\b/.test(first);
  if(localHint) return [parts[0],parts[1]].filter(Boolean).join(' ');
  return [parts[0],parts[parts.length-1]].filter(Boolean).join(' ');
}
'''
    anchor='function launchPlatform(p)'
    assert 'function gv043SearchPair()' not in s
    s=s.replace(anchor,helper+'\n'+anchor,1)

    # Scope query override only while launchPlatform builds the platform URL.
    s=s.replace('function launchPlatform(p) {','function launchPlatform(p) {\n  const gv043BaseQuery=query; const query=()=>gv043SearchPair();',1)

    # Audioguide: speak the already-existing local intro immediately while AI loads.
    old="""async function enrichNarration(p) { const run = ++narrationRun; const guide = $('#audioGuide'); if (!guide)
    return; guide.innerHTML = '<div class="audio-title">Audioguida AI</div><div id="guideScroll" class="guide-scroll"><div id="guideTranscript"><div class="loading">Preparo l’audioguida…</div></div><div id="guideSource" class="source"></div></div><button id="deepenGuide" class="deepen-guide" type="button" disabled>Voglio saperne di più</button>'; const transcript = $('#guideTranscript'), source = $('#guideSource'), button = $('#deepenGuide'); let told = '', depth = 0; let continuation = await aiNarration(p, 'guide', '', '');"""
    new="""async function enrichNarration(p) { const run = ++narrationRun; const guide = $('#audioGuide'); if (!guide)
    return; const gv043Intro=instantNarrationIntro(p); guide.innerHTML = '<div class="audio-title">Audioguida AI</div><div id="guideScroll" class="guide-scroll"><div id="guideTranscript"><div class="narration narration-stage">'+esc(gv043Intro)+'</div></div><div id="guideSource" class="source"></div></div><button id="deepenGuide" class="deepen-guide" type="button" disabled>Voglio saperne di più</button>'; const transcript = $('#guideTranscript'), source = $('#guideSource'), button = $('#deepenGuide'); let told = gv043Intro, depth = 0; if(gv043Intro) speak(gv043Intro); let continuation = await aiNarration(p, 'guide', '', told);"""
    assert s.count(old)==1,'audioguide anchor missing/duplicated'
    s=s.replace(old,new,1)

    assert s.count('function launchPlatform(p) {')==1
    assert s.count('function gv043SearchPair()')==1
    assert 'package=com.google.android.youtube;end' in s
    assert 'gvFacebookLegacySearch' in s
    assert 'instagram' in s.lower()
    assert 'tiktok' in s.lower()
    assert 'if(gv043Intro) speak(gv043Intro)' in s
    path.write_text(s,encoding='utf-8')

for p in PATHS:
    if p.exists(): patch(p)
print('LAB043 fixed: 2-level platform context + immediate audioguide intro; LAB042 social launch preserved')
