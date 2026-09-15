from pathlib import Path
import re
ROOT=Path(__file__).resolve().parents[1]
HTML=ROOT/'android-youtube-test/app/src/main/assets/geovision.html'
OUT=ROOT/'out/LAB_012_FAILOVER.html'

def patch(path):
    s=path.read_text(encoding='utf-8')
    # Keep LAB024 button/graphics. Change only its click destination: Google results already filtered to photos for current place.
    old="gv024PhotoButton.onclick=e=>{e.preventDefault();e.stopPropagation();openPhotoGallery();};"
    new="""gv024PhotoButton.onclick=e=>{e.preventDefault();e.stopPropagation();
    const p=(typeof current!=='undefined'&&current)?current:null;
    const q=[p?.name||'',p?.address||p?.vicinity||''].filter(Boolean).join(' ').trim();
    if(!q)return;
    const u='https://www.google.com/search?q='+encodeURIComponent('foto di '+q)+'&tbm=isch';
    try{ if(window.GeoVisionSocial&&typeof window.GeoVisionSocial.open==='function') window.GeoVisionSocial.open(u); else location.href=u; }
    catch(_){ location.href=u; }
  };"""
    assert old in s, 'LAB024 photo click anchor missing'
    s=s.replace(old,new,1)

    # Regression guard for the official Google card: do not replace/rebuild it. Ensure its render path is called and its host stays visible.
    assert 'async function renderOfficialGoogleCard(p)' in s, 'official Google card renderer missing'
    assert 'id="googleCardHost"' in s, 'Google card host missing'
    assert 'const cardPromise=renderOfficialGoogleCard(p);' in s, 'openPlace no longer calls Google card renderer'
    css='''\n<style id="gv025-google-card-guard">\n#googleCardHost{display:block!important;visibility:visible!important;opacity:1!important;min-height:1px}\n</style>\n'''
    s=s.replace('</head>',css+'</head>',1)
    path.write_text(s,encoding='utf-8')

patch(HTML)
if OUT.exists(): patch(OUT)
print('LAB025: Google card render path guarded + photo button opens Google image results')
