from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
HTML=ROOT/'android-youtube-test/app/src/main/assets/geovision.html'
OUT=ROOT/'out/LAB_012_FAILOVER.html'

def patch(path):
    s=path.read_text(encoding='utf-8')
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
    # Keep the existing official Google-card implementation untouched; only prevent its host from being hidden by a regression.
    assert 'async function renderOfficialGoogleCard(p)' in s, 'official Google card renderer missing'
    assert 'id="googleCardHost"' in s, 'Google card host missing'
    css='''\n<style id="gv025-google-card-guard">\n#googleCardHost{display:block!important;visibility:visible!important;opacity:1!important;min-height:1px}\n</style>\n'''
    s=s.replace('</head>',css+'</head>',1)
    path.write_text(s,encoding='utf-8')

patch(HTML)
if OUT.exists(): patch(OUT)
print('LAB025: Google card host guarded + photo button opens Google image results')
