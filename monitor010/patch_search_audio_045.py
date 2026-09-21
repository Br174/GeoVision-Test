from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PATHS=[ROOT/'android-youtube-test/app/src/main/assets/geovision.html',ROOT/'out/LAB_012_FAILOVER.html']

OLD_QUERY="""function platformQuery043(){
  const manual=clean(document.getElementById('manual').value);
  if(macroPrimary) return [manual,macroPrimary].filter(Boolean).join(' ');
  const poi=clean(document.getElementById('poi').value);
  let geo='';
  if(typeof current!=='undefined' && current){
    geo=current.isPoi ? clean(current.parent||'') : gv043GeoPair(current);
  }
  if(!geo) geo=clean(document.getElementById('place').value);
  return [manual,poi,geo].filter(Boolean).join(' ');
}
"""

NEW_QUERY="""function gv045ParentPair(v){
  const parts=gv043Split(v).filter(x=>!gv043Noise(x));
  if(parts.length<=2) return parts.join(' ');
  return [parts[0],parts[parts.length-1]].filter(Boolean).join(' ');
}
function platformQuery045(){
  if(typeof current!=='undefined' && current){
    if(current.isPoi){
      const parent=gv045ParentPair(current.parent||'');
      if(parent) return parent;
    }
    const geo=gv043GeoPair(current);
    if(geo) return geo;
  }
  const place=clean(document.getElementById('place').value);
  if(place){
    const pair=gv045ParentPair(place);
    if(pair) return pair;
  }
  return '';
}
"""

OLD_OPEN="""  const guidePromise = gv043PreloadGuide(p);
  const lead = gv043GuideLead(p);
  if(lead){
    try{
      if(typeof speak==='function') speak(lead,false);
      else if(window.GeoVisionTTS && typeof window.GeoVisionTTS.speak==='function') window.GeoVisionTTS.speak(lead,false);
    }catch(_){}
  }
  const cardPromise = renderOfficialGoogleCard(p);
"""
NEW_OPEN="""  const guidePromise = gv043PreloadGuide(p);
  const cardPromise = renderOfficialGoogleCard(p);
"""

def patch(path):
    s=path.read_text(encoding='utf-8')
    assert s.count(OLD_QUERY)==1, 'platformQuery043 anchor missing/duplicated'
    assert s.count(OLD_OPEN)==1, 'preselected guide lead anchor missing/duplicated'
    s=s.replace(OLD_QUERY,OLD_QUERY+'\n'+NEW_QUERY,1)
    s=s.replace(OLD_OPEN,NEW_OPEN,1)
    s=s.replace("const sq = platformQuery043();", "const sq = platformQuery045();",1)
    s=s.replace("const yq = platformQuery043();", "const yq = platformQuery045();",1)
    old_fb="if (p === 'facebook') return gvFacebookLegacySearch(social);"
    new_fb="if (p === 'facebook') { const fq=platformQuery045(); if(!fq) return toast('Niente da cercare'); return gvFacebookLegacySearch(fq); }"
    assert s.count(old_fb)==1, 'Facebook search anchor missing/duplicated'
    s=s.replace(old_fb,new_fb,1)
    assert s.count('function platformQuery045()')==1
    assert 'const sq = platformQuery045();' in s
    assert 'const yq = platformQuery045();' in s
    assert 'gvFacebookLegacySearch(fq)' in s
    assert 'const lead = gv043GuideLead(p);' not in s
    assert "void enrichNarration(p, guidePromise);" in s
    path.write_text(s,encoding='utf-8')

for p in PATHS:
    if p.exists(): patch(p)
print('LAB045: original AI audioguide only + place-only YouTube/Shorts/Facebook search')
