from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
HTML=ROOT/'android-youtube-test/app/src/main/assets/geovision.html'
OUT=ROOT/'out/LAB_012_FAILOVER.html'

def patch(path):
    s=path.read_text(encoding='utf-8')
    assert 'async function renderOfficialGoogleCard' in s, 'official card renderer missing'
    assert 'googleCardHost' in s, 'official card host missing'
    assert 'const gv024PhotoButton' in s, 'LAB024 photo button missing'

    old="gv024PhotoButton.onclick=e=>{e.preventDefault();e.stopPropagation();openPhotoGallery();};"
    new="""gv024PhotoButton.onclick=e=>{
    e.preventDefault();e.stopPropagation();
    const p=(typeof current!=='undefined'&&current)?current:null;
    const q=String((p&&(p.name||p.title||p.address))||'').trim();
    if(!q){ if(typeof openPhotoGallery==='function') openPhotoGallery(); return; }
    const url='https://www.google.com/search?tbm=isch&q='+encodeURIComponent(q+' foto');
    try{
      if(window.GeoVisionSocial&&typeof window.GeoVisionSocial.open==='function') window.GeoVisionSocial.open(url);
      else window.open(url,'_blank');
    }catch(_){ window.location.href=url; }
  };"""
    assert old in s, 'LAB024 photo handler anchor missing'
    s=s.replace(old,new,1)

    # Regression guards: this patch must not rewrite/remove the existing Google card machinery.
    assert 'renderOfficialGoogleCard(p)' in s
    assert "$('#sheet').classList.add('show')" in s
    path.write_text(s,encoding='utf-8')

patch(HTML)
if OUT.exists(): patch(OUT)
print('LAB025: official Google card preserved; photo button opens Google image results for current place')
